from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        Node(
            package='ce_python',
            executable='angle_forwarder',
            name='angle_forwarder',
            output='screen'
        ),
        Node(
            package='ce_python',
            executable='image_publish_node',
            name='image_publish_node',
            output='screen'
        ),
        Node(
            package='ce_python',
            executable='hand_gesture_node',
            name='hand_gesture_node',
            output='screen'
        )
    ])
