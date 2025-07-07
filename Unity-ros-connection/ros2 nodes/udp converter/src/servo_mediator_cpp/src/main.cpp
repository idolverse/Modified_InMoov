#include "rclcpp/rclcpp.hpp"
#include "servo_mediator_cpp/udp_receiver_node.hpp"        // UDP 接收节点
#include "servo_mediator_cpp/tcp_receiver_node.hpp"        // TCP 接收节点
#include "servo_mediator_cpp/servo_mediator_node.hpp"      // 中间控制节点
#include "servo_mediator_cpp/websocket_receiver_node.hpp"  // WebSocket 图像接收节点

int main(int argc, char * argv[])
{
    rclcpp::init(argc, argv);

    // 创建各个节点实例
    auto udp_node = std::make_shared<UdpReceiverNode>();
    auto tcp_node = std::make_shared<TcpReceiverNode>();
    auto servo_node = std::make_shared<ServoMediatorNode>();
    auto websocket_node = std::make_shared<WebSocketReceiverNode>();

    // 多线程执行器
    rclcpp::executors::MultiThreadedExecutor executor;
    executor.add_node(udp_node);
    executor.add_node(tcp_node);
    executor.add_node(servo_node);
    executor.add_node(websocket_node);

    // 启动执行
    executor.spin();
    rclcpp::shutdown();
    return 0;
}
