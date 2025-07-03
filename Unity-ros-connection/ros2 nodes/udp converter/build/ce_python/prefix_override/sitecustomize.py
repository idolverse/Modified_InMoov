import sys
if sys.prefix == '/usr':
    sys.real_prefix = sys.prefix
    sys.prefix = sys.exec_prefix = '/home/guyi/cececeCeESP/ros2_ws/install/ce_python'
