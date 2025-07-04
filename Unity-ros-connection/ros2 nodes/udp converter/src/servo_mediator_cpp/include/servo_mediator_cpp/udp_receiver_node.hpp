#pragma once

#include "rclcpp/rclcpp.hpp"
#include "std_msgs/msg/string.hpp"
#include <unordered_map>
#include <nlohmann/json.hpp>

class UdpReceiverNode : public rclcpp::Node {
public:
    UdpReceiverNode();
    ~UdpReceiverNode();

private:
    void check_udp();
    rclcpp::Publisher<std_msgs::msg::String>::SharedPtr get_or_create_publisher(const std::string &topic);

    int sockfd_;
    rclcpp::TimerBase::SharedPtr timer_;
    std::unordered_map<std::string, rclcpp::Publisher<std_msgs::msg::String>::SharedPtr> publisher_map_;
};
