from moveit_configs_utils import MoveItConfigsBuilder
from moveit_configs_utils.launches import generate_spawn_controllers_launch

from launch import LaunchDescription


def generate_launch_description():
    moveit_config = MoveItConfigsBuilder("ArmsnHands", package_name="sup_moveit_config").to_moveit_configs()

    # MoveIt 自动生成的控制器加载（包含你的 left_arm_controller 等）
    moveit_controllers = generate_spawn_controllers_launch(moveit_config)

    # 直接返回，不再重复加载 joint_state_broadcaster
    return LaunchDescription(moveit_controllers.entities)
