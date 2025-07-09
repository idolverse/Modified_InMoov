from moveit_configs_utils import MoveItConfigsBuilder
from moveit_configs_utils.launches import generate_spawn_controllers_launch

from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    moveit_config = MoveItConfigsBuilder("ArmsnHands", package_name="suP_moveit_config").to_moveit_configs()

    # 添加 joint_state_broadcaster spawner 节点
    joint_state_broadcaster_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["joint_state_broadcaster"],
        output="screen",
    )

    # MoveIt 自动生成的控制器加载
    moveit_controllers = generate_spawn_controllers_launch(moveit_config)

    # 合并两个 LaunchDescription
    return LaunchDescription([
        joint_state_broadcaster_spawner,
        *moveit_controllers.entities
    ])

