#pragma once

#include "rclcpp/rclcpp.hpp"
#include "sensor_msgs/msg/image.hpp"
#include "cv_bridge/cv_bridge.h"
#include "nlohmann/json.hpp"
#include <opencv2/opencv.hpp>
#include <websocketpp/config/asio_no_tls.hpp>
#include <websocketpp/server.hpp>
#include <thread>
#include <vector>
#include <string>
#include "base64.hpp"

using json = nlohmann::json;
typedef websocketpp::server<websocketpp::config::asio> WebSocketServer;

class WebSocketReceiverNode : public rclcpp::Node {
public:
    WebSocketReceiverNode() : Node("websocket_receiver_node") {
        RCLCPP_INFO(this->get_logger(), "✅ WebSocketReceiverNode started.");

        publisher_ = this->create_publisher<sensor_msgs::msg::Image>("/image_raw", 10);

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
    rclcpp::Publisher<sensor_msgs::msg::Image>::SharedPtr publisher_;

    void handle_message(const std::string& message) {
        RCLCPP_INFO(this->get_logger(), "📨 Raw WebSocket msg: '%s'", message.c_str());

        try {
            auto j = json::parse(message);
            std::string topic = j.at("topic");

            if (topic == "/image_raw") {
                std::string img_b64 = j["data"]["img"];

                std::string img_data = base64_decode(img_b64);
                std::vector<uchar> buffer(img_data.begin(), img_data.end());
                cv::Mat img = cv::imdecode(buffer, cv::IMREAD_COLOR);

                if (!img.empty()) {
                    // ✅ 发布 ROS2 图像消息
                    auto msg = cv_bridge::CvImage(std_msgs::msg::Header(), "bgr8", img).toImageMsg();
                    msg->header.stamp = this->get_clock()->now();
                    publisher_->publish(*msg);

                    // ✅ 显示图像窗口
                    //cv::imshow("WebSocket Image", img);
                    //cv::waitKey(1);
                } else {
                    RCLCPP_WARN(this->get_logger(), "⚠️ 图像解码失败！");
                }
            } else {
                RCLCPP_INFO(this->get_logger(), "📨 Received non-image topic: %s", topic.c_str());
            }

        } catch (const std::exception& e) {
            RCLCPP_ERROR(this->get_logger(), "❌ JSON/Base64 解析错误: %s", e.what());
        }
    }
};
