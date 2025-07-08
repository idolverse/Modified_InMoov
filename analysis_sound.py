#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import wave
import numpy as np
import serial
import time
import threading

class AudioAnalyzer:
    def __init__(self, com_port="COM7", baud_rate=9600):
        """
        音频分析器，用于分析音频振幅并控制舵机
        
        Args:
            com_port: Arduino串口号
            baud_rate: 串口波特率
        """
        self.com_port = com_port
        self.baud_rate = baud_rate
        self.serial_conn = None
        self.is_playing = False
        
        # 舵机角度配置
        self.min_angle = 0      # 嘴巴闭合角度
        self.max_angle = 90     # 嘴巴张开最大角度
        
        # 音频分析参数
        self.window_size = 512  # 分析窗口大小
        self.threshold_low = 0.1    # 低振幅阈值
        self.threshold_high = 0.3   # 高振幅阈值
        
    def connect_arduino(self):
        """连接Arduino"""
        try:
            self.serial_conn = serial.Serial(self.com_port, self.baud_rate, timeout=1)
            time.sleep(2)  # 等待Arduino初始化
            print(f"已连接到Arduino: {self.com_port}")
            return True
        except Exception as e:
            print(f"连接Arduino失败: {e}")
            return False
    
    def disconnect_arduino(self):
        """断开Arduino连接"""
        if self.serial_conn:
            self.serial_conn.close()
            self.serial_conn = None
            print("已断开Arduino连接")
    
    def send_angle(self, angle):
        """发送角度到Arduino"""
        if self.serial_conn:
            try:
                # 限制角度范围
                angle = max(self.min_angle, min(self.max_angle, angle))
                command = f"{int(angle)}\n"
                self.serial_conn.write(command.encode())
                return True
            except Exception as e:
                print(f"发送角度失败: {e}")
                return False
        return False
    
    def analyze_audio_file(self, wav_file):
        """分析WAV文件的振幅"""
        try:
            with wave.open(wav_file, 'rb') as wav:
                # 获取音频参数
                frames = wav.getnframes()
                sample_rate = wav.getframerate()
                channels = wav.getnchannels()
                sample_width = wav.getsampwidth()
                
                print(f"音频信息: {frames}帧, {sample_rate}Hz, {channels}声道, {sample_width}字节")
                
                # 读取音频数据
                audio_data = wav.readframes(frames)
                
                # 转换为numpy数组
                if sample_width == 1:
                    audio_array = np.frombuffer(audio_data, dtype=np.uint8)
                    audio_array = (audio_array - 128) / 128.0
                elif sample_width == 2:
                    audio_array = np.frombuffer(audio_data, dtype=np.int16)
                    audio_array = audio_array / 32768.0
                else:
                    print("不支持的音频格式")
                    return None
                
                # 如果是双声道，取平均值
                if channels == 2:
                    audio_array = audio_array.reshape(-1, 2).mean(axis=1)
                
                # 计算每个窗口的振幅
                amplitudes = []
                time_points = []
                
                for i in range(0, len(audio_array), self.window_size):
                    window = audio_array[i:i + self.window_size]
                    if len(window) > 0:
                        # 计算RMS振幅
                        rms = np.sqrt(np.mean(window ** 2))
                        amplitudes.append(rms)
                        # 计算时间点（秒）
                        time_points.append(i / sample_rate)
                
                return amplitudes, time_points, sample_rate
                
        except Exception as e:
            print(f"分析音频文件失败: {e}")
            return None
    
    def amplitude_to_angle(self, amplitude):
        """将振幅转换为舵机角度"""
        if amplitude < self.threshold_low:
            # 低振幅 - 嘴巴闭合
            return self.min_angle
        elif amplitude > self.threshold_high:
            # 高振幅 - 嘴巴张开最大
            return self.max_angle
        else:
            # 中等振幅 - 线性映射
            ratio = (amplitude - self.threshold_low) / (self.threshold_high - self.threshold_low)
            angle = self.min_angle + ratio * (self.max_angle - self.min_angle)
            return angle
    
    def play_with_mouth_control(self, wav_file):
        """播放音频并同时控制嘴部动作"""
        # 分析音频
        result = self.analyze_audio_file(wav_file)
        if not result:
            print("音频分析失败")
            return False
        
        amplitudes, time_points, sample_rate = result
        
        # 连接Arduino
        if not self.connect_arduino():
            print("Arduino连接失败，只播放音频")
            return False
        
        print("开始播放并控制嘴部动作...")
        
        # 启动音频播放线程
        def play_audio():
            import pygame
            pygame.mixer.init()
            pygame.mixer.music.load(wav_file)
            pygame.mixer.music.play()
            
            while pygame.mixer.music.get_busy() and self.is_playing:
                time.sleep(0.01)
            
            pygame.mixer.quit()
        
        # 启动舵机控制线程
        def control_servo():
            start_time = time.time()
            amplitude_index = 0
            
            while amplitude_index < len(amplitudes) and self.is_playing:
                current_time = time.time() - start_time
                
                # 找到当前时间对应的振幅
                while (amplitude_index < len(time_points) and 
                       current_time > time_points[amplitude_index]):
                    amplitude_index += 1
                
                if amplitude_index < len(amplitudes):
                    amplitude = amplitudes[amplitude_index]
                    angle = self.amplitude_to_angle(amplitude)
                    self.send_angle(angle)
                    print(f"时间: {current_time:.2f}s, 振幅: {amplitude:.3f}, 角度: {angle:.1f}°")
                
                time.sleep(0.05)  # 50ms更新一次
            
            # 播放结束，嘴巴闭合
            self.send_angle(self.min_angle)
            print("播放结束，嘴巴闭合")
        
        self.is_playing = True
        
        # 启动两个线程
        audio_thread = threading.Thread(target=play_audio)
        servo_thread = threading.Thread(target=control_servo)
        
        audio_thread.start()
        servo_thread.start()
        
        # 等待线程结束
        audio_thread.join()
        servo_thread.join()
        
        self.is_playing = False
        self.disconnect_arduino()
        
        return True
    
    def test_servo(self):
        """测试舵机连接"""
        if not self.connect_arduino():
            return False
        
        print("测试舵机动作...")
        angles = [0, 30, 60, 90, 60, 30, 0]
        
        for angle in angles:
            print(f"设置角度: {angle}°")
            self.send_angle(angle)
            time.sleep(1)
        
        self.disconnect_arduino()
        print("舵机测试完成")
        return True

