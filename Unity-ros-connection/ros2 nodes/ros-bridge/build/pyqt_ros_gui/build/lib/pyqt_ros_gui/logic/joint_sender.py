from PyQt5.QtWidgets import QInputDialog, QMessageBox
from ament_index_python.packages import get_package_share_directory
import os, json

class JointSender:
    def __init__(self, node):
        self.node = node
        self.ui = None  # UI 绑定

    def send_data(self, joint_inputs, sender):
        joint_data = {}
        for joint, input_box in joint_inputs.items():
            text = input_box.text()
            if text:
                try:
                    value = float(text)
                    joint_data[joint] = {"position": value}
                except ValueError:
                    pass
        if joint_data:
            sender.send_joint_commands(joint_data)

    def clear_inputs(self, joint_inputs):
        for input_box in joint_inputs.values():
            input_box.clear()

    def run_action(self, action_name, actions, sender):
        for action in actions:
            if action['name'] == action_name:
                joints = action.get('joints', {})
                joint_data = {k: {"position": v} for k, v in joints.items()}
                sender.send_joint_commands(joint_data)
                break

    def start_recording_placeholder(self, latest_joint_state):
        name, ok = QInputDialog.getText(None, "Record Action", "Enter action name:")
        if not (ok and name):
            QMessageBox.warning(None, "Canceled", "Recording canceled or empty name.")
            return

        json_path = os.path.join(get_package_share_directory('pyqt_ros_gui'), 'actions', 'actions.json')

        try:
            with open(json_path, 'r') as f:
                actions = json.load(f)
        except Exception:
            actions = []

        actions.append({
            "name": name,
            "joints": latest_joint_state
        })

        with open(json_path, 'w') as f:
            json.dump(actions, f, indent=2)

        QMessageBox.information(None, "Saved", f"Action '{name}' recorded.")
        print(f"[DEBUG] Action saved to: {json_path}")

        if self.ui and hasattr(self.ui, 'update_action_combo'):
            self.ui.update_action_combo()

    def send_latest_state(self, latest_joint_state, sender):
        joint_data = {k: {"position": v} for k, v in latest_joint_state.items()}
        sender.send_joint_commands(joint_data)
