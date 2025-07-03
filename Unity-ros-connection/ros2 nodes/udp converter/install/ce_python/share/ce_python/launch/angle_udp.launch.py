from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        Node(
            package='ce_python',
            executable='angle_forwarder',
            name='angle_forwarder',
            output='screen'
        )
    ])
