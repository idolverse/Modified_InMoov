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

# 所有源文件
set(NODE_SRC
        src/main.cpp
        src/servo_mediator_node.cpp
        src/udp_receiver_node.cpp
        src/tcp_receiver_node.cpp  # ✅ 加入 TCP 节点源文件
)

# 构建可执行文件
add_executable(combined_node ${NODE_SRC})
ament_target_dependencies(combined_node rclcpp std_msgs nlohmann_json)

# 安装
install(TARGETS
        combined_node
        DESTINATION lib/${PROJECT_NAME}
)

ament_package()
