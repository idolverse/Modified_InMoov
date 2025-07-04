import cv2
import base64
from udp_package.tcp_bridge import TCPBridge
import time

def main():
    bridge = TCPBridge()
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("无法打开摄像头")
        return

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("无法读取帧")
                break

            _, buffer = cv2.imencode('.jpg', frame)
            jpg_bytes = buffer.tobytes()
            b64_str = base64.b64encode(jpg_bytes).decode('utf-8')

            bridge.send("image_raw", {"img": b64_str})

            cv2.imshow("TCP Sender", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

            time.sleep(0.03)

    finally:
        cap.release()
        bridge.close()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
