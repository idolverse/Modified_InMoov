import os

def get_src_action_json_path():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    src_actions_path = os.path.abspath(os.path.join(current_dir, "..", "actions", "actions.json"))
    return src_actions_path
