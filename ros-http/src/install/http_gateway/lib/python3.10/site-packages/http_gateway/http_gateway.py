import rclpy
from rclpy.node import Node
from flask import Flask, request, jsonify
import threading
import importlib
import base64
import numpy as np
import cv2
from std_msgs.msg import String

SUPPORTED_TYPES = {
    "std_msgs/String": "std_msgs.msg.String",
    "std_msgs/Float64": "std_msgs.msg.Float64",
    "geometry_msgs/Twist": "geometry_msgs.msg.Twist",
    "sensor_msgs/CompressedImage": "sensor_msgs.msg.CompressedImage",
    "sensor_msgs/Image": "sensor_msgs.msg.Image",
}

class HttpGatewayNode(Node):
    def __init__(self):
        super().__init__('http_gateway_node')
        self.topic_publishers = {}

    def get_publisher(self, topic, msg_type_str):
        if topic not in self.topic_publishers:
            module_name, class_name = SUPPORTED_TYPES[msg_type_str].rsplit(".", 1)
            msg_module = importlib.import_module(module_name)
            msg_class = getattr(msg_module, class_name)
            pub = self.create_publisher(msg_class, topic, 10)
            self.topic_publishers[topic] = (pub, msg_class)
        return self.topic_publishers[topic]

    def publish(self, topic, msg_type_str, data_dict):
        pub, msg_class = self.get_publisher(topic, msg_type_str)
        msg = msg_class()
        for k, v in data_dict.items():
            setattr(msg, k, v)
        pub.publish(msg)
        self.get_logger().info(f"✅ Published to {topic}: {data_dict}")

        # 图像类型转发到 base64 decode 节点
        if msg_type_str in ["sensor_msgs/CompressedImage", "sensor_msgs/Image"]:
            self.handle_image_encoding(msg_type_str, data_dict)

    def handle_image_encoding(self, msg_type_str, data_dict):
        if msg_type_str == "sensor_msgs/CompressedImage":
            raw_bytes = bytes(data_dict["data"])
        elif msg_type_str == "sensor_msgs/Image":
            height = data_dict["height"]
            width = data_dict["width"]
            channels = data_dict.get("step", 3) // width
            img_np = np.frombuffer(bytes(data_dict["data"]), dtype=np.uint8).reshape((height, width, channels))
            _, buffer = cv2.imencode('.jpg', img_np)
            raw_bytes = buffer.tobytes()
        else:
            return

        b64 = base64.b64encode(raw_bytes).decode("utf-8")
        pub, _ = self.get_publisher("/compressed_image_base64", "std_msgs/String")
        pub.publish(String(data=b64))
        self.get_logger().info("🖼️ Sent base64 image to /compressed_image_base64")

    def get_status(self):
        return {
            "topics": [
                {"topic": topic, "type": pub[1].__name__}
                for topic, pub in self.topic_publishers.items()
            ]
        }

def main():
    rclpy.init()
    node = HttpGatewayNode()
    app = Flask("http_gateway")

    @app.route("/", methods=["POST"])
    def handle_post():
        content = request.get_json()
        try:
            topic = content["topic"]
            msg_type = content["type"]
            data = content["data"]
            if msg_type not in SUPPORTED_TYPES:
                return jsonify({"error": f"Unsupported type {msg_type}"}), 400
            node.publish(topic, msg_type, data)
            return jsonify({"status": "ok"})
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/status", methods=["GET"])
    def handle_status():
        return jsonify(node.get_status())

    threading.Thread(target=lambda: app.run(host="0.0.0.0", port=5000), daemon=True).start()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    node.destroy_node()
    rclpy.shutdown()
