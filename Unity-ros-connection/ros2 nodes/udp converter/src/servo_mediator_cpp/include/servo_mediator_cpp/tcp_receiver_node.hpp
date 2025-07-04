#ifndef TCP_RECEIVER_NODE_HPP
#define TCP_RECEIVER_NODE_HPP

#include <rclcpp/rclcpp.hpp>
#include <std_msgs/msg/string.hpp>
#include <unordered_map>
#include <string>
#include <memory>
#include <nlohmann/json.hpp>

class TcpReceiverNode : public rclcpp::Node {
public:
    TcpReceiverNode();
    ~TcpReceiverNode();

private:
    void check_tcp();
    int accept_and_read(int client_sock);

    rclcpp::TimerBase::SharedPtr timer_;
    int server_fd_;
    std::unordered_map<std::string, rclcpp::Publisher<std_msgs::msg::String>::SharedPtr> publisher_map_;

    rclcpp::Publisher<std_msgs::msg::String>::SharedPtr
    get_or_create_publisher(const std::string &topic);
};

#endif // TCP_RECEIVER_NODE_HPP
