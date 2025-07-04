#include "rclcpp/rclcpp.hpp"
#include "std_msgs/msg/string.hpp"
#include <cstddef>
#include <initializer_list> 
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <unistd.h>

#include <string>
#include <iostream>
#include <nlohmann/json.hpp>  // JSON 库（你需要集成）

using json = nlohmann::json;

class ServoMediatorNode : public rclcpp::Node {
public:
    ServoMediatorNode() : Node("servo_mediator") {
        RCLCPP_INFO(this->get_logger(), "ServoMediatorNode started.");

        sock_ = socket(AF_INET, SOCK_DGRAM, 0);
        target_addr_.sin_family = AF_INET;
        target_addr_.sin_port = htons(4210);
        inet_pton(AF_INET, "192.168.110.48", &target_addr_.sin_addr);

        subscription_ = this->create_subscription<std_msgs::msg::String>(
            "unity_angle_publisher", 10,
            std::bind(&ServoMediatorNode::topic_callback, this, std::placeholders::_1));
    }

private:
    void topic_callback(const std_msgs::msg::String::SharedPtr msg) {
        try {
            json data = json::parse(msg->data);
            std::string payload = data.dump();
            sendto(sock_, payload.c_str(), payload.size(), 0, (sockaddr*)&target_addr_, sizeof(target_addr_));
            RCLCPP_INFO(this->get_logger(), "Forwarded: %s", payload.c_str());
        } catch (const std::exception& e) {
            RCLCPP_ERROR(this->get_logger(), "JSON parse error: %s", e.what());
        }
    }

    rclcpp::Subscription<std_msgs::msg::String>::SharedPtr subscription_;
    int sock_;
    sockaddr_in target_addr_;
};

std::shared_ptr<ServoMediatorNode> create_servo_mediator() {
    return std::make_shared<ServoMediatorNode>();
}
