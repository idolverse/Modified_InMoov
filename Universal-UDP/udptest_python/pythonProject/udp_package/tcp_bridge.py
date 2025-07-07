import socket
import json
import struct

class TCPBridge:
    def __init__(self, ros_ip="192.168.110.80", ros_port=4211):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((ros_ip, ros_port))

    def send(self, topic, data: dict):
        msg = {
            "topic": topic,
            "data": json.dumps(data)
        }
        serialized = json.dumps(msg).encode('utf-8')
        length_prefix = struct.pack("!I", len(serialized))  # 4-byte big-endian
        self.sock.sendall(length_prefix + serialized)

    def close(self):
        self.sock.close()
