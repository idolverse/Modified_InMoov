import requests
import time
import json
import base64

# TCP API测试脚本上线！准备发射你的能量指令吧！


def send_with_retry(device, value, max_retries=3, retry_delay=0.5):
    # 发射器上线！失败了也不怕，咱们多试几次！
    for attempt in range(max_retries + 1):
        try:
            resp = requests.post('http://localhost:5000/api/tcp/send',
                                 json={
                                     "data": {
                                         "device": device.upper(),  # "HEAD" or "HAND"，大写更有气场
                                         "command": "move",
                                         "value": value
                                     }
                                 },
                                 timeout=5)
            # 响应到啦！快看看是不是成功了
            if resp.status_code == 200:
                result = resp.json()
                print(f'发送 {device} 值: {value}，结果: {result}')
                # 成功就直接返回，完美收工！
                if result.get('success', True):
                    return True
                else:
                    print(f'发送 {device} 值 {value} 失败，服务器说不行: {result}')
            else:
                print(f'发送 {device} 值 {value} HTTP出错，状态码: {resp.status_code}')
        except requests.exceptions.Timeout:
            print(f'发送 {device} 值 {value} 超时啦 (第 {attempt + 1}/{max_retries + 1} 次)')
        except requests.exceptions.ConnectionError:
            print(f'发送 {device} 值 {value} 连接不上 (第 {attempt + 1}/{max_retries + 1} 次)')
        except Exception as e:
            print(f'发送 {device} 值 {value} 遇到奇怪问题: {e} (第 {attempt + 1}/{max_retries + 1} 次)')
        # 失败了就歇一歇，蓄力再冲！
        if attempt < max_retries:
            print(f'休息 {retry_delay} 秒，马上再来！')
            time.sleep(retry_delay)
    print(f'发送 {device} 值 {value} 最终还是没成功，咱们下次再战！')
    return False


def continuous_send_dual_device(start_value=0, end_value=180, step=10,
                                send_delay=0.1, max_retries=3,
                                retry_delay=0.5, max_failures=5):
    # 连续发射模式！左右开弓，双设备轮流轰炸！
    try:
        resp = requests.post('http://localhost:5000/api/tcp/connect',
                             json={
                                 "ip": "192.168.110.89",
                                 "port": 9000
                             },
                             timeout=10)
        print('连接结果:', resp.json())
    except Exception as e:
        print(f'连接失败了，网络不给力: {e}')
        return False

    total_attempts = 0
    successful_sends = 0
    consecutive_failures = 0

    try:
        for value in range(start_value, end_value + 1, step):
            for device in ['hand', 'head']:
                total_attempts += 1
                success = send_with_retry(device, value, max_retries, retry_delay)
                # 每次都要给自己点赞，努力了就值得被夸！
                if success:
                    successful_sends += 1
                    consecutive_failures = 0
                    print(f'✅ {device.upper()} = {value} 发射成功！棒棒哒！')
                else:
                    consecutive_failures += 1
                    print(f'❌ {device.upper()} = {value} 没发出去，继续加油！')
                    if consecutive_failures >= max_failures:
                        print(f'⚠️ 连续失败 {max_failures} 次，先休息一下吧！')
                        raise RuntimeError('Too many failures')
                time.sleep(send_delay)
            # 每20次来个小结，给自己鼓鼓劲！
            if total_attempts % 20 == 0:
                rate = (successful_sends / total_attempts) * 100
                print(f'📊 已试 {total_attempts} 次，成功率 {rate:.1f}%，继续冲鸭！')
    except KeyboardInterrupt:
        print('\n⏹️ 你主动喊停了，懂了，咱们下次再战！')
    except Exception as e:
        print(f'发送过程中遇到点小状况: {e}')
    finally:
        try:
            resp = requests.post('http://localhost:5000/api/tcp/disconnect', timeout=5)
            print('断开结果:', resp.json())
        except Exception as e:
            print(f'断开连接时也遇到点麻烦: {e}')
        rate = (successful_sends / total_attempts) * 100 if total_attempts > 0 else 0
        print(f'\n📈 最终汇报：')
        print(f'   总共试了：{total_attempts} 次')
        print(f'   成功了：{successful_sends} 次')
        print(f'   没成功：{total_attempts - successful_sends} 次')
        print(f'   成功率：{rate:.1f}%')
        return successful_sends == total_attempts


def send_bytes_command(cmd, max_retries=3, retry_delay=0.5):
    """字节流发射器上线！直接硬刚底层，黑客范儿十足！"""
    for attempt in range(max_retries + 1):
        try:
            send_bytes = cmd.encode('utf-8')
            send_b64 = base64.b64encode(send_bytes).decode('utf-8')
            resp = requests.post('http://localhost:5000/api/tcp/send',
                                 json={"data": send_b64},
                                 timeout=5)
            if resp.status_code == 200:
                result = resp.json()
                print(f'发送命令: {cmd}，结果: {result}')
                if result.get('success', True):
                    return True
            else:
                print(f'HTTP出错，状态码: {resp.status_code}')
        except Exception as e:
            print(f'发送命令 {cmd} 出错啦: {e} (第 {attempt + 1}/{max_retries + 1} 次)')
        if attempt < max_retries:
            time.sleep(retry_delay)
    print(f'发送命令 {cmd} 还是没成功，咱们下次再来！')
    return False


# 程序入口，准备开火！冲冲冲！
if __name__ == "__main__":
    success = continuous_send_dual_device(
        start_value=0,
        end_value=180,
        step=10,
        send_delay=0.1,
        max_retries=3,
        retry_delay=0.5,
        max_failures=5
    )

    if success:
        print('🎉 所有数据发送成功！完美收官！')
    else:
        print('⚠️ 有些数据没发出去，遗憾收场，下次一定！')

    # 试试直接发射一条SERVO命令，秀一波操作
    send_bytes_command("SERVO:1,90\n")
