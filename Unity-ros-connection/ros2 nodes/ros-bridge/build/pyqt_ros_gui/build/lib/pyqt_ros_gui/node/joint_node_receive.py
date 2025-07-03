import rclpy
from rclpy.node import Node
from std_msgs.msg import String
import json

class JointReceiver(Node):
    def __init__(self):
        super().__init__('joint_node_receive')
        self.subscription = self.create_subscription(
            String,
            'processed_joint_states',
            self.listener_callback,
            10
        )
        self.get_logger().info("Subscribed to 'processed_joint_states'")

    def listener_callback(self, msg):
        try:
            joint_data = json.loads(msg.data)
            self.get_logger().info("Received joint data:")
            for joint, value_dict in joint_data.items():
                pos = value_dict.get("position", "N/A")
                self.get_logger().info(f"  {joint}: {pos}")
        except json.JSONDecodeError:
            self.get_logger().error("Failed to decode JSON from message")

def main(args=None):
    rclpy.init(args=args)
    node = JointReceiver()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
