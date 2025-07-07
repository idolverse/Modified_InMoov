#ifndef WEBSOCKET_BRIDGE_H
#define WEBSOCKET_BRIDGE_H

#include <string>
#include <thread>
#include <atomic>
#include <mutex>
#include <queue>
#include <condition_variable>
#include <websocketpp/client.hpp>
#include <websocketpp/config/asio_no_tls_client.hpp>
#include <nlohmann/json.hpp>

typedef websocketpp::client<websocketpp::config::asio_client> ws_client;

class WebSocketBridge {
public:
    explicit WebSocketBridge(const std::string& uri);
    ~WebSocketBridge();

    void send(const std::string& topic, const nlohmann::json& data);
    void close();

private:
    void run();
    void connect();

    std::string uri_;
    std::atomic<bool> connected_;
    std::thread thread_;
    ws_client client_;
    websocketpp::connection_hdl connection_hdl_;
    std::mutex send_mutex_;
    std::condition_variable cv_;
};

#endif  // WEBSOCKET_BRIDGE_H
