import socket

HOST = '0.0.0.0'
PORT = 9000

print(f"下位机TCP服务已启动，监听端口 {PORT}")

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.bind((HOST, PORT))
    s.listen(1)
    conn, addr = s.accept()
    with conn:
        print('连接来自:', addr)
        while True:
            data = conn.recv(1024)
            if not data:
                break
            print('收到:', data)