import sys
if sys.prefix == '/usr':
    sys.real_prefix = sys.prefix
    sys.prefix = sys.exec_prefix = '/home/guyi/github/Modified_InMoov/Unity-ros-connection/ros2 nodes/install/ros_tcp_endpoint'
