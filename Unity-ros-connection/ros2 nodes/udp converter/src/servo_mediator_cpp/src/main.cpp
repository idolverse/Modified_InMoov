#include "rclcpp/rclcpp.hpp"
#include "servo_mediator_cpp/udp_receiver_node.hpp"
#include "servo_mediator_cpp/servo_mediator_node.hpp"

int main(int argc, char * argv[])
{
    rclcpp::init(argc, argv);
    auto udp_node = std::make_shared<UdpReceiverNode>();
    auto servo_node = std::make_shared<ServoMediatorNode>();

    rclcpp::executors::MultiThreadedExecutor executor;
    executor.add_node(udp_node);
    executor.add_node(servo_node);
    executor.spin();
    rclcpp::shutdown();
    return 0;
}
