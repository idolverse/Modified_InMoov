#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import wave
import numpy as np
import serial
import serial.tools.list_ports
import time
import threading
from typing import Optional, Callable

class AudioAnalyzer:
    def __init__(self, com_port="COM7", baud_rate=115200):
        """
        音频分析器，用于分析音频振幅并控制舵机
        """
        self.com_port = com_port
        self.baud_rate = baud_rate
        self.serial_conn = None
        self.is_playing = False
        self.is_connected = False
        
        # 面部部位映射 - 整合arduino_facecontrol功能
        self.face_parts = {
            'LEFT_EYE_V': 'LEFT_EYE_V',
            'LEFT_EYE_H': 'LEFT_EYE_H',
            'RIGHT_EYE_V': 'RIGHT_EYE_V',
            'RIGHT_EYE_H': 'RIGHT_EYE_H',
            'PHILTRUM': 'PHILTRUM',
            'CHIN': 'CHIN',
            'MOUTH': 'PHILTRUM',  # 兼容原有嘴巴控制
            'LEFT_UPPER_EYELID': 'LEFT_UPPER_EYELID',
            'LEFT_LOWER_EYELID': 'LEFT_LOWER_EYELID',
            'RIGHT_UPPER_EYELID': 'RIGHT_UPPER_EYELID',
            'RIGHT_LOWER_EYELID': 'RIGHT_LOWER_EYELID',
            'LEFT_EYEBROW': 'LEFT_EYEBROW',
            'RIGHT_EYEBROW': 'RIGHT_EYEBROW',
            'LEFT_FOREHEAD': 'LEFT_FOREHEAD',
            'RIGHT_FOREHEAD': 'RIGHT_FOREHEAD',
            'LEFT_CHEEK': 'LEFT_CHEEK',
            'RIGHT_CHEEK': 'RIGHT_CHEEK'
        }
        
        # 各部位的角度范围 - 使用robot_head标准
        self.angle_ranges = {
            'LEFT_EYE_V': (30, 150),
            'LEFT_EYE_H': (30, 150),
            'RIGHT_EYE_V': (30, 150),
            'RIGHT_EYE_H': (30, 150),
            'PHILTRUM': (70, 100),    
            'CHIN': (60, 120),        # robot_head标准范围
            'MOUTH': (70, 100),       
            'LEFT_UPPER_EYELID': (45, 100),   
            'LEFT_LOWER_EYELID': (69, 71),    
            'RIGHT_UPPER_EYELID': (30, 100),  
            'RIGHT_LOWER_EYELID': (78, 80),   
            'LEFT_EYEBROW': (60, 100),        
            'RIGHT_EYEBROW': (50, 100),       
            'LEFT_FOREHEAD': (70, 85),        
            'RIGHT_FOREHEAD': (70, 85),       
            'LEFT_CHEEK': (50, 90),           
            'RIGHT_CHEEK': (60, 100)          
        }
        
        # 下巴控制参数 - robot_head标准
        self.chin_min_angle = 60    # 下巴最小角度
        self.chin_max_angle = 120   # 下巴最大角度
        
        # 添加缺失的回调函数属性
        self.connection_callback: Optional[Callable] = None
        self.response_callback: Optional[Callable] = None
        
        # 添加robot_head版本的完整功能
        # 音频播放控制
        self.is_playing_audio = False
        
        # 敏感度设置 - robot_head版本的敏感度系统
        self.current_sensitivity = {
            'threshold_low': 0.005,
            'threshold_high': 0.03,
            'description': "正常敏感度"
        }

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
        if hasattr(self, 'serial_conn') and self.serial_conn and self.serial_conn.is_open:
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
        if not self.is_connected or not self.serial_conn:
            raise Exception("未连接到设备")
        
        self.serial_conn.write((command + '\n').encode())
        self.serial_conn.flush()
    
    def _read_response(self, timeout: float = 1.0) -> str:
        """读取Arduino响应"""
        if not self.is_connected or not self.serial_conn:
            raise Exception("未连接到设备")
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            if self.serial_conn.in_waiting > 0:
                response = self.serial_conn.readline().decode().strip()
                if self.response_callback:
                    self.response_callback(response)
                return response
            time.sleep(0.01)
        
        return ""
    
    def send_angle(self, angle):
        """发送嘴巴角度（兼容原有接口）"""
        return self.set_face_part_angle('PHILTRUM', angle)
    
    def set_face_part_angle(self, part: str, angle: int):
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
            
            command = f"FACE:{part},{angle}"
            self._send_command(command)
            
            threading.Thread(target=self._read_response, daemon=True).start()
            return True
            
        except Exception as e:
            if self.response_callback:
                self.response_callback(f"错误: {str(e)}")
            return False
    
    def set_servo_angle(self, channel: int, angle: int):
        """直接设置舵机角度"""
        if not self.is_connected:
            return False
        
        try:
            angle = max(0, min(180, angle))
            command = f"SERVO:{channel},{angle}"
            self._send_command(command)
            
            threading.Thread(target=self._read_response, daemon=True).start()
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
            threading.Thread(target=self._read_response, daemon=True).start()
            return True
            
        except Exception as e:
            if self.response_callback:
                self.response_callback(f"错误: {str(e)}")
            return False
    
    def get_angle_range(self, part: str) -> tuple:
        """获取指定部位的角度范围"""
        return self.angle_ranges.get(part, (0, 180))
    
    def blink_eyes(self):
        """眨眼动作"""
        if self.is_connected:
            # 闭眼
            self.set_face_part_angle('LEFT_UPPER_EYELID', self.eye_close_angle)
            self.set_face_part_angle('RIGHT_UPPER_EYELID', self.eye_close_angle)
            time.sleep(0.15)
            
            # 睁眼
            self.set_face_part_angle('LEFT_UPPER_EYELID', self.eye_open_angle)
            self.set_face_part_angle('RIGHT_UPPER_EYELID', self.eye_open_angle)
    
    def check_and_blink(self):
        """检查是否需要眨眼"""
        current_time = time.time()
        if current_time - self.last_blink_time >= self.blink_interval:
            self.blink_eyes()
            self.last_blink_time = current_time
            if self.response_callback:
                self.response_callback(f"眨眼 - 时间: {current_time:.2f}s")
    
    def analyze_audio_file(self, wav_file):
        """分析WAV文件的振幅，返回振幅数据和时间点 - robot_head版本"""
        try:
            import wave
            
            with wave.open(wav_file, 'rb') as wav:
                frames = wav.getnframes()
                sample_rate = wav.getframerate()
                channels = wav.getnchannels()
                sample_width = wav.getsampwidth()
                
                if self.response_callback:
                    self.response_callback(f"音频信息: {frames}帧, {sample_rate}Hz, {channels}声道, {sample_width}字节")
                
                audio_data = wav.readframes(frames)
                
                # 转换为numpy数组
                if sample_width == 1:
                    audio_array = np.frombuffer(audio_data, dtype=np.uint8)
                    audio_array = (audio_array - 128) / 128.0
                elif sample_width == 2:
                    audio_array = np.frombuffer(audio_data, dtype=np.int16)
                    audio_array = audio_array / 32768.0
                else:
                    if self.response_callback:
                        self.response_callback("不支持的音频格式")
                    return None
                
                # 如果是双声道，取平均值
                if channels == 2:
                    audio_array = audio_array.reshape(-1, 2).mean(axis=1)
                
                # robot_head版本的高精度分析窗口
                window_size = 128   # 更小的分析窗口，增加细节
                step_size = 64      # 更小的步进，获得更高的时间分辨率
                amplitudes = []
                time_points = []
                
                for i in range(0, len(audio_array), step_size):
                    window = audio_array[i:i + window_size]
                    if len(window) > 0:
                        rms = np.sqrt(np.mean(window ** 2))
                        amplitudes.append(rms)
                        time_points.append(i / sample_rate)
                
                return amplitudes, time_points, sample_rate
                
        except Exception as e:
            if self.response_callback:
                self.response_callback(f"分析音频文件失败: {e}")
            return None

    def amplitude_to_angle(self, amplitude, threshold_low=None, threshold_high=None):
        """将振幅转换为舵机角度 - robot_head版本的精确映射算法"""
        if threshold_low is None:
            threshold_low = self.current_sensitivity['threshold_low']
        if threshold_high is None:
            threshold_high = self.current_sensitivity['threshold_high']
        
        # 使用robot_head标准角度范围：60-120度
        min_angle = 60   # 嘴巴完全闭合
        max_angle = 120  # 嘴巴完全张开
        
        # robot_head版本的振幅处理算法 - 增强敏感度
        if amplitude < 0.001:
            normalized_amp = 0.0
        elif amplitude < threshold_low:
            # 低音量区间：放大到 0.0-0.3
            normalized_amp = (amplitude / threshold_low) * 0.3
        elif amplitude < threshold_high:
            # 中音量区间：映射到 0.3-0.7
            normalized_amp = 0.3 + ((amplitude - threshold_low) / (threshold_high - threshold_low)) * 0.4
        else:
            # 高音量区间：映射到 0.7-1.0，但限制最大值避免过度张嘴
            excess = min(amplitude - threshold_high, threshold_high)
            normalized_amp = 0.7 + (excess / threshold_high) * 0.3
        
        # 应用非线性映射，增强中等音量的变化
        enhanced_amp = np.sqrt(normalized_amp)
        
        # 映射到角度范围
        angle = min_angle + (max_angle - min_angle) * enhanced_amp
        angle = round(angle)
        angle = max(min_angle, min(max_angle, angle))
        
        return angle
    
    def play_audio_with_face_control(self, wav_file, threshold_low=None, threshold_high=None, enable_blink=True):
        """播放音频并同时控制面部动作 - robot_head版本的完整实现（包括嘴部和眨眼）"""
        if not self.is_connected:
            if self.response_callback:
                self.response_callback("错误：未连接到面部控制器")
            return False
        
        # 使用动态阈值或默认值
        if threshold_low is None or threshold_high is None:
            threshold_low = self.current_sensitivity['threshold_low']
            threshold_high = self.current_sensitivity['threshold_high']
            
        # 分析音频
        result = self.analyze_audio_file(wav_file)
        if not result:
            if self.response_callback:
                self.response_callback("音频分析失败")
            return False
        
        amplitudes, time_points, sample_rate = result
        
        if self.response_callback:
            self.response_callback(f"使用阈值: 低={threshold_low:.4f}, 高={threshold_high:.4f}")
            self.response_callback(f"眨眼功能: {'开启' if enable_blink else '关闭'}")
        
        # 标记播放状态
        self.is_playing_audio = True
        
        # 启动音频播放线程
        def play_audio():
            try:
                import pygame
                pygame.mixer.init()
                pygame.mixer.music.load(wav_file)
                pygame.mixer.music.play()
                
                while pygame.mixer.music.get_busy() and self.is_playing_audio:
                    time.sleep(0.01)
                
                pygame.mixer.quit()
            except Exception as e:
                if self.response_callback:
                    self.response_callback(f"播放音频失败: {e}")
        
        # 启动面部控制线程 - robot_head版本的完整面部控制
        def control_face():
            try:
                start_time = time.time()
                amplitude_index = 0
                last_angle = 60  # 初始闭嘴状态
                last_blink_time = start_time
                blink_interval = 2.5 + (time.time() % 3.0)  # 随机眨眼间隔2.5-5.5秒
                
                while amplitude_index < len(amplitudes) and self.is_playing_audio:
                    current_time = time.time() - start_time
                    
                    # 找到当前时间对应的振幅
                    while (amplitude_index < len(time_points) and 
                        current_time > time_points[amplitude_index]):
                        amplitude_index += 1
                    
                    if amplitude_index < len(amplitudes):
                        amplitude = amplitudes[amplitude_index]
                        angle = self.amplitude_to_angle(amplitude, threshold_low, threshold_high)
                        
                        # 控制嘴部动作 - 使用快速命令
                        if int(angle) != int(last_angle):
                            self.set_face_part_fast('CHIN', int(angle))
                            last_angle = angle
                        
                        # robot_head版本的智能眨眼功能
                        if enable_blink and (time.time() - last_blink_time) > blink_interval:
                            # 在说话间隙眨眼（声音较小时）
                            if amplitude < threshold_low * 2:
                                self.trigger_blink()
                                last_blink_time = time.time()
                                blink_interval = 2.0 + (time.time() % 4.0)  # 重新设置随机间隔
                        
                        # 显示实时信息
                        if self.response_callback and amplitude_index % 10 == 0:
                            self.response_callback(f"时间: {current_time:.2f}s, 振幅: {amplitude:.4f}, 嘴部: {angle}°")
                    
                    time.sleep(0.02)  # 50Hz频率
                
                # 播放结束，面部回到中性状态
                self.set_face_part_fast('CHIN', 60)
                if self.response_callback:
                    self.response_callback("播放结束，面部回到中性状态")
            except Exception as e:
                if self.response_callback:
                    self.response_callback(f"控制面部动作失败: {e}")
        
        # 启动线程
        import threading
        audio_thread = threading.Thread(target=play_audio, daemon=True)
        audio_thread.start()
        
        face_thread = threading.Thread(target=control_face, daemon=True)
        face_thread.start()
        
        return {
            "audio_thread": audio_thread,
            "face_thread": face_thread,
            "stop": lambda: setattr(self, 'is_playing_audio', False)
        }

    def trigger_blink(self):
        """触发眨眼动作 - robot_head版本的快速眨眼"""
        try:
            # robot_head版本的固定眨眼角度
            left_upper_open = 60
            left_upper_closed = 100
            right_upper_open = 90
            right_upper_closed = 30
            
            # 确保角度在范围内
            left_upper_min, left_upper_max = self.angle_ranges['LEFT_UPPER_EYELID']
            right_upper_min, right_upper_max = self.angle_ranges['RIGHT_UPPER_EYELID']
            
            left_upper_open = max(left_upper_min, min(left_upper_max, left_upper_open))
            left_upper_closed = max(left_upper_min, min(left_upper_max, left_upper_closed))
            right_upper_open = max(right_upper_min, min(right_upper_max, right_upper_open))
            right_upper_closed = max(right_upper_min, min(right_upper_max, right_upper_closed))
            
            # 快速闭眼
            self.set_face_part_fast('LEFT_UPPER_EYELID', left_upper_closed)
            self.set_face_part_fast('RIGHT_UPPER_EYELID', right_upper_closed)
            
            # 启动线程进行眨眼动作，不阻塞主控制
            def blink_action():
                time.sleep(0.15)  # 保持闭眼状态
                # 快速睁眼
                self.set_face_part_fast('LEFT_UPPER_EYELID', left_upper_open)
                self.set_face_part_fast('RIGHT_UPPER_EYELID', right_upper_open)
            
            import threading
            blink_thread = threading.Thread(target=blink_action, daemon=True)
            blink_thread.start()
            
        except Exception as e:
            if self.response_callback:
                self.response_callback(f"眨眼失败: {e}")

    def set_face_part_fast(self, part: str, angle: int):
        """快速设置面部部位角度 - robot_head版本的FAST命令"""
        if not self.is_connected:
            return False
        
        if part not in self.face_parts:
            return False
        
        try:
            # 限制角度范围
            if part in self.angle_ranges:
                min_angle, max_angle = self.angle_ranges[part]
                angle = max(min_angle, min(max_angle, angle))
            
            command = f"FAST:{part},{angle}"
            self._send_command(command)
            return True
            
        except Exception as e:
            if self.response_callback:
                self.response_callback(f"错误: {str(e)}")
            return False

    def set_mouth_fast(self, philtrum_angle: int, chin_angle: int):
        """快速设置嘴部角度 - robot_head版本的MOUTH命令"""
        if not self.is_connected:
            return False
        
        try:
            # 限制角度范围
            philtrum_min, philtrum_max = self.angle_ranges['PHILTRUM']
            chin_min, chin_max = self.angle_ranges['CHIN']
            
            philtrum_angle = max(philtrum_min, min(philtrum_max, philtrum_angle))
            chin_angle = max(chin_min, min(chin_max, chin_angle))
            
            command = f"MOUTH:{philtrum_angle},{chin_angle}"
            self._send_command(command)
            return True
            
        except Exception as e:
            if self.response_callback:
                self.response_callback(f"错误: {str(e)}")
            return False

    def test_face_animation(self):
        """测试面部动画 - robot_head版本的边说话边眨眼"""
        if not self.is_connected:
            return False
        
        print("开始测试面部动画...")
        
        # 模拟说话过程中的动作
        import threading
        import random
        
        def simulate_speech():
            try:
                # 模拟5秒的说话
                start_time = time.time()
                last_blink = start_time
                
                while time.time() - start_time < 5:
                    current_time = time.time()
                    
                    # 模拟嘴部动作
                    amplitude = random.uniform(0.002, 0.025)
                    angle = self.amplitude_to_angle(amplitude)
                    self.set_face_part_fast('CHIN', angle)
                    
                    # 随机眨眼
                    if current_time - last_blink > random.uniform(1.5, 3.0):
                        self.trigger_blink()
                        last_blink = current_time
                        print(f"眨眼 - 时间: {current_time - start_time:.1f}s")
                    
                    # 显示当前状态
                    if int((current_time - start_time) * 2) % 4 == 0:
                        print(f"说话模拟 - 时间: {current_time - start_time:.1f}s, 嘴部: {angle}°")
                    
                    time.sleep(0.05)  # 20Hz更新
                
                # 结束，回到中性状态
                self.set_face_part_fast('CHIN', 60)
                print("面部动画测试完成")
                
            except Exception as e:
                print(f"面部动画测试失败: {e}")
        
        # 启动测试线程
        test_thread = threading.Thread(target=simulate_speech, daemon=True)
        test_thread.start()
        
        return True

    def set_mouth_sensitivity(self, sensitivity_level: str = "normal"):
        """设置嘴部动作敏感度 - robot_head版本的敏感度系统"""
        sensitivity_settings = {
            "low": {
                "threshold_low": 0.01,
                "threshold_high": 0.05,
                "description": "低敏感度 - 需要较大音量才有明显动作"
            },
            "normal": {
                "threshold_low": 0.005,
                "threshold_high": 0.03,
                "description": "正常敏感度 - 平衡的响应"
            },
            "high": {
                "threshold_low": 0.002,
                "threshold_high": 0.02,
                "description": "高敏感度 - 对轻微声音也有响应"
            },
            "ultra": {
                "threshold_low": 0.001,
                "threshold_high": 0.015,
                "description": "超高敏感度 - 对极小声音都有反应"
            }
        }
        
        if sensitivity_level in sensitivity_settings:
            self.current_sensitivity = sensitivity_settings[sensitivity_level]
            if self.response_callback:
                self.response_callback(f"已设置: {self.current_sensitivity['description']}")
            return True
        else:
            if self.response_callback:
                self.response_callback(f"无效的敏感度级别。可选: {list(sensitivity_settings.keys())}")
            return False

    def test_fast_mouth_control(self):
        """测试快速嘴部控制 - robot_head版本"""
        if not self.is_connected:
            if self.response_callback:
                self.response_callback("错误：未连接到面部控制器")
            return False
        
        if self.response_callback:
            self.response_callback("开始测试快速嘴部控制...")
        
        try:
            # 快速张嘴闭嘴测试
            for i in range(3):
                # 张嘴
                self.set_face_part_fast('CHIN', 120)
                time.sleep(0.3)
                
                # 闭嘴
                self.set_face_part_fast('CHIN', 60)
                time.sleep(0.3)
            
            # 测试MOUTH命令（同时控制人中和下巴）
            self.set_mouth_fast(85, 90)
            time.sleep(0.5)
            
            # 回到中性位置
            self.set_mouth_fast(85, 90)
            
            if self.response_callback:
                self.response_callback("快速嘴部控制测试完成")
            return True
            
        except Exception as e:
            if self.response_callback:
                self.response_callback(f"测试失败: {str(e)}")
            return False

    def test_dynamic_mouth_movement(self):
        """测试动态嘴部运动 - robot_head版本"""
        if not self.is_connected:
            if self.response_callback:
                self.response_callback("错误：未连接到面部控制器")
            return False
        
        if self.response_callback:
            self.response_callback("开始测试动态嘴部运动...")
        
        try:
            # 模拟不同强度的语音
            speech_pattern = [
                (0.002, "轻声"),    # 轻声 -> 约62-65度
                (0.008, "正常"),    # 正常音量 -> 约75-85度  
                (0.02, "大声"),     # 大声 -> 约95-105度
                (0.04, "很大声"),   # 很大声 -> 约110-115度
                (0.08, "最大声"),   # 最大声 -> 约118-120度
                (0.001, "静音"),    # 静音 -> 60度
            ]
            
            for amplitude, description in speech_pattern:
                angle = self.amplitude_to_angle(amplitude)
                self.set_face_part_fast('CHIN', angle)
                
                if self.response_callback:
                    self.response_callback(f"{description}(振幅:{amplitude:.3f}) -> {angle}°")
                
                time.sleep(0.8)  # 每个状态持续0.8秒
            
            # 最后回到闭嘴状态
            self.set_face_part_fast('CHIN', 60)
            
            if self.response_callback:
                self.response_callback("动态嘴部运动测试完成")
            return True
            
        except Exception as e:
            if self.response_callback:
                self.response_callback(f"测试失败: {str(e)}")
            return False

    def get_dynamic_thresholds(self):
        """获取当前动态阈值设置 - robot_head版本"""
        if hasattr(self, 'current_sensitivity'):
            return self.current_sensitivity['threshold_low'], self.current_sensitivity['threshold_high']
        else:
            return 0.005, 0.03

    def stop_audio_playback(self):
        """停止音频播放和嘴部动作 - robot_head版本"""
        self.is_playing_audio = False
        time.sleep(0.1)
        self.set_face_part_fast('CHIN', 60)
        if self.response_callback:
            self.response_callback("已停止音频播放")

