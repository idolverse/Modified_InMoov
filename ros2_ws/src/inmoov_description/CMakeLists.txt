cmake_minimum_required(VERSION 3.5)
project(inmoov_description)

# Find ament and other dependencies
find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(gazebo_ros REQUIRED)
find_package(sensor_msgs REQUIRED)
find_package(std_msgs REQUIRED)
# Add any additional ROS 2 dependencies here if necessary

# Specify where the source files are located (if applicable)
# install(DIRECTORY urdf DESTINATION share/${PROJECT_NAME}/urdf)

# This will install your URDF and any necessary files.
install(DIRECTORY urdf
  DESTINATION share/${PROJECT_NAME}/urdf)

# Declare ament package
ament_package()

