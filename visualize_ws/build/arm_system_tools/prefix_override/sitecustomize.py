import sys
if sys.prefix == '/usr':
    sys.real_prefix = sys.prefix
    sys.prefix = sys.exec_prefix = '/home/guyi/github/Modified_InMoov/visualize_ws/install/arm_system_tools'
