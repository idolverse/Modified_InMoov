cmake_minimum_required(VERSION 3.5)
project(servo_mediator_cpp)

set(CMAKE_CXX_STANDARD 14)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# ✅ 查找依赖
find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(std_msgs REQUIRED)
find_package(nlohmann_json REQUIRED)
find_package(OpenCV REQUIRED)
find_package(cv_bridge REQUIRED)
find_package(sensor_msgs REQUIRED)

# ✅ 手动添加 libcurl 和 libtiff
find_library(CURL_LIB curl)
find_library(TIFF_LIB tiff)

# ✅ 添加头文件目录
include_directories(
  include
  ${OpenCV_INCLUDE_DIRS}
)

# ✅ 源文件列表
set(NODE_SRC
  src/main.cpp
  src/servo_mediator_node.cpp
  src/udp_receiver_node.cpp
  src/tcp_receiver_node.cpp
  src/websocket_receiver_node.cpp
)

# ✅ 构建可执行文件
add_executable(combined_node ${NODE_SRC})

# ✅ 添加依赖
ament_target_dependencies(combined_node
  rclcpp
  std_msgs
  sensor_msgs       # ✅ 添加
  nlohmann_json
  OpenCV
  cv_bridge         # ✅ 添加
)


# ✅ 链接库
target_link_libraries(combined_node
  ${OpenCV_LIBS}
  ${CURL_LIB}
  ${TIFF_LIB}
)

# ✅ 安装
install(TARGETS
  combined_node
  DESTINATION lib/${PROJECT_NAME}
)

ament_package()
