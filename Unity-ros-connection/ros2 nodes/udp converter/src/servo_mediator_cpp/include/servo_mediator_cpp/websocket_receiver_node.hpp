#pragma once

#include "rclcpp/rclcpp.hpp"
#include "std_msgs/msg/string.hpp"
#include "sensor_msgs/msg/image.hpp"
#include "cv_bridge/cv_bridge.h"
#include "nlohmann/json.hpp"
#include "base64.hpp"

#include <websocketpp/config/asio_no_tls.hpp>
#include <websocketpp/server.hpp>
#include <opencv2/opencv.hpp>

#include <unordered_map>
#include <string>
#include <thread>
#include <vector>

using json = nlohmann::json;
typedef websocketpp::server<websocketpp::config::asio> WebSocketServer;

class WebSocketReceiverNode : public rclcpp::Node {
public:
    WebSocketReceiverNode() : Node("websocket_receiver_node") {
        RCLCPP_INFO(this->get_logger(), "✅ WebSocketReceiverNode started.");

        image_publisher_ = this->create_publisher<sensor_msgs::msg::Image>("/image_raw", 10);

        server_thread_ = std::thread([this]() {
            server_.init_asio();

            server_.set_message_handler([this](websocketpp::connection_hdl, WebSocketServer::message_ptr msg) {
                this->handle_message(msg->get_payload());
            });

            server_.listen(8765);
            server_.start_accept();
            server_.run();
        });
        server_thread_.detach();
    }

private:
    WebSocketServer server_;
    std::thread server_thread_;

    // 用于发布非图像类消息（原样字符串）
    std::unordered_map<std::string, rclcpp::Publisher<std_msgs::msg::String>::SharedPtr> generic_publishers_;

    // 图像专用 publisher（只支持 /image_raw）
    rclcpp::Publisher<sensor_msgs::msg::Image>::SharedPtr image_publisher_;

    void handle_message(const std::string& message) {
        try {
            auto j = json::parse(message);
            std::string topic = j.at("topic");
            json data_json = j.at("data");

            if (topic == "/image_raw") {
                std::string img_b64 = data_json.at("img");

                std::string img_data = base64_decode(img_b64);
                std::vector<uchar> buffer(img_data.begin(), img_data.end());
                cv::Mat img = cv::imdecode(buffer, cv::IMREAD_COLOR);

                if (!img.empty()) {
                    auto msg = cv_bridge::CvImage(std_msgs::msg::Header(), "bgr8", img).toImageMsg();
                    msg->header.stamp = this->get_clock()->now();
                    image_publisher_->publish(*msg);
                    RCLCPP_INFO(this->get_logger(), "🖼️ Published image to /image_raw");
                } else {
                    RCLCPP_WARN(this->get_logger(), "⚠️ 图像解码失败！");
                }
            } else {
                // 非图像类消息：将 data_json 转为字符串发布
                if (generic_publishers_.find(topic) == generic_publishers_.end()) {
                    auto pub = this->create_publisher<std_msgs::msg::String>(topic, 10);
                    generic_publishers_[topic] = pub;
                    RCLCPP_INFO(this->get_logger(), "📌 Created generic publisher for topic: %s", topic.c_str());
                }

                std_msgs::msg::String ros_msg;
                ros_msg.data = data_json.dump();
                generic_publishers_[topic]->publish(ros_msg);
                RCLCPP_INFO(this->get_logger(), "📤 Published string to %s: %s", topic.c_str(), ros_msg.data.c_str());
            }

        } catch (const std::exception& e) {
            RCLCPP_ERROR(this->get_logger(), "❌ JSON/Base64 解析或消息处理失败: %s", e.what());
        }
    }
};
