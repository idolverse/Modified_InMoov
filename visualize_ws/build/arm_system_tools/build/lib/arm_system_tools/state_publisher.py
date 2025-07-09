#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import JointState
from builtin_interfaces.msg import Time
import math

class ArmStatePublisher(Node):
    def __init__(self):
        super().__init__('state_publisher')
        self.publisher_ = self.create_publisher(JointState, 'joint_states', 10)
        self.timer = self.create_timer(0.1, self.timer_callback)

        self.angle = 0.0
        self.get_logger().info("✅ arm_system_tools state_publisher started")

    def timer_callback(self):
        now = self.get_clock().now().to_msg()

        joint_state = JointState()
        joint_state.header.stamp = now
        joint_state.name = [
            'elbow_joint',
            'forearm_updown_joint',
            'foreamr_roll_joint'
        ]
        joint_state.position = [
            math.sin(self.angle),
            math.sin(self.angle) * 0.5,
            math.cos(self.angle) * 0.25
        ]

        self.publisher_.publish(joint_state)
        self.angle += 0.05

def main(args=None):
    rclpy.init(args=args)
    node = ArmStatePublisher()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()

