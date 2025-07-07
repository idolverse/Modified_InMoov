cmake_minimum_required(VERSION 3.5)
project(decode_node)

set(CMAKE_CXX_STANDARD 14)
set(CMAKE_POSITION_INDEPENDENT_CODE ON)

# 查找依赖
find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(std_msgs REQUIRED)
find_package(sensor_msgs REQUIRED)
find_package(OpenCV REQUIRED)
find_package(OpenSSL REQUIRED)

# 包含目录
include_directories(
  include
  ${OpenCV_INCLUDE_DIRS}
)

# 构建节点
add_executable(image_decoder_node src/image_decoder_node.cpp)

ament_target_dependencies(image_decoder_node
  rclcpp
  std_msgs
  sensor_msgs
  OpenCV
)

target_link_libraries(image_decoder_node
  ${OpenCV_LIBRARIES}
  OpenSSL::SSL
  OpenSSL::Crypto
)

install(TARGETS image_decoder_node
  DESTINATION lib/${PROJECT_NAME}
)

ament_package()
