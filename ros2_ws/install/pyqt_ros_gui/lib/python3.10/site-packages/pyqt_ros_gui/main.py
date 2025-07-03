import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from PyQt5.QtWidgets import QApplication
from pyqt_ros_gui.logic.joint_sender import JointSender
from pyqt_ros_gui.ui.joint_gui import JointGUI
import serial

class GUINode(Node):
    def __init__(self):
        super().__init__('gui_joint_publisher')
        self.publisher = self.create_publisher(String, 'processed_joint_states', 10)
        self.gui = None
        self.serial_path = "/dev/serial/by-id/usb-1a86_USB_Serial-if00-port0"
        self.ser = None
        self.try_open_serial()

    def try_open_serial(self):
        try:
            self.ser = serial.Serial(self.serial_path, 115200, timeout=1)
            self.get_logger().info(f"✅ 成功连接串口: {self.serial_path}")
        except serial.SerialException as e:
            self.get_logger().error(f"❌ 无法打开串口 {self.serial_path}: {e}")
            self.ser = None

    def send_joint_commands(self, joint_data):
        lines = []
        for joint, info in joint_data.items():
            position = info.get("position", 0) if isinstance(info, dict) else info
            lines.append(f"{joint}:{position}")

        msg = String()
        msg.data = "\n".join(lines)
        self.publisher.publish(msg)
        self.get_logger().info(f"✅ 发布 joint 数据:\n{msg.data}")

        # 发送给串口
        if self.ser and self.ser.is_open:
            try:
                for line in lines:
                    self.ser.write((line + "\n").encode('utf-8'))
                    print(f"📤 串口发送: {line}")
            except serial.SerialException as e:
                self.get_logger().error(f"串口写入失败: {e}")
                self.ser.close()
                self.try_open_serial()
        else:
            self.try_open_serial()


    # 如果你有用 JSON 监听别的 Topic，可启用
    # def listener_callback(self, msg):
    #     try:
    #         data = json.loads(msg.data)
    #         if self.gui:
    #             self.gui.update_joint_states({k: v['position'] for k, v in data.items()})
    #     except Exception as e:
    #         self.get_logger().error(f"Failed to parse incoming JSON: {e}")

def main():
    rclpy.init()
    node = GUINode()
    logic = JointSender(node)

    app = QApplication([])
    gui = JointGUI(sender=node, logic=logic)
    node.gui = gui
    logic.ui = gui
    gui.show()

    from threading import Thread
    ros_thread = Thread(target=rclpy.spin, args=(node,), daemon=True)
    ros_thread.start()

    app.exec()
    node.destroy_node()
    rclpy.shutdown()
