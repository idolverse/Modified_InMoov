import socket
import json

class TCPBridge:
    def __init__(self, ros_ip="192.168.110.80", ros_port=4211):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((ros_ip, ros_port))

    def send(self, topic, data: dict):
        msg = {
            "topic": topic,
            "data": json.dumps(data)
        }
        serialized = json.dumps(msg)
        self.sock.sendall(serialized.encode('utf-8'))

    def close(self):
        self.sock.close()
