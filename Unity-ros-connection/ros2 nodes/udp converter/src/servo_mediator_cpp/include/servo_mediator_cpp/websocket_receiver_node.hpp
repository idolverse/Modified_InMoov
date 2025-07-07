#pragma once

#include "rclcpp/rclcpp.hpp"
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

        // 启动 websocket 服务线程
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

void handle_message(const std::string& message) {
    try {
        auto j = json::parse(message);
        std::string topic = j.at("topic");
        std::string payload = j.at("data");

        if (topic == "/image_raw") {
            auto data_json = json::parse(payload);
            std::string img_b64 = data_json["img"];

            std::string img_data = base64_decode(img_b64);
            std::vector<uchar> buffer(img_data.begin(), img_data.end());
            cv::Mat img = cv::imdecode(buffer, cv::IMREAD_COLOR);

            if (!img.empty()) {
                cv::imshow("WebSocket Image", img);
                cv::waitKey(1);
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
