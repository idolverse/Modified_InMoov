import cv2
import base64
import time
import requests

HTTP_URL = "http://192.168.110.80:5000/"  # HTTP Gateway 地址
TOPIC = "/image_raw"
MSG_TYPE = "sensor_msgs/CompressedImage"

def main():
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
                continue

            b64_str = base64.b64encode(buffer).decode('utf-8')

            # 构造 HTTP 请求
            payload = {
                "topic": TOPIC,
                "type": MSG_TYPE,
                "data": {
                    "format": "jpeg",
                    "data": b64_str
                }
            }

            try:
                requests.post(HTTP_URL, json=payload, timeout=1)
            except Exception as e:
                print(f"❌ Failed to POST: {e}")

            cv2.imshow("HTTP Sender", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

            time.sleep(0.03)

    finally:
        cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
