from moveit_configs_utils import MoveItConfigsBuilder
from moveit_configs_utils.launches import generate_move_group_launch, generate_rviz_config, generate_planning_scene_monitor_launch

from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    moveit_config = (
        MoveItConfigsBuilder("ArmsnHands", package_name="sup_moveit_config")
        .to_moveit_configs()
    )

    return LaunchDescription([
        # 启动 move_group node
        generate_move_group_launch(moveit_config),
        
        # 启动 RViz 并加载配置
        generate_rviz_config(moveit_config),

        # 可选：发布 joint_state_broadcaster
        Node(
            package="controller_manager",
            executable="spawner",
            arguments=["joint_state_broadcaster"],
            output="screen"
        ),
    ])
