cmake_minimum_required(VERSION 3.10)
project(udptest)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# 添加头文件目录（当前目录）
include_directories(${CMAKE_SOURCE_DIR}/include)

add_executable(udptest main.cpp)