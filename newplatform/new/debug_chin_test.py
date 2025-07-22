import serial
import serial.tools.list_ports
import time

def test_all_ports():
    """测试所有可用COM口，找到PCA9685版本"""
    print("=== 全端口Arduino版本检测 ===")
    
    # 获取所有可用端口
    ports = []
    for port in serial.tools.list_ports.comports():
        ports.append(port.device)
    
    print(f"发现可用端口: {ports}")
    
    if not ports:
        print("❌ 未发现任何串口设备")
        return None
    
    for port in ports:
        print(f"\n🔍 测试端口: {port}")
        try:
            ser = serial.Serial(port, 115200, timeout=2)
            time.sleep(3)
            
            # 清空缓冲区
            while ser.in_waiting > 0:
                ser.read()
            
            # 发送PING测试
            ser.write(b"PING\n")
            ser.flush()
            time.sleep(1)
            
            if ser.in_waiting > 0:
                response = ser.readline().decode().strip()
                print(f"PING响应: {response}")
                
                if response == "PONG":
                    print(f"✅ 找到PCA9685版本在端口: {port}")
                    
                    # 测试下巴控制
                    print("🎯 测试PCA9685下巴控制...")
                    test_angles = [60, 90, 120]
                    
                    for angle in test_angles:
                        print(f"测试下巴角度: {angle}")
                        command = f"FACE:CHIN,{angle}\n"
                        ser.write(command.encode())
                        ser.flush()
                        time.sleep(0.5)
                        
                        if ser.in_waiting > 0:
                            resp = ser.readline().decode().strip()
                            print(f"响应: {resp}")
                        
                        time.sleep(2)
                    
                    ser.close()
                    return port
                else:
                    print(f"❌ 端口{port}是face_control版本 (响应: {response})")
            else:
                print(f"❌ 端口{port}无PING响应，可能是face_control版本")
            
            ser.close()
            
        except Exception as e:
            print(f"❌ 端口{port}连接失败: {e}")
    
    print("❌ 未找到PCA9685版本的Arduino")
    return None

def test_specific_port(port):
    """详细测试指定端口"""
    print(f"\n=== 详细测试端口 {port} ===")
    try:
        ser = serial.Serial(port, 115200, timeout=2)
        time.sleep(3)
        
        print("📱 读取启动消息...")
        startup_messages = []
        for _ in range(10):
            if ser.in_waiting > 0:
                try:
                    line = ser.readline().decode().strip()
                    if line:
                        startup_messages.append(line)
                        print(f"启动消息: {line}")
                except:
                    pass
            time.sleep(0.1)
        
        # 清空缓冲区
        while ser.in_waiting > 0:
            ser.read()
        
        print("🔍 检查版本...")
        # 发送PING
        ser.write(b"PING\n")
        ser.flush()
        time.sleep(1)
        
        if ser.in_waiting > 0:
            response = ser.readline().decode().strip()
            print(f"PING响应: {response}")
            
            if response == "PONG":
                print("✅ 确认是PCA9685版本")
                return True, "PCA9685"
            else:
                print("❌ 确认是face_control版本")
                return True, "face_control"
        else:
            print("❌ 无PING响应，确认是face_control版本")
            return True, "face_control"
        
        ser.close()
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False, "unknown"

if __name__ == "__main__":
    print("🤔 你说烧录了PCA9685，但测试显示face_control...")
    print("让我们检查所有端口，找到真正的PCA9685!")
    
    # 测试所有端口
    pca9685_port = test_all_ports()
    
    if pca9685_port:
        print(f"\n🎯 更新analysis_sound.py使用正确端口: {pca9685_port}")
        print("修改这行代码:")
        print(f"analyzer = AudioAnalyzer(com_port='{pca9685_port}')")
    else:
        print("\n🔧 建议重新烧录PCA9685代码:")
        print("1. 打开Arduino IDE")
        print("2. 打开文件: c:\\Users\\a's\\Desktop\\newplatform\\new\\arduino_pca9685\\arduino_pca9685.ino")
        print("3. 选择正确的开发板和端口")
        print("4. 重新烧录")
        
        print("\n或者修改Python代码匹配face_control版本:")
        print("CHIN范围改为: (45, 300)")
        print("下巴映射改为: chin_min_angle=45, chin_max_angle=300")
    
    # 详细测试COM7
    print(f"\n📋 详细测试当前使用的COM7:")
    test_specific_port("COM7")
