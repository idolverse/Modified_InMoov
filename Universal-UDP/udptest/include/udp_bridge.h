#ifndef UDP_BRIDGE_H
#define UDP_BRIDGE_H

#include <winsock2.h>
#include <windows.h>
#include <string>
#include <map>
#include <sstream>

#pragma comment(lib, "ws2_32.lib")

class UdpBridge {
public:
    // 默认构造：使用默认 IP 和端口
    UdpBridge(const std::string& ip = "192.168.110.80", int port = 4210, int local_port = 4211) {
        WSAStartup(MAKEWORD(2, 2), &wsa);

        send_sock_ = socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP);
        memset(&ros_addr_, 0, sizeof(ros_addr_));
        ros_addr_.sin_family = AF_INET;
        ros_addr_.sin_port = htons(port);
        ros_addr_.sin_addr.s_addr = inet_addr(ip.c_str());

        recv_sock_ = socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP);
        memset(&ue_addr_, 0, sizeof(ue_addr_));
        ue_addr_.sin_family = AF_INET;
        ue_addr_.sin_port = htons(local_port);
        ue_addr_.sin_addr.s_addr = INADDR_ANY;
        bind(recv_sock_, (SOCKADDR*)&ue_addr_, sizeof(ue_addr_));
    }

    ~UdpBridge() {
        closesocket(send_sock_);
        closesocket(recv_sock_);
        WSACleanup();
    }

    void send(const std::string& topic, const std::map<std::string, int>& data) {
        std::string raw_json = build_json(data);
        std::string escaped = escape_quotes(raw_json);
        std::string msg = "{\"topic\": \"" + topic + "\", \"data\": \"" + escaped + "\"}";
        sendto(send_sock_, msg.c_str(), msg.length(), 0, (SOCKADDR*)&ros_addr_, sizeof(ros_addr_));
        printf("Sent to [%s]: %s\n", topic.c_str(), raw_json.c_str());
    }

private:
    WSADATA wsa;
    SOCKET send_sock_, recv_sock_;
    struct sockaddr_in ros_addr_, ue_addr_;

    std::string build_json(const std::map<std::string, int>& m) {
        std::ostringstream oss;
        oss << "{";
        for (auto it = m.begin(); it != m.end(); ++it) {
            oss << "\"" << it->first << "\": " << it->second;
            if (std::next(it) != m.end()) oss << ", ";
        }
        oss << "}";
        return oss.str();
    }

    std::string escape_quotes(const std::string& input) {
        std::string result;
        for (char c : input) {
            if (c == '\"') result += "\\\"";
            else result += c;
        }
        return result;
    }
};

#endif  // UDP_BRIDGE_H
