#include "servo_mediator_cpp/udp_receiver_node.hpp"

#include <sys/socket.h>
#include <netinet/in.h>
#include <unistd.h>
#include <cstring>

using json = nlohmann::json;

UdpReceiverNode::UdpReceiverNode() : Node("udp_receiver_node") {
    sockfd_ = socket(AF_INET, SOCK_DGRAM, 0);
    sockaddr_in addr{};
    addr.sin_family = AF_INET;
    addr.sin_port = htons(4210);
    addr.sin_addr.s_addr = INADDR_ANY;
    bind(sockfd_, (struct sockaddr *)&addr, sizeof(addr));

    RCLCPP_INFO(this->get_logger(), "Listening on UDP port 4210");

    timer_ = this->create_wall_timer(
        std::chrono::milliseconds(50),
        std::bind(&UdpReceiverNode::check_udp, this));
}

UdpReceiverNode::~UdpReceiverNode() {
    close(sockfd_);
}

void UdpReceiverNode::check_udp() {
    
    char buffer[1024] = {0};
    sockaddr_in sender_addr{};
    socklen_t addr_len = sizeof(sender_addr);
    ssize_t len = recvfrom(sockfd_, buffer, sizeof(buffer) - 1, MSG_DONTWAIT,
                           (struct sockaddr *)&sender_addr, &addr_len);

    if (len > 0) {
        try {
            auto j = json::parse(buffer, buffer + len);
            std::string topic = j.at("topic");
            std::string data = j.at("data");

            auto pub = get_or_create_publisher(topic);
            std_msgs::msg::String msg;
            msg.data = data;
            pub->publish(msg);
            RCLCPP_INFO(this->get_logger(), "Published to [%s]: %s", topic.c_str(), data.c_str());
        } catch (const std::exception &e) {
            RCLCPP_WARN(this->get_logger(), "JSON parse or publish error: %s", e.what());
        }
    }
}

rclcpp::Publisher<std_msgs::msg::String>::SharedPtr
UdpReceiverNode::get_or_create_publisher(const std::string &topic) {
    if (publisher_map_.find(topic) == publisher_map_.end()) {
        publisher_map_[topic] = this->create_publisher<std_msgs::msg::String>(topic, 10);
    }
    return publisher_map_[topic];
}
