import rclpy
from rclpy.node import Node
from std_msgs.msg import String
import json
import base64
import cv2
import numpy as np

class ImageViewerNode(Node):
    def __init__(self):
        super().__init__('image_viewer_node')
        self.subscription = self.create_subscription(
            String,
            '/image_raw',
            self.listener_callback,
            10
        )
        self.get_logger().info("🖼️ ImageViewerNode started, subscribed to /image_raw")

    def listener_callback(self, msg):
        try:
            img_json = json.loads(msg.data)
            b64_str = img_json['img']
            img_bytes = base64.b64decode(b64_str)
            np_arr = np.frombuffer(img_bytes, np.uint8)
            img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
            if img is not None:
                cv2.imshow("Image Viewer", img)
                cv2.waitKey(1)
        except Exception as e:
            self.get_logger().warn(f"❌ Failed to display image: {e}")

def main(args=None):
    rclpy.init(args=args)
    node = ImageViewerNode()
    rclpy.spin(node)
    cv2.destroyAllWindows()
    node.destroy_node()
    rclpy.shutdown()
