import cv2
import base64
import time
from udp_package.websocket_bridge import WebSocketBridge

def main():
    bridge = WebSocketBridge("ws://192.168.110.80:8765")  # 换成实际 ROS2 WebSocket 地址
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("无法打开摄像头")
        return

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            success, buffer = cv2.imencode('.jpg', frame)
            if not success:
                continue  # 或 return/raise，根据需求
            b64_str = base64.b64encode(buffer).decode('utf-8')
            bridge.send("/image_raw", {"img": b64_str})

            cv2.imshow("Sender", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

            time.sleep(0.03)

    finally:
        bridge.close()
        cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
