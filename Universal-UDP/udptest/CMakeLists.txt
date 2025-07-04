cmake_minimum_required(VERSION 3.10)
project(udptest)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# 添加 OpenCV 和你自己的头文件路径
include_directories(
        ${CMAKE_SOURCE_DIR}/include
        ${CMAKE_SOURCE_DIR}/include/opencv/build/include
        ${CMAKE_SOURCE_DIR}/include/opencv/build/include/opencv2
)

# 链接 OpenCV 库路径
link_directories(${CMAKE_SOURCE_DIR}/include/opencv/build/x64/vc16/lib)

# 添加 OpenCV 依赖的库文件（根据你实际的 OpenCV 版本）
set(OPENCV_LIBS
        opencv_world4120.lib
)

# 编译
add_executable(udptest main.cpp)
target_link_libraries(udptest ${OPENCV_LIBS})
