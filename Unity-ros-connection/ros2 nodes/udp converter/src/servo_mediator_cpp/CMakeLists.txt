cmake_minimum_required(VERSION 3.5)
project(servo_mediator_cpp)
include_directories(include)

set(CMAKE_CXX_STANDARD 14)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# 查找依赖
find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(std_msgs REQUIRED)
find_package(nlohmann_json REQUIRED)

# 源文件
set(NODE_SRC_1 src/servo_mediator_node.cpp)
set(NODE_SRC_2 src/udp_receiver_node.cpp)

# 单独节点编译
# add_executable(servo_mediator_node ${NODE_SRC_1})
# add_executable(udp_receiver_node ${NODE_SRC_2})

# 多节点组合执行程序
add_executable(combined_node src/main.cpp)
target_sources(combined_node PRIVATE ${NODE_SRC_1} ${NODE_SRC_2})

# 链接依赖

ament_target_dependencies(combined_node rclcpp std_msgs nlohmann_json)

# 安装所有可执行文件
install(TARGETS
  combined_node
  DESTINATION lib/${PROJECT_NAME}
)

ament_package()
