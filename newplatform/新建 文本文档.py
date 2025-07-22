import requests
import time
import statistics
# 这个文件用来测试发送json包的速度 为了和ping的速度对比

def diagnose_send_speed():
    """诊断发送速度瓶颈"""

    print("🔍 开始诊断发送速度...")

    # 1. 测试连接速度
    print("\n1. 测试连接速度...")
    connect_times = []
    for i in range(5):
        start = time.time()
        try:
            resp = requests.post('http://localhost:5000/api/tcp/connect',
                                 json={"ip": "192.168.110.89", "port": 9000},
                                 timeout=5)
            end = time.time()
            connect_times.append(end - start)
            print(f"   连接 {i + 1}: {(end - start) * 1000:.1f}ms")

            # 立即断开
            requests.post('http://localhost:5000/api/tcp/disconnect', timeout=2)
        except Exception as e:
            print(f"   连接 {i + 1} 失败: {e}")

    if connect_times:
        print(f"   平均连接时间: {statistics.mean(connect_times) * 1000:.1f}ms")

    # 2. 测试单次发送速度
    print("\n2. 测试单次发送速度...")

    # 先建立连接
    try:
        resp = requests.post('http://localhost:5000/api/tcp/connect',
                             json={"ip": "192.168.110.89", "port": 9000})
        print(f"   连接建立: {resp.json()}")

        send_times = []
        for i in range(10):
            start = time.time()
            resp = requests.post('http://localhost:5000/api/tcp/send',
                                 json={
                                     "data": {
                                         "device": "HAND",
                                         "command": "move",
                                         "value": i
                                     }
                                 },
                                 timeout=3)
            end = time.time()
            send_times.append(end - start)
            print(f"   发送 {i}: {(end - start) * 1000:.1f}ms")

        if send_times:
            print(f"   平均发送时间: {statistics.mean(send_times) * 1000:.1f}ms")
            print(f"   最快发送时间: {min(send_times) * 1000:.1f}ms")
            print(f"   最慢发送时间: {max(send_times) * 1000:.1f}ms")

        # 断开连接
        requests.post('http://localhost:5000/api/tcp/disconnect')

    except Exception as e:
        print(f"   发送测试失败: {e}")

    # 3. 测试网络延迟
    print("\n3. 测试网络延迟...")
    ping_times = []
    for i in range(5):
        start = time.time()
        try:
            resp = requests.get('http://localhost:5000/ping', timeout=2)
            end = time.time()
            ping_times.append(end - start)
            print(f"   Ping {i + 1}: {(end - start) * 1000:.1f}ms")
        except Exception as e:
            print(f"   Ping {i + 1} 失败: {e}")

    if ping_times:
        print(f"   平均Ping时间: {statistics.mean(ping_times) * 1000:.1f}ms")

    # 4. 测试批量发送
    print("\n4. 测试批量发送速度...")
    try:
        resp = requests.post('http://localhost:5000/api/tcp/connect',
                             json={"ip": "192.168.110.89", "port": 9000})

        start = time.time()
        success_count = 0
        for i in range(20):
            try:
                resp = requests.post('http://localhost:5000/api/tcp/send',
                                     json={
                                         "data": {
                                             "device": "HAND",
                                             "command": "move",
                                             "value": i
                                         }
                                     },
                                     timeout=1)
                success_count += 1
            except:
                pass

        end = time.time()
        total_time = end - start
        print(f"   发送20个值用时: {total_time:.2f}s")
        print(f"   成功发送: {success_count}/20")
        print(f"   平均每个值: {total_time / 20 * 1000:.1f}ms")
        print(f"   理论最大速度: {20 / total_time:.1f}个/秒")

        requests.post('http://localhost:5000/api/tcp/disconnect')

    except Exception as e:
        print(f"   批量测试失败: {e}")

    # 5. 给出优化建议
    print("\n📋 优化建议:")

    if connect_times and statistics.mean(connect_times) > 0.1:
        print("   ⚠️  连接时间过长，可能是服务器性能问题")

    if send_times and statistics.mean(send_times) > 0.05:
        print("   ⚠️  发送时间过长，可能的原因：")
        print("      - 下位机处理慢")
        print("      - 网络延迟高")
        print("      - 服务器处理慢")

    if ping_times and statistics.mean(ping_times) > 0.01:
        print("   ⚠️  网络延迟较高，建议：")
        print("      - 检查网络连接")
        print("      - 使用有线连接")
        print("      - 减少网络负载")

    print("\n🚀 加速方案:")
    print("   1. 使用更短的发送间隔")
    print("   2. 考虑异步发送")
    print("   3. 批量发送多个值")
    print("   4. 直接TCP连接绕过HTTP")


# 异步发送示例
def async_send_example():
    """异步发送示例"""
    import asyncio
    import aiohttp

    async def send_single_value(session, value):
        try:
            async with session.post('http://localhost:5000/api/tcp/send',
                                    json={
                                        "data": {
                                            "device": "HAND",
                                            "command": "move",
                                            "value": value
                                        }
                                    },
                                    timeout=aiohttp.ClientTimeout(total=2)) as resp:
                result = await resp.json()
                print(f"异步发送 {value}: {result}")
                return True
        except Exception as e:
            print(f"异步发送 {value} 失败: {e}")
            return False

    async def async_send_all():
        # 建立连接
        async with aiohttp.ClientSession() as session:
            # 连接
            await session.post('http://localhost:5000/api/tcp/connect',
                               json={"ip": "192.168.110.89", "port": 9000})

            # 创建所有发送任务
            tasks = []
            for value in range(0, 21):  # 发送0-20做测试
                task = send_single_value(session, value)
                tasks.append(task)

            # 并发执行所有任务
            start = time.time()
            results = await asyncio.gather(*tasks, return_exceptions=True)
            end = time.time()

            print(f"异步发送21个值用时: {end - start:.2f}s")
            print(f"平均每个值: {(end - start) / 21 * 1000:.1f}ms")

            # 断开连接
            await session.post('http://localhost:5000/api/tcp/disconnect')

    # 运行异步发送
    asyncio.run(async_send_all())


if __name__ == "__main__":
    diagnose_send_speed()

    print("\n" + "=" * 50)
    print("是否要测试异步发送？(y/n)")
    if input().lower() == 'y':
        try:
            async_send_example()
        except ImportError:
            print("需要安装aiohttp: pip install aiohttp")
