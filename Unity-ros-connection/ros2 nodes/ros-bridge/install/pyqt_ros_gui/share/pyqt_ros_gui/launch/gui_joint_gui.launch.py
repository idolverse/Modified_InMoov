from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        Node(
            package='pyqt_ros_gui',
            executable='gui_node',
            name='gui_joint_publisher',
            output='screen'
        ),
        Node(
            package='pyqt_ros_gui',
            executable='joint_node_receive',
            name='joint_node_receiver',
            output='screen'
        )
    ])
