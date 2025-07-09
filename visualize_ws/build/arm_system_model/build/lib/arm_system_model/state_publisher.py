#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import JointState
import math
import time

class JointStatePublisher(Node):
    def __init__(self):
        super().__init__('custom_joint_state_publisher')
        self.publisher_ = self.create_publisher(JointState, 'joint_states', 10)
        self.timer = self.create_timer(0.1, self.timer_callback)
        self.start_time = time.time()
        self.joint_names = [
            'l_shoulder_ud_joint', 'l_shoulder_io_joint', 'l_upper_arm_roll_joint',
            'l_forearm_ud_joint', 'l_forearm_roll_joint', 'l_hand_dumb_joint',
            'r_shoulder_ud_joint', 'r_shoulder_io_joint', 'r_upper_arm_roll_joint',
            'r_forearm_ud_joint', 'r_forearm_roll_joint', 'r_hand_dumb_joint'
        ]
        self.get_logger().info("✅ JointStatePublisher started.")

    def timer_callback(self):
        msg = JointState()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.name = self.joint_names

        t = time.time() - self.start_time
        # 示例：每个关节做一个简单的周期运动
        msg.position = [0.5 * math.sin(t)] * len(self.joint_names)

        self.publisher_.publish(msg)

def main(args=None):
    rclpy.init(args=args)
    node = JointStatePublisher()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
