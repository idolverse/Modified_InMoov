#include "lwip/sockets.h"
#include "lwip/netdb.h"
#include <string.h>
#include <stdio.h>

#define TCP_SERVER_PORT 9000
#define RECV_BUF_SIZE 512

void tcp_server_task(void *argument) {
    int server_fd, client_fd;
    struct sockaddr_in server_addr, client_addr;
    char recv_buf[RECV_BUF_SIZE];
    int ret;

    // 1. 创建socket
    server_fd = socket(AF_INET, SOCK_STREAM, 0);
    if (server_fd < 0) {
        printf("Socket创建失败\r\n");
        return;
    }

    // 2. 绑定端口
    memset(&server_addr, 0, sizeof(server_addr));
    server_addr.sin_family = AF_INET;
    server_addr.sin_port = htons(TCP_SERVER_PORT);
    server_addr.sin_addr.s_addr = INADDR_ANY;
    bind(server_fd, (struct sockaddr *)&server_addr, sizeof(server_addr));

    // 3. 监听
    listen(server_fd, 1);
    printf("STM32 TCP服务已启动，监听端口 %d\r\n", TCP_SERVER_PORT);

    while (1) {
        socklen_t addr_len = sizeof(client_addr);
        client_fd = accept(server_fd, (struct sockaddr *)&client_addr, &addr_len);
        if (client_fd < 0) continue;
        printf("有客户端连接\r\n");

        while (1) {
            memset(recv_buf, 0, RECV_BUF_SIZE);
            ret = recv(client_fd, recv_buf, RECV_BUF_SIZE - 1, 0);
            if (ret <= 0) break;
            printf("收到数据: %s\r\n", recv_buf);

            // 这里可以解析JSON并执行动作（如控制LED、舵机等）
            // 你可以用cJSON库解析recv_buf

            // 示例：收到"hello"命令
            if (strstr(recv_buf, "\"cmd\":\"hello\"")) {
                printf("执行hello动作\r\n");
                // 控制硬件
            }
        }
        closesocket(client_fd);
        printf("客户端断开\r\n");
    }
}
