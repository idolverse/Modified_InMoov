from launch import LaunchDescription
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory
import os
from moveit_configs_utils import MoveItConfigsBuilder
from launch.substitutions import PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare
from launch.actions import TimerAction

def generate_launch_description():
    pkg_share = get_package_share_directory("sup_moveit_model")

    srdf_path = os.path.join(pkg_share, "config", "ArmsnHands.srdf")
    with open(srdf_path, "r") as f:
        srdf_content = f.read()

    moveit_config = (
        MoveItConfigsBuilder("ArmsnHands", package_name="sup_moveit_model")
        .robot_description(file_path="config/ArmsnHands.urdf.xacro")
        .robot_description_semantic(file_path="config/ArmsnHands.srdf")
        .robot_description_kinematics(file_path="config/kinematics.yaml")
        .to_moveit_configs()
    )

    controllers_yaml = PathJoinSubstitution([
        FindPackageShare("sup_moveit_model"),
        "config", "ros2_controllers.yaml"
    ])

    # ✅ 启动 ros2_control_node 和 spawner 要在同一 launch
    control_node = Node(
        package="controller_manager",
        executable="ros2_control_node",
        parameters=[
            moveit_config.robot_description,
            controllers_yaml
        ],
        output="screen"
    )

    # ✅ 延时启动 controller spawners，确保 control_node 启动完成
    spawner_delay = 3.0  # 秒

    return LaunchDescription([
        control_node,

        TimerAction(
            period=spawner_delay,
            actions=[
                Node(
                    package="controller_manager",
                    executable="spawner",
                    arguments=["joint_state_broadcaster"],
                    output="screen"
                ),
                Node(
                    package="controller_manager",
                    executable="spawner",
                    arguments=["left_arm_controller"],
                    output="screen"
                ),
                Node(
                    package="controller_manager",
                    executable="spawner",
                    arguments=["right_arm_controller"],
                    output="screen"
                )
            ]
        ),

        Node(
            package="moveit_ros_move_group",
            executable="move_group",
            output="screen",
            parameters=[
                moveit_config.robot_description,
                {"robot_description_semantic": srdf_content},
                moveit_config.robot_description_kinematics,
                moveit_config.joint_limits,
                moveit_config.planning_pipelines,
                {"moveit_controller_manager": "moveit_simple_controller_manager/MoveItSimpleControllerManager"},
                PathJoinSubstitution([
                FindPackageShare("sup_moveit_model"),
                "config",
                "moveit_controllers.yaml"
        ]),
                {"publish_robot_description": True},
                {"publish_robot_description_semantic": True},
            ]
        ),

        Node(
            package="rviz2",
            executable="rviz2",
            arguments=["-d", os.path.join(pkg_share, "config", "moveit.rviz")],
            parameters=[
                moveit_config.robot_description,
                {"robot_description_semantic": srdf_content},
            ],
            output="screen"
        )
    ])
