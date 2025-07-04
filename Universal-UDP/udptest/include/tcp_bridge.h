#ifndef TCP_BRIDGE_HPP
#define TCP_BRIDGE_HPP

#include <winsock2.h>
#include <windows.h>
#include <string>
#include <map>
#include <sstream>

#pragma comment(lib, "ws2_32.lib")

class TCPBridge {
public:
    TCPBridge(const std::string& ip = "127.0.0.1", int port = 4211) {
        WSAStartup(MAKEWORD(2, 2), &wsa);
        sock_ = socket(AF_INET, SOCK_STREAM, IPPROTO_TCP);

        sockaddr_in addr{};
        addr.sin_family = AF_INET;
        addr.sin_port = htons(port);
        addr.sin_addr.s_addr = inet_addr(ip.c_str());

        connect(sock_, (SOCKADDR*)&addr, sizeof(addr));
    }

    ~TCPBridge() {
        closesocket(sock_);
        WSACleanup();
    }

    void send(const std::string& topic, const std::map<std::string, int>& data) {
        std::string json_str = build_json_string(topic, data);
        send(sock_, json_str.c_str(), json_str.length(), 0);
    }

private:
    WSADATA wsa;
    SOCKET sock_;

    std::string build_json_string(const std::string& topic, const std::map<std::string, int>& data) {
        std::ostringstream oss;
        oss << "{\"topic\":\"" << topic << "\",\"data\":{";
        for (auto it = data.begin(); it != data.end(); ++it) {
            oss << "\"" << it->first << "\":" << it->second;
            if (std::next(it) != data.end()) oss << ",";
        }
        oss << "}}";
        return oss.str();
    }
};

#endif // TCP_BRIDGE_HPP
