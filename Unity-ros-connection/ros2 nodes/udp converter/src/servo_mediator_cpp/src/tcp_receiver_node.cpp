#include "servo_mediator_cpp/tcp_receiver_node.hpp"

#include <sys/socket.h>
#include <netinet/in.h>
#include <unistd.h>
#include <cstring>
#include <thread>
#include <nlohmann/json.hpp>

using json = nlohmann::json;

TcpReceiverNode::TcpReceiverNode() : Node("tcp_receiver_node") {
    server_fd_ = socket(AF_INET, SOCK_STREAM, 0);
    if (server_fd_ < 0) {
        RCLCPP_FATAL(this->get_logger(), "Failed to create socket");
        throw std::runtime_error("Socket creation failed");
    }

    sockaddr_in addr{};
    addr.sin_family = AF_INET;
    addr.sin_port = htons(4211);
    addr.sin_addr.s_addr = INADDR_ANY;

    int opt = 1;
    setsockopt(server_fd_, SOL_SOCKET, SO_REUSEADDR, &opt, sizeof(opt));

    if (bind(server_fd_, (struct sockaddr *)&addr, sizeof(addr)) < 0) {
        RCLCPP_FATAL(this->get_logger(), "Bind failed");
        throw std::runtime_error("Bind failed");
    }

    if (listen(server_fd_, 5) < 0) {
        RCLCPP_FATAL(this->get_logger(), "Listen failed");
        throw std::runtime_error("Listen failed");
    }

    RCLCPP_INFO(this->get_logger(), "TCP server listening on port 4211");

    timer_ = this->create_wall_timer(
        std::chrono::milliseconds(100),
        std::bind(&TcpReceiverNode::check_tcp, this));
}

TcpReceiverNode::~TcpReceiverNode() {
    close(server_fd_);
}

void TcpReceiverNode::check_tcp() {
    sockaddr_in client_addr{};
    socklen_t addr_len = sizeof(client_addr);
    int client_sock = accept(server_fd_, (struct sockaddr *)&client_addr, &addr_len);
    if (client_sock < 0) return;

    RCLCPP_INFO(this->get_logger(), "Client connected");

    std::thread([this, client_sock]() {
        this->handle_client_loop(client_sock);
        close(client_sock);
        RCLCPP_INFO(this->get_logger(), "Client disconnected");
    }).detach();
}

void TcpReceiverNode::handle_client_loop(int client_sock) {
    // 设置超时（秒级）
    struct timeval timeout;
    timeout.tv_sec = 5;
    timeout.tv_usec = 0;
    setsockopt(client_sock, SOL_SOCKET, SO_RCVTIMEO, &timeout, sizeof(timeout));

    while (rclcpp::ok()) {
        int ret = accept_and_read(client_sock);
        if (ret < 0) break;  // 超时或连接断开
    }
}

int TcpReceiverNode::accept_and_read(int client_sock) {
    uint32_t len = 0;
    ssize_t header = recv(client_sock, &len, sizeof(len), 0);
    if (header != sizeof(len)) return -1;
    len = ntohl(len);

    std::vector<char> buffer(len + 1, 0);
    size_t received = 0;
    while (received < len) {
        ssize_t ret = recv(client_sock, buffer.data() + received, len - received, 0);
        if (ret <= 0) return -1;
        received += ret;
    }

    try {
        json j = json::parse(buffer.begin(), buffer.begin() + len);
        std::string topic = j.at("topic");
        std::string data = j.at("data");

        auto pub = get_or_create_publisher(topic);
        std_msgs::msg::String msg;
        msg.data = data;
        pub->publish(msg);

        RCLCPP_INFO(this->get_logger(), "Published to [%s] (%ld bytes)", topic.c_str(), data.size());
    } catch (const std::exception &e) {
        RCLCPP_WARN(this->get_logger(), "JSON parse error: %s", e.what());
        return -1;
    }

    return 0;
}

rclcpp::Publisher<std_msgs::msg::String>::SharedPtr
TcpReceiverNode::get_or_create_publisher(const std::string &topic) {
    if (publisher_map_.find(topic) == publisher_map_.end()) {
        publisher_map_[topic] = this->create_publisher<std_msgs::msg::String>(topic, 10);
    }
    return publisher_map_[topic];
}
