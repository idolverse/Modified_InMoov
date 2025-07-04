import socket
import json


class UdpBridge:
    def __init__(self, ip="192.168.110.80", port=4210, local_port=4211):
        self.ros_addr = (ip, port)

        # 发送 Socket
        self.send_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        # 接收 Socket（预留）
        self.recv_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.recv_sock.bind(('', local_port))

    def send(self, topic: str, data: dict):
        raw_json = json.dumps(data)
        escaped = raw_json.replace('"', '\\"')
        msg = f'{{"topic": "{topic}", "data": "{escaped}"}}'
        self.send_sock.sendto(msg.encode('utf-8'), self.ros_addr)
        print(f"Sent to [{topic}]: {raw_json}")

    def close(self):
        self.send_sock.close()
        self.recv_sock.close()
