#include "include/udp_bridge.h"
#include <random>
#include <map>

int main() {
    UdpBridge bridge;
    std::random_device rd;
    std::mt19937 gen(rd());
    std::uniform_int_distribution<> dis(0, 180);

    while (true) {
        int angle1 = dis(gen);
        int angle2 = dis(gen);

        std::map<std::string, int> control_data = {
            {"servo1", angle1},
            {"servo2", angle2}
        };

        // 修改这里的 topic 字符串
        bridge.send("unity_angle_publisher", control_data);

        Sleep((angle1 + angle2) * 2);
    }

    return 0;
}
