import serial
import serial.tools.list_ports
import time
import threading
from typing import Optional, Callable

class FaceController:
    def __init__(self, com_port="COM7", baud_rate=115200):
        # 保持兼容性：构造函数接受参数
        self.com_port = com_port
        self.baud_rate = baud_rate
        self.serial_conn: Optional[serial.Serial] = None
        self.is_connected = False
        self.port = None
        
        # 面部部位映射
        self.face_parts = {
            'LEFT_EYEBROW': 'LEFT_EYEBROW',
            'RIGHT_EYEBROW': 'RIGHT_EYEBROW',
            'LEFT_CHEEK': 'LEFT_CHEEK',
            'RIGHT_CHEEK': 'RIGHT_CHEEK',
            'LEFT_UPPER_EYELID': 'LEFT_UPPER_EYELID',
            'LEFT_LOWER_EYELID': 'LEFT_LOWER_EYELID',
            'RIGHT_UPPER_EYELID': 'RIGHT_UPPER_EYELID',
            'RIGHT_LOWER_EYELID': 'RIGHT_LOWER_EYELID',
            'LEFT_FOREHEAD': 'LEFT_FOREHEAD',
            'RIGHT_FOREHEAD': 'RIGHT_FOREHEAD',
            'LEFT_EYE_V': 'LEFT_EYE_V',
            'LEFT_EYE_H': 'LEFT_EYE_H',
            'RIGHT_EYE_V': 'RIGHT_EYE_V',
            'RIGHT_EYE_H': 'RIGHT_EYE_H',
            'PHILTRUM': 'PHILTRUM',
            'CHIN': 'CHIN',
            'MOUTH': 'PHILTRUM'  # 兼容原有嘴巴控制
        }
        
        # PCA9685 16通道舵机映射
        self.servo_channels = {
            'LEFT_EYE_V': 0,           # 左眼球上下
            'LEFT_EYE_H': 1,           # 左眼球左右  
            'RIGHT_EYE_V': 2,          # 右眼球上下
            'RIGHT_EYE_H': 3,          # 右眼球左右
            'PHILTRUM': 4,             # 人中
            'CHIN': 5,                 # 下巴
            'LEFT_UPPER_EYELID': 6,    # 左上眼皮
            'LEFT_LOWER_EYELID': 7,    # 左下眼皮
            'RIGHT_UPPER_EYELID': 8,   # 右上眼皮
            'RIGHT_LOWER_EYELID': 9,   # 右下眼皮
            'LEFT_EYEBROW': 10,        # 左眉毛
            'RIGHT_EYEBROW': 11,       # 右眉毛
            'LEFT_FOREHEAD': 12,       # 左前额
            'RIGHT_FOREHEAD': 13,      # 右前额
            'LEFT_CHEEK': 14,          # 左脸颊
            'RIGHT_CHEEK': 15,         # 右脸颊
            'MOUTH': 4                 # 兼容：嘴巴映射到人中
        }
        
        # PCA9685精确角度范围 - 已经是robot_head标准
        self.angle_ranges = {
            'LEFT_EYE_V': (30, 150),
            'LEFT_EYE_H': (30, 150),
            'RIGHT_EYE_V': (30, 150),
            'RIGHT_EYE_H': (30, 150),
            'PHILTRUM': (70, 100),
            'CHIN': (60, 120),      # 已经是正确的robot_head标准
            'MOUTH': (70, 100),     # 改为与PHILTRUM一致
            'LEFT_UPPER_EYELID': (45, 100),
            'LEFT_LOWER_EYELID': (69, 71),  # 改为与face_control.ino一致
            'RIGHT_UPPER_EYELID': (30, 100),
            'RIGHT_LOWER_EYELID': (78, 80),  # 改为与face_control.ino一致
            'LEFT_EYEBROW': (60, 100),
            'RIGHT_EYEBROW': (50, 100),
            'LEFT_FOREHEAD': (70, 85),
            'RIGHT_FOREHEAD': (70, 85),
            'LEFT_CHEEK': (50, 90),
            'RIGHT_CHEEK': (60, 100)
        }
        
        # 反向设置功能
        self.reverse_settings = {
            'LEFT_EYE_V': False,
            'LEFT_EYE_H': False,
            'RIGHT_EYE_V': False,
            'RIGHT_EYE_H': False,
            'PHILTRUM': False,
            'CHIN': False,
            'MOUTH': False,
            'LEFT_UPPER_EYELID': False,
            'LEFT_LOWER_EYELID': False,
            'RIGHT_UPPER_EYELID': False,
            'RIGHT_LOWER_EYELID': False,
            'LEFT_EYEBROW': False,
            'RIGHT_EYEBROW': False,
            'LEFT_FOREHEAD': False,
            'RIGHT_FOREHEAD': False,
            'LEFT_CHEEK': False,
            'RIGHT_CHEEK': False
        }
        
        # 眨眼参数（保持兼容）
        self.eye_open_angle = 135
        self.eye_close_angle = 45
        self.blink_interval = 4.0
        self.last_blink_time = 0
        
        # 状态回调函数
        self.connection_callback: Optional[Callable] = None
        self.response_callback: Optional[Callable] = None
    
    def set_connection_callback(self, callback: Callable):
        """设置连接状态回调"""
        self.connection_callback = callback
    
    def set_response_callback(self, callback: Callable):
        """设置响应回调"""
        self.response_callback = callback
    
    def get_available_ports(self):
        """获取可用串口列表"""
        ports = []
        for port in serial.tools.list_ports.comports():
            ports.append(port.device)
        return ports
    
    def connect(self, port: str) -> bool:
        """连接到指定串口（兼容旧接口）"""
        self.com_port = port
        return self.connect_arduino()
    
    def connect_arduino(self) -> bool:
        """连接到Arduino"""
        try:
            if hasattr(self, 'serial_conn') and self.serial_conn and self.serial_conn.is_open:
                self.serial_conn.close()
                time.sleep(0.5)
            
            if self.response_callback:
                self.response_callback(f"正在连接到 {self.com_port}...")
            
            self.serial_conn = serial.Serial(
                port=self.com_port,
                baudrate=self.baud_rate,
                timeout=2,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                bytesize=serial.EIGHTBITS
            )
            
            if self.response_callback:
                self.response_callback("串口已打开，等待Arduino初始化...")
            
            # 等待Arduino初始化
            time.sleep(3)
            
            # 清空缓冲区
            self.serial_conn.flushInput()
            self.serial_conn.flushOutput()
            
            if self.response_callback:
                self.response_callback("正在读取Arduino启动消息...")
            
            # 读取Arduino启动消息
            startup_messages = []
            start_time = time.time()
            while time.time() - start_time < 3:
                if self.serial_conn.in_waiting > 0:
                    try:
                        line = self.serial_conn.readline().decode().strip()
                        if line:
                            startup_messages.append(line)
                            if self.response_callback:
                                self.response_callback(f"Arduino: {line}")
                    except Exception as read_error:
                        if self.response_callback:
                            self.response_callback(f"读取消息错误: {read_error}")
                time.sleep(0.1)
            
            # 检查启动消息
            arduino_ready = False
            if startup_messages:
                if self.response_callback:
                    self.response_callback(f"收到 {len(startup_messages)} 条启动消息")
                
                # 检查是否有预期的启动消息
                for msg in startup_messages:
                    if "Face Control System" in msg or "Ready" in msg:
                        arduino_ready = True
                        break
                
                if not arduino_ready:
                    if self.response_callback:
                        self.response_callback("警告: 未收到预期的启动消息，但Arduino有响应")
                    arduino_ready = True  # 有响应就认为可能连接成功
            else:
                if self.response_callback:
                    self.response_callback("警告: 未收到Arduino启动消息")
            
            # 测试连接
            if self.response_callback:
                self.response_callback("正在测试Arduino响应...")
            
            connection_test_passed = self._test_connection()
            
            if arduino_ready or connection_test_passed:
                self.is_connected = True
                if self.connection_callback:
                    self.connection_callback(True, f"已连接到 {self.com_port}")
                if self.response_callback:
                    self.response_callback("✅ Arduino连接成功！")
                return True
            else:
                self.disconnect_arduino()
                if self.connection_callback:
                    self.connection_callback(False, "Arduino连接测试失败")
                if self.response_callback:
                    self.response_callback("❌ Arduino连接失败: 设备无响应")
                return False
                
        except serial.SerialException as e:
            self.is_connected = False
            error_msg = f"串口错误: {str(e)}"
            if "could not open port" in str(e).lower():
                error_msg += " (串口可能被其他程序占用)"
            elif "access is denied" in str(e).lower():
                error_msg += " (权限不足或串口被占用)"
            
            if self.connection_callback:
                self.connection_callback(False, error_msg)
            if self.response_callback:
                self.response_callback(f"❌ {error_msg}")
            return False
            
        except Exception as e:
            self.is_connected = False
            error_msg = f"连接异常: {str(e)}"
            if self.connection_callback:
                self.connection_callback(False, error_msg)
            if self.response_callback:
                self.response_callback(f"❌ {error_msg}")
            return False

    def disconnect_arduino(self):
        """断开Arduino连接"""
        if self.serial_conn and self.serial_conn.is_open:
            self.serial_conn.close()
        self.is_connected = False
        if self.connection_callback:
            self.connection_callback(False, "已断开连接")
    
    def _test_connection(self) -> bool:
        """测试连接是否正常"""
        try:
            if not hasattr(self, 'serial_conn') or not self.serial_conn or not self.serial_conn.is_open:
                if self.response_callback:
                    self.response_callback("串口未正确打开")
                return False
            
            if self.response_callback:
                self.response_callback("发送测试命令: PING")
            
            # 清空缓冲区
            self.serial_conn.flushInput()
            self.serial_conn.flushOutput()
            
            # 发送PING命令测试
            try:
                self.serial_conn.write(b"PING\n")
                self.serial_conn.flush()
            except Exception as send_error:
                if self.response_callback:
                    self.response_callback(f"发送PING失败: {send_error}")
                return False
            
            # 等待响应
            ping_response = ""
            start_time = time.time()
            while time.time() - start_time < 3.0:
                if self.serial_conn.in_waiting > 0:
                    try:
                        line = self.serial_conn.readline().decode().strip()
                        if line:
                            ping_response = line
                            if self.response_callback:
                                self.response_callback(f"收到响应: {line}")
                            
                            if "PONG" in line:
                                return True
                    except:
                        break
                time.sleep(0.01)
            
            # 如果PING失败，尝试CENTER
            if self.response_callback:
                self.response_callback("PING无响应，尝试CENTER命令")
            
            try:
                self.serial_conn.write(b"CENTER\n")
                self.serial_conn.flush()
                
                center_response = ""
                start_time = time.time()
                while time.time() - start_time < 3.0:
                    if self.serial_conn.in_waiting > 0:
                        try:
                            line = self.serial_conn.readline().decode().strip()
                            if line:
                                center_response = line
                                if self.response_callback:
                                    self.response_callback(f"CENTER响应: {line}")
                                
                                if "OK" in line:
                                    return True
                        except:
                            break
                    time.sleep(0.01)
                
                # 如果有任何响应，认为连接可能成功
                if ping_response or center_response:
                    if self.response_callback:
                        self.response_callback("Arduino有响应，连接可能成功")
                    return True
                    
            except Exception as center_error:
                if self.response_callback:
                    self.response_callback(f"CENTER命令失败: {center_error}")
            
            if self.response_callback:
                self.response_callback("两次测试都无响应")
            return False
            
        except Exception as e:
            if self.response_callback:
                self.response_callback(f"连接测试异常: {str(e)}")
            return False
    
    def _send_command(self, command: str):
        """发送命令到Arduino"""
        # 修复：直接检查串口状态，不依赖is_connected
        if not hasattr(self, 'serial_conn') or not self.serial_conn or not self.serial_conn.is_open:
            raise Exception("串口未打开")
        
        self.serial_conn.write((command + '\n').encode())
        self.serial_conn.flush()
    
    def _read_response(self, timeout: float = 1.0) -> str:
        """读取Arduino响应"""
        # 修复：直接检查串口状态，不依赖is_connected
        if not hasattr(self, 'serial_conn') or not self.serial_conn or not self.serial_conn.is_open:
            raise Exception("串口未打开")
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            if self.serial_conn.in_waiting > 0:
                response = self.serial_conn.readline().decode().strip()
                if self.response_callback:
                    self.response_callback(response)
                return response
            time.sleep(0.01)
        
        return ""
    
    def set_face_part_angle(self, part: str, angle: int, delay_ms: int = 0):  # 默认延时改为0
        """设置面部部位角度"""
        if not self.is_connected:
            return False
        
        if part not in self.face_parts:
            return False
        
        try:
            # 限制角度范围
            if part in self.angle_ranges:
                min_angle, max_angle = self.angle_ranges[part]
                angle = max(min_angle, min(max_angle, angle))
            
            # 应用反向设置
            final_angle = self._apply_reverse(part, angle)
            
            command = f"FACE:{part},{final_angle}"
            self._send_command(command)
            
            # 只在需要时添加延时
            if delay_ms > 0:
                time.sleep(delay_ms / 1000.0)
            
            return True
            
        except Exception as e:
            if self.response_callback:
                self.response_callback(f"错误: {str(e)}")
            return False
    
    def set_servo_angle(self, channel: int, angle: int, delay_ms: int = 0):  # 默认延时改为0
        """直接设置舵机角度"""
        if not self.is_connected:
            return False
        
        try:
            angle = max(0, min(180, angle))
            command = f"SERVO:{channel},{angle}"
            self._send_command(command)
            
            # 只在需要时添加延时
            if delay_ms > 0:
                time.sleep(delay_ms / 1000.0)
            
            return True
            
        except Exception as e:
            if self.response_callback:
                self.response_callback(f"错误: {str(e)}")
            return False

    def center_all_servos(self):
        """所有舵机回到中位"""
        if not self.is_connected:
            return False
        
        try:
            self._send_command("CENTER")
            # 移除线程化的响应读取
            return True
            
        except Exception as e:
            if self.response_callback:
                self.response_callback(f"错误: {str(e)}")
            return False

    def _apply_smooth_expression(self, angles_dict, delay_between_commands=20):  # 减少延时
        """平滑应用表情，避免卡顿"""
        # 按组分批发送命令，减少同时发送的数量
        groups = [
            ['LEFT_EYE_V', 'RIGHT_EYE_V'],  # 眼球垂直
            ['LEFT_EYE_H', 'RIGHT_EYE_H'],  # 眼球水平
            ['LEFT_EYEBROW', 'RIGHT_EYEBROW'],  # 眉毛
            ['LEFT_UPPER_EYELID', 'RIGHT_UPPER_EYELID'],  # 上眼皮
            ['LEFT_LOWER_EYELID', 'RIGHT_LOWER_EYELID'],  # 下眼皮
            ['LEFT_FOREHEAD', 'RIGHT_FOREHEAD'],  # 前额
            ['LEFT_CHEEK', 'RIGHT_CHEEK'],  # 脸颊
            ['PHILTRUM', 'CHIN']  # 嘴部
        ]
        
        for group in groups:
            for part in group:
                if part in angles_dict:
                    self.set_face_part_angle(part, angles_dict[part], delay_ms=0)  # 无延时
            # 每组之间稍微等待
            time.sleep(delay_between_commands / 1000.0)
    
    def blink_eyes(self):
        """眨眼动作（兼容接口）"""
        if self.is_connected:
            # 闭眼
            self.set_face_part_angle('LEFT_UPPER_EYELID', self.eye_close_angle)
            self.set_face_part_angle('RIGHT_UPPER_EYELID', self.eye_close_angle)
            time.sleep(0.15)
            
            # 睁眼
            self.set_face_part_angle('LEFT_UPPER_EYELID', self.eye_open_angle)
            self.set_face_part_angle('RIGHT_UPPER_EYELID', self.eye_open_angle)
    
    def check_and_blink(self):
        """检查是否需要眨眼（兼容接口）"""
        current_time = time.time()
        if current_time - self.last_blink_time >= self.blink_interval:
            self.blink_eyes()
            self.last_blink_time = current_time
            if self.response_callback:
                self.response_callback(f"眨眼 - 时间: {current_time:.2f}s")
    
    # =====================================================
    # 新增功能：预设表情控制
    # =====================================================
    
    def apply_expression(self, expression_name: str):
        """应用预设表情"""
        if not self.is_connected:
            return False
        
        expressions = {
            'blink': self._expression_blink,
            'frown': self._expression_frown,
            'smile': self._expression_smile,
            'neutral': self._expression_neutral
        }
        
        if expression_name in expressions:
            try:
                expressions[expression_name]()
                if self.response_callback:
                    self.response_callback(f"应用表情: {expression_name}")
                return True
            except Exception as e:
                if self.response_callback:
                    self.response_callback(f"表情应用失败: {str(e)}")
                return False
        else:
            if self.response_callback:
                self.response_callback(f"未知表情: {expression_name}")
            return False

    def _expression_blink(self):
        """眨眼表情 - robot_head版本"""
        # 使用固定的角度值
        left_upper_open = 60
        left_upper_closed = 100
        right_upper_open = 90
        right_upper_closed = 30
        
        # 确保角度在舵机范围内
        left_upper_min, left_upper_max = self.angle_ranges['LEFT_UPPER_EYELID']
        right_upper_min, right_upper_max = self.angle_ranges['RIGHT_UPPER_EYELID']
        
        left_upper_open = max(left_upper_min, min(left_upper_max, left_upper_open))
        left_upper_closed = max(left_upper_min, min(left_upper_max, left_upper_closed))
        right_upper_open = max(right_upper_min, min(right_upper_max, right_upper_open))
        right_upper_closed = max(right_upper_min, min(right_upper_max, right_upper_closed))
        
        # 获取下眼皮的中值（保持不动）
        left_lower_min, left_lower_max = self.angle_ranges['LEFT_LOWER_EYELID']
        right_lower_min, right_lower_max = self.angle_ranges['RIGHT_LOWER_EYELID']
        left_lower_fixed = (left_lower_min + left_lower_max) // 2
        right_lower_fixed = (right_lower_min + right_lower_max) // 2
        
        # 首先确保下眼皮固定
        self.set_face_part_angle('LEFT_LOWER_EYELID', left_lower_fixed, delay_ms=0)
        self.set_face_part_angle('RIGHT_LOWER_EYELID', right_lower_fixed, delay_ms=0)
        
        # 眨眼动作
        # 快速闭眼
        self.set_face_part_angle('LEFT_UPPER_EYELID', left_upper_closed, delay_ms=0)
        self.set_face_part_angle('RIGHT_UPPER_EYELID', right_upper_closed, delay_ms=0)
        time.sleep(0.15)  # 保持闭眼状态
        
        # 快速睁眼
        self.set_face_part_angle('LEFT_UPPER_EYELID', left_upper_open, delay_ms=0)
        self.set_face_part_angle('RIGHT_UPPER_EYELID', right_upper_open, delay_ms=0)

    def _expression_smile(self):
        """笑脸表情 - 脸颊上移并眨眼"""
        # 获取脸颊的角度范围
        left_cheek_min, left_cheek_max = self.angle_ranges['LEFT_CHEEK']
        right_cheek_min, right_cheek_max = self.angle_ranges['RIGHT_CHEEK']
        
        # 脸颊上移
        self.set_face_part_angle('LEFT_CHEEK', left_cheek_max - 5, delay_ms=0)
        self.set_face_part_angle('RIGHT_CHEEK', right_cheek_max - 5, delay_ms=0)
        
        time.sleep(0.3)
        
        # 眨眼
        self._expression_blink()
        
        time.sleep(0.5)
        
        # 脸颊回到中性位置
        center_left_cheek = (left_cheek_min + left_cheek_max) // 2
        center_right_cheek = (right_cheek_min + right_cheek_max) // 2
        
        self.set_face_part_angle('LEFT_CHEEK', center_left_cheek, delay_ms=0)
        self.set_face_part_angle('RIGHT_CHEEK', center_right_cheek, delay_ms=0)

    def _expression_frown(self):
        """皱眉表情"""
        # 获取眉毛的角度范围
        left_eyebrow_min, left_eyebrow_max = self.angle_ranges['LEFT_EYEBROW']
        right_eyebrow_min, right_eyebrow_max = self.angle_ranges['RIGHT_EYEBROW']
        
        # 眉毛上挑
        self.set_face_part_angle('LEFT_EYEBROW', left_eyebrow_min + 5, delay_ms=0)
        self.set_face_part_angle('RIGHT_EYEBROW', right_eyebrow_min + 5, delay_ms=0)
        time.sleep(0.5)
        
        # 恢复中性位置
        center_left = (left_eyebrow_min + left_eyebrow_max) // 2
        center_right = (right_eyebrow_min + right_eyebrow_max) // 2
        
        self.set_face_part_angle('LEFT_EYEBROW', center_left, delay_ms=0)
        self.set_face_part_angle('RIGHT_EYEBROW', center_right, delay_ms=0)

    def _expression_neutral(self):
        """中性表情（回到中位）"""
        for part in self.face_parts.keys():
            if part == 'MOUTH':  # 跳过兼容性映射
                continue
            min_angle, max_angle = self.angle_ranges.get(part, (0, 180))
            center_angle = (min_angle + max_angle) // 2
            self.set_face_part_angle(part, center_angle, delay_ms=0)
    
    def __del__(self):
        """析构函数"""
        if hasattr(self, 'serial_conn') and self.serial_conn and self.serial_conn.is_open:
            self.serial_conn.close()

    def get_servo_channel(self, part: str) -> int:
        """获取面部部位对应的舵机通道"""
        return self.servo_channels.get(part, -1)
    
    def get_all_servo_channels(self):
        """获取所有舵机通道映射"""
        return self.servo_channels
    
    def set_multiple_servos(self, servo_angles: dict, delay_ms: int = 50):
        """批量设置多个舵机角度
        
        Args:
            servo_angles: {part_name: angle} 或 {channel: angle}
            delay_ms: 每个命令间的延时
        """
        if not self.is_connected:
            return False
        
        try:
            for key, angle in servo_angles.items():
                if isinstance(key, str):
                    # 面部部位名称
                    self.set_face_part_angle(key, angle, delay_ms)
                elif isinstance(key, int):
                    # 直接通道号
                    self.set_servo_angle(key, angle, delay_ms)
            return True
        except Exception as e:
            if self.response_callback:
                self.response_callback(f"批量设置错误: {str(e)}")
            return False
