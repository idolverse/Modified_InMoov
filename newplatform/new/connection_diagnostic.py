import serial
import serial.tools.list_ports
import time

def comprehensive_arduino_test():
    """全面的Arduino连接诊断"""
    print("🔍 Arduino连接全面诊断")
    print("=" * 50)
    
    # 1. 检查可用端口
    print("📱 步骤1: 检查可用串口")
    print("-" * 30)
    
    ports = []
    for port in serial.tools.list_ports.comports():
        ports.append(port.device)
        print(f"发现端口: {port.device} - {port.description}")
    
    if not ports:
        print("❌ 未发现任何串口设备！")
        print("🔧 解决方案：")
        print("   1. 检查USB线是否连接")
        print("   2. 检查Arduino是否有电源指示灯")
        print("   3. 重新插拔USB线")
        print("   4. 检查设备管理器中的COM口")
        return False
    
    print(f"✅ 发现 {len(ports)} 个串口设备")
    
    # 2. 测试每个端口的不同波特率
    for port in ports:
        print(f"\n🔌 步骤2: 详细测试端口 {port}")
        print("-" * 30)
        
        # 尝试不同波特率
        baud_rates = [115200, 9600, 57600, 38400]
        
        for baud in baud_rates:
            print(f"尝试波特率 {baud}...")
            
            try:
                # 尝试打开串口
                ser = serial.Serial(port, baud, timeout=3)
                print(f"✅ 串口 {port} 在波特率 {baud} 下成功打开")
                
                # 等待Arduino启动
                print("⏳ 等待Arduino启动...")
                time.sleep(4)  # 给Arduino充分的启动时间
                
                # 清空缓冲区
                ser.flushInput()
                ser.flushOutput()
                time.sleep(0.5)
                
                # 读取启动消息
                print("📖 读取Arduino启动消息...")
                startup_messages = []
                start_time = time.time()
                
                while time.time() - start_time < 5:  # 增加等待时间
                    if ser.in_waiting > 0:
                        try:
                            line = ser.readline().decode().strip()
                            if line:
                                startup_messages.append(line)
                                print(f"   📨 Arduino: {line}")
                        except Exception as decode_error:
                            print(f"   ⚠️  解码错误: {decode_error}")
                    time.sleep(0.1)
                
                has_startup = len(startup_messages) > 0
                has_face_system = any("Face Control System" in msg for msg in startup_messages)
                has_ready = any("Ready" in msg or "ARDUINO_READY" in msg for msg in startup_messages)
                
                print(f"📊 启动消息统计:")
                print(f"   消息数量: {len(startup_messages)}")
                print(f"   包含'Face Control System': {has_face_system}")
                print(f"   包含就绪信号: {has_ready}")
                
                if has_startup:
                    print("✅ 收到Arduino启动消息")
                    
                    if has_face_system:
                        print("🎯 确认是面部控制系统代码！")
                        
                        # 清空缓冲区准备测试命令
                        ser.flushInput()
                        ser.flushOutput()
                        time.sleep(0.5)
                        
                        # 测试PING命令
                        print("📡 测试PING命令...")
                        ser.write(b"PING\n")
                        ser.flush()
                        time.sleep(1)
                        
                        ping_response = ""
                        if ser.in_waiting > 0:
                            ping_response = ser.readline().decode().strip()
                            print(f"PING响应: {ping_response}")
                            
                            if ping_response == "PONG":
                                print("✅ PING测试成功！")
                                
                                # 测试基本舵机命令
                                print("🎮 测试基本舵机命令...")
                                
                                test_commands = [
                                    ("CENTER", "中心位置"),
                                    ("FACE:PHILTRUM,85", "人中控制"),
                                    ("FACE:CHIN,150", "下巴控制"),
                                    ("STATUS", "状态查询")
                                ]
                                
                                all_commands_ok = True
                                for cmd, desc in test_commands:
                                    print(f"   🔧 {desc}: {cmd}")
                                    ser.write((cmd + '\n').encode())
                                    ser.flush()
                                    time.sleep(0.8)
                                    
                                    if ser.in_waiting > 0:
                                        resp = ser.readline().decode().strip()
                                        print(f"   📥 响应: {resp}")
                                        if "OK" in resp or "STATUS" in resp:
                                            print("   ✅ 命令执行成功")
                                        else:
                                            print("   ⚠️  响应异常")
                                            all_commands_ok = False
                                    else:
                                        print("   ❌ 无响应")
                                        all_commands_ok = False
                                
                                ser.close()
                                
                                if all_commands_ok:
                                    print(f"\n🎉 诊断完成！Arduino工作正常！")
                                    print(f"✅ 推荐设置:")
                                    print(f"   端口: {port}")
                                    print(f"   波特率: {baud}")
                                    print(f"   Arduino代码: 面部控制系统 (支持PING)")
                                    print(f"   下巴角度范围: 45-300")
                                    return True
                                else:
                                    print("⚠️  部分命令失败，但基本连接正常")
                            else:
                                print("❌ PING响应错误")
                        else:
                            print("❌ PING无响应，可能是旧版Arduino代码")
                    else:
                        print("⚠️  Arduino有响应但可能不是面部控制代码")
                else:
                    print("❌ 无Arduino启动消息")
                
                ser.close()
                
            except serial.SerialException as e:
                print(f"❌ 波特率 {baud} 连接失败: {e}")
            except Exception as e:
                print(f"❌ 测试异常: {e}")
    
    print(f"\n❌ 所有端口和波特率测试完毕，未找到正常工作的Arduino")
    print("🔧 建议解决方案：")
    print("   1. 🔄 重新烧录Arduino代码")
    print("      文件: c:\\Users\\a's\\Desktop\\newplatform\\new\\arduino_pca9685\\arduino_pca9685.ino")
    print("   2. 🔌 检查PCA9685模块连接")
    print("      VCC -> 5V, GND -> GND, SCL -> A5, SDA -> A4")
    print("   3. ⚡ 检查电源供应")
    print("      确保Arduino和PCA9685都有足够电源")
    print("   4. 🛠️  使用Arduino IDE串口监视器直接测试")
    print("      波特率115200，发送PING命令，应该收到PONG响应")
    
    return False

if __name__ == "__main__":
    success = comprehensive_arduino_test()
    if not success:
        print(f"\n🆘 如果问题仍然存在，请：")
        print(f"   1. 确认Arduino IDE中选择了正确的开发板(Arduino Uno)")
        print(f"   2. 确认选择了正确的COM口")
        print(f"   3. 重新编译并上传Arduino代码")
        print(f"   4. 检查串口是否被其他程序占用")
    
    input("\n按回车键退出...")