def main():
    # 创建分析器实例
    analyzer = AudioAnalyzer(com_port="COM7")
    
    while True:
        print("\n=== 音频振幅分析器 (robot_head完整版) ===")
        print("1. 测试舵机")
        print("2. 分析并播放音频 (标准)")
        print("3. 分析并播放音频 (带面部控制)")
        print("4. 设置参数")
        print("5. 设置敏感度")
        print("6. 测试快速嘴部控制")
        print("7. 测试动态嘴部运动")
        print("8. 测试面部动画")
        print("9. 启动GUI界面")
        print("10. 退出")
        
        choice = input("请选择功能: ").strip()
        
        if choice == "1":
            analyzer.test_servo()
        
        elif choice == "2":
            wav_file = input("请输入WAV文件路径: ").strip()
            if wav_file and wav_file.endswith('.wav'):
                analyzer.play_with_mouth_control(wav_file)
            else:
                print("请输入有效的WAV文件路径")
        
        elif choice == "3":
            wav_file = input("请输入WAV文件路径: ").strip()
            if wav_file and wav_file.endswith('.wav'):
                enable_blink = input("是否启用眨眼? (y/n): ").strip().lower() in ['y', 'yes', '是']
                if analyzer.connect_arduino():
                    analyzer.play_audio_with_face_control(wav_file, enable_blink=enable_blink)
                    analyzer.disconnect_arduino()
            else:
                print("请输入有效的WAV文件路径")
        
        elif choice == "5":
            print("可选敏感度级别: low, normal, high, ultra")
            level = input("请输入敏感度级别: ").strip()
            if level:
                analyzer.set_mouth_sensitivity(level)
        
        elif choice == "6":
            if analyzer.connect_arduino():
                analyzer.test_fast_mouth_control()
                analyzer.disconnect_arduino()
        
        elif choice == "7":
            if analyzer.connect_arduino():
                analyzer.test_dynamic_mouth_movement()
                analyzer.disconnect_arduino()
        
        elif choice == "8":
            if analyzer.connect_arduino():
                analyzer.test_face_animation()
                analyzer.disconnect_arduino()
        
        elif choice == "10":
            print("退出程序")
            break
        
        else:
            print("无效选择")

if __name__ == "__main__":
    main()
