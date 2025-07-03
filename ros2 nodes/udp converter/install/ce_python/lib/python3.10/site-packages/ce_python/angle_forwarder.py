import rclpy
from rclpy.node import Node
from std_msgs.msg import String
import socket
import json

class ServoMediatorNode(Node):
    def __init__(self):
        super().__init__('servo_mediator')

        self.udp_ip = '192.168.110.48'
        self.udp_port = 4210
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        self.subscription = self.create_subscription(
            String,
            'unity_angle_publisher',
            self.listener_callback,
            10
        )
        self.get_logger().info('ServoMediatorNode started.')

    def listener_callback(self, msg):
        try:
            data = json.loads(msg.data)  # 应为包含 float 的结构
            self.get_logger().info(f'Received JSON with float values: {data}')

            # 不做任何类型转换，直接转发给 ESP32
            payload = json.dumps(data).encode('utf-8')
            self.sock.sendto(payload, (self.udp_ip, self.udp_port))
        except Exception as e:
            self.get_logger().error(f"Error processing message: {e}")

def main(args=None):
    rclpy.init(args=args)
    node = ServoMediatorNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()
