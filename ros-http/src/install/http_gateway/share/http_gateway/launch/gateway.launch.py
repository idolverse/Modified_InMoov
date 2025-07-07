from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        Node(
            package='http_gateway',
            executable='http_gateway',  # 来自 setup.py 的 console_scripts
            name='http_gateway_node',
            output='screen'
        )
    ])