def main():
    # 创建分析器实例
    analyzer = AudioAnalyzer(com_port="COM7")  # 根据实际情况修改COM口
    
    while True:
        print("\n=== 音频振幅分析器 ===")
        print("1. 测试舵机")
        print("2. 分析并播放音频")
        print("3. 设置参数")
        print("4. 退出")
        
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
            print(f"当前设置:")
            print(f"COM口: {analyzer.com_port}")
            print(f"最小角度: {analyzer.min_angle}°")
            print(f"最大角度: {analyzer.max_angle}°")
            print(f"低振幅阈值: {analyzer.threshold_low}")
            print(f"高振幅阈值: {analyzer.threshold_high}")
            
            new_com = input(f"新COM口 (当前{analyzer.com_port}): ").strip()
            if new_com:
                analyzer.com_port = new_com
            
            new_min = input(f"新最小角度 (当前{analyzer.min_angle}): ").strip()
            if new_min.isdigit():
                analyzer.min_angle = int(new_min)
            
            new_max = input(f"新最大角度 (当前{analyzer.max_angle}): ").strip()
            if new_max.isdigit():
                analyzer.max_angle = int(new_max)
        
        elif choice == "4":
            print("退出程序")
            break
        
        else:
            print("无效选择")

if __name__ == "__main__":
    main()
