import rclpy
from rclpy.node import Node
from std_msgs.msg import String
import json

class JointPublisher(Node):
    def __init__(self):
        super().__init__('gui_joint_publisher')

        # 发布 JSON 控制指令
        self.publisher = self.create_publisher(String, 'processed_joint_states', 10)

        # ✅ 实时监听 processed_joint_states
        self.subscription = self.create_subscription(
            String,
            'processed_joint_states',
            self.processed_callback,
            10
        )

        self.gui = None  # main.py 设置
        self.get_logger().info("Subscribed to processed_joint_states")

    def send_joint_commands(self, joint_data):
        msg = String()
        msg.data = json.dumps(joint_data)
        self.publisher.publish(msg)
        self.get_logger().info(f"Sent: {msg.data}")

    def processed_callback(self, msg):
        try:
            data = json.loads(msg.data)
            joint_state_dict = {k: v["position"] for k, v in data.items()}
            if self.gui:
                self.gui.update_joint_states(joint_state_dict)
        except Exception as e:
            self.get_logger().error(f"Failed to parse: {e}")
