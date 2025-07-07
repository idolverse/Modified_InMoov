import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
import cv2
import mediapipe as mp
import serial
from collections import deque
import threading
import time

class HandGestureNode(Node):
    def __init__(self):
        super().__init__('hand_gesture_node')
        self.bridge = CvBridge()
        self.subscription = self.create_subscription(
            Image,
            '/image_raw',
            self.listener_callback,
            10)

        self.hand = [["Wrist", False], ["IndexFinger", False], ["Middle", False], 
                     ["Ring", False], ["Thumb", False], ["Pinky", False]]
        self.frame_count = 0
        self.WINDOW_SIZE = 5
        self.finger_history = {i: deque([False]*self.WINDOW_SIZE, maxlen=self.WINDOW_SIZE) for i in range(6)}
        self.detector = mp.solutions.hands.Hands(static_image_mode=False, max_num_hands=1,
                                                 min_detection_confidence=0.7, min_tracking_confidence=0.5)
        self.drawer = mp.solutions.drawing_utils

        try:
            self.ser = serial.Serial("/dev/ttyACM0", 9600, timeout=0.1)
            self.get_logger().info(f"Serial port {self.ser.port} opened.")
            threading.Thread(target=self.serial_monitor, daemon=True).start()
        except Exception as e:
            self.get_logger().error(f"Serial error: {e}")
            self.ser = None

    def serial_monitor(self):
        while True:
            try:
                if self.ser.in_waiting > 0:
                    data = self.ser.readline().decode('utf-8').strip()
                    if data:
                        self.get_logger().info(f"[Arduino]: {data}")
            except:
                break
            time.sleep(0.01)

    def listener_callback(self, msg):
        frame = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
        self.frame_count += 1
        image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.detector.process(image_rgb)

        current_state = [False] * 6

        if results.multi_hand_landmarks:
            for handLms in results.multi_hand_landmarks:
                self.drawer.draw_landmarks(frame, handLms, mp.solutions.hands.HAND_CONNECTIONS)

            lmList = []
            h, w, _ = frame.shape
            for id, lm in enumerate(results.multi_hand_landmarks[0].landmark):
                cx, cy = int(lm.x * w), int(lm.y * h)
                lmList.append([id, cx, cy])

            j = 1
            for i in range(1, 6):
                if i == 1:
                    if lmList[4][1] > lmList[3][1]:
                        current_state[4] = True
                else:
                    tip = i * 4
                    pip = i * 4 - 2
                    if tip < len(lmList) and pip < len(lmList):
                        if lmList[tip][2] > lmList[pip][2]:
                            current_state[j] = True
                    j = j + 2 if j == 3 else j + 1

        for i in range(6):
            self.finger_history[i].append(current_state[i])

        if self.frame_count % self.WINDOW_SIZE == 0:
            changed = False
            for i in range(6):
                new_state = sum(self.finger_history[i]) > (self.WINDOW_SIZE // 2)
                if new_state != self.hand[i][1]:
                    self.hand[i][1] = new_state
                    changed = True
                    self.get_logger().info(f"{self.hand[i][0]}: {'BENT' if new_state else 'STRAIGHT'}")

            if changed and self.ser:
                msg = ''.join(['1' if h[1] else '0' for h in self.hand]) + '\n'
                try:
                    self.ser.write(msg.encode("ascii"))
                    self.ser.flush()
                    self.get_logger().info(f"Sent: {msg.strip()}")
                except Exception as e:
                    self.get_logger().error(f"Serial write error: {e}")

        # ✅ OpenCV 显示图像窗口
        cv2.imshow("Hand Gesture Viewer", frame)
        cv2.waitKey(1)

def main(args=None):
    rclpy.init(args=args)
    node = HandGestureNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    node.destroy_node()
    cv2.destroyAllWindows()  # ✅ 清理窗口
    rclpy.shutdown()

if __name__ == '__main__':
    main()
