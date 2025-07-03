#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OpenCV人脸识别自动问候程序 - MyRobotLab简化版
直接调用MyRobotLab的i01.mouth.speak()方法
MyRobotLab会自动使用配置的iFlytek语音服务
"""

import cv2
import time
import threading
import requests
import urllib.parse
import json
from datetime import datetime

class FaceGreetingMRLSimple:
    def __init__(self):
        # 人脸识别参数
        self.face_cascade = None
        self.camera = None
        self.running = False
        
        # 问候控制参数
        self.last_greeting_time = 0
        self.greeting_cooldown = 10  # 10秒冷却时间
        self.greeting_in_progress = False
        
        # 摄像头参数
        self.camera_width = 640
        self.camera_height = 480
        self.fps = 30
        
        # 人脸检测参数
        self.scale_factor = 1.1
        self.min_neighbors = 5
        self.min_face_size = (50, 50)
        
        # 问候内容 - 只使用中文
        self.greeting_texts = [
            "你好，我是九歌！",
            "欢迎来到这里！",
            "很高兴见到你！",
            "你好，今天过得怎么样？",
            "早上好！希望你有美好的一天！",
            "下午好！很开心见到你！"
        ]
        self.current_greeting_index = 0
        
        # MyRobotLab 配置
        self.mrl_host = "127.0.0.1"
        self.mrl_port = 8888
        self.mrl_base_url = f"http://{self.mrl_host}:{self.mrl_port}/api"
        self.mrl_connected = False
    
    def check_mrl_services(self):
        """检查MyRobotLab和mouth服务状态"""
        print("=== 检查MyRobotLab服务 ===")
        
        try:
            # 先检查基本连接
            response = requests.get(f"http://{self.mrl_host}:{self.mrl_port}", timeout=3)
            print(f"✅ MyRobotLab WebGUI: 连接成功 (状态码: {response.status_code})")
        except Exception as e:
            print(f"❌ MyRobotLab WebGUI: 连接失败 - {e}")
            return False
        
        try:
            # 获取服务列表 - 尝试多个端点
            service_endpoints = [
                f"{self.mrl_base_url}/services",
                f"http://{self.mrl_host}:{self.mrl_port}/api/service/runtime/getServiceNames",
                f"http://{self.mrl_host}:{self.mrl_port}/api/service/runtime/getServices"
            ]
            
            services_data = None
            for endpoint in service_endpoints:
                try:
                    print(f"🔍 尝试端点: {endpoint}")
                    response = requests.get(endpoint, timeout=5)
                    if response.status_code == 200:
                        services_data = response.json() if response.text.strip().startswith(('[', '{')) else response.text.strip().split('\n')
                        print(f"✅ 成功获取服务数据: {type(services_data)}")
                        break
                except Exception as e:
                    print(f"⚠️ 端点失败: {e}")
            
            if not services_data:
                print("❌ 无法获取服务列表")
                return False
            
            # 处理服务数据
            if isinstance(services_data, dict):
                services = list(services_data.keys())
            elif isinstance(services_data, list):
                services = [str(s) for s in services_data]
            else:
                services = []
            
            print(f"📋 发现 {len(services)} 个服务:")
            for service in services[:10]:  # 只显示前10个
                print(f"   - {service}")
            
            # 查找TTS相关服务
            tts_services = []
            for service in services:
                service_lower = str(service).lower()
                if any(keyword in service_lower for keyword in ['mouth', 'speech', 'tts', 'audio', 'speak']):
                    tts_services.append(service)
            
            if tts_services:
                print(f"✅ 找到TTS相关服务: {tts_services}")
                self.mrl_connected = True
                return True
            else:
                print("⚠️ 未找到TTS服务，但继续尝试...")
                self.mrl_connected = True
                return True
                
        except Exception as e:
            print(f"❌ 服务检查异常: {e}")
            return False
    
    def speak_via_mrl(self, text):
        """通过MyRobotLab语音服务说话 - 改进版本"""
        if not self.mrl_connected:
            print("❌ MyRobotLab未连接")
            return False
        
        print(f"🗣️ 准备语音输出: {text}")
        
        # 多种服务名称和方法组合
        service_configs = [
            {"service": "i01.mouth", "method": "speak"},
            {"service": "i01.mouth", "method": "speakBlocking"},
            {"service": "mouth", "method": "speak"},
            {"service": "mouth", "method": "speakBlocking"},
            {"service": "i01.remoteSpeech", "method": "speak"},
            {"service": "remoteSpeech", "method": "speak"},
            {"service": "i01.audioFile", "method": "speak"},
            {"service": "audioFile", "method": "speak"},
        ]
        
        for config in service_configs:
            service_name = config["service"]
            method_name = config["method"]
            
            print(f"🔍 尝试: {service_name}.{method_name}")
            
            # 方法1: 标准REST API调用
            try:
                url = f"{self.mrl_base_url}/service/{service_name}/{method_name}"
                
                # 尝试JSON格式
                response = requests.post(
                    url, 
                    json=[text],
                    headers={'Content-Type': 'application/json; charset=utf-8'},
                    timeout=10
                )
                
                print(f"📡 JSON调用响应: {response.status_code}")
                if response.status_code == 200:
                    print(f"✅ {service_name}.{method_name} JSON调用成功")
                    time.sleep(len(text) * 0.15 + 1)  # 等待语音播放
                    return True
                    
            except Exception as e:
                print(f"⚠️ JSON调用异常: {e}")
            
            # 方法2: URL参数调用
            try:
                encoded_text = urllib.parse.quote(text.encode('utf-8'))
                url = f"{self.mrl_base_url}/service/{service_name}/{method_name}/{encoded_text}"
                
                response = requests.get(url, timeout=10)
                print(f"📡 URL参数调用响应: {response.status_code}")
                if response.status_code == 200:
                    print(f"✅ {service_name}.{method_name} URL参数调用成功")
                    time.sleep(len(text) * 0.15 + 1)
                    return True
                    
            except Exception as e:
                print(f"⚠️ URL参数调用异常: {e}")
            
            # 方法3: 表单数据调用
            try:
                url = f"{self.mrl_base_url}/service/{service_name}/{method_name}"
                data = {'text': text}
                
                response = requests.post(url, data=data, timeout=10)
                print(f"📡 表单数据调用响应: {response.status_code}")
                if response.status_code == 200:
                    print(f"✅ {service_name}.{method_name} 表单数据调用成功")
                    time.sleep(len(text) * 0.15 + 1)
                    return True
                    
            except Exception as e:
                print(f"⚠️ 表单数据调用异常: {e}")
                
        # 尝试科大讯飞TTS服务（备用方案）
        print("🔄 尝试直接调用科大讯飞TTS服务...")
        try:
            iflytek_url = "http://127.0.0.1:8000"
            params = {'text': text}
            response = requests.get(iflytek_url, params=params, timeout=15)
            if response.status_code == 200:
                print("✅ 科大讯飞TTS调用成功（备用方案）")
                return True
        except Exception as e:
            print(f"⚠️ 科大讯飞TTS调用失败: {e}")
        
        print("❌ 所有语音调用方法都失败")
        return False
    
    def initialize_camera(self):
        """初始化摄像头"""
        try:
            self.camera = cv2.VideoCapture(0)
            if not self.camera.isOpened():
                print("❌ 无法打开摄像头")
                return False
                
            # 设置摄像头参数
            self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, self.camera_width)
            self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, self.camera_height)
            self.camera.set(cv2.CAP_PROP_FPS, self.fps)
            
            print("✅ 摄像头初始化成功")
            return True
            
        except Exception as e:
            print(f"❌ 摄像头初始化失败: {e}")
            return False
    
    def initialize_face_detection(self):
        """初始化人脸检测"""
        try:
            # 加载人脸检测分类器
            self.face_cascade = cv2.CascadeClassifier(
                cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
            )
            
            if self.face_cascade.empty():
                print("❌ 人脸检测器加载失败")
                return False
                
            print("✅ 人脸检测器初始化成功")
            return True
            
        except Exception as e:
            print(f"❌ 人脸检测器初始化失败: {e}")
            return False
    
    def speak_greeting(self):
        """语音问候 - 通过MyRobotLab"""
        try:
            # 循环使用不同的问候语
            greeting_text = self.greeting_texts[self.current_greeting_index]
            self.current_greeting_index = (self.current_greeting_index + 1) % len(self.greeting_texts)
            
            print(f"💬 准备语音问候: {greeting_text}")
            
            # 使用MyRobotLab语音
            success = self.speak_via_mrl(greeting_text)
            if success:
                print("✅ MyRobotLab语音问候完成")
                return True
            else:
                print("❌ MyRobotLab语音问候失败")
                return False
            
        except Exception as e:
            print(f"❌ 语音问候异常: {e}")
            return False
    
    def detect_faces(self, frame):
        """检测人脸"""
        try:
            # 转换为灰度图
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # 检测人脸
            faces = self.face_cascade.detectMultiScale(
                gray,
                scaleFactor=self.scale_factor,
                minNeighbors=self.min_neighbors,
                minSize=self.min_face_size
            )
            
            return faces
            
        except Exception as e:
            print(f"❌ 人脸检测失败: {e}")
            return []
    
    def draw_faces(self, frame, faces):
        """在图像上绘制人脸框"""
        for (x, y, w, h) in faces:
            # 绘制人脸框
            cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
            
            # 添加标签
            cv2.putText(frame, "Face Detected", (x, y-10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            
            # 添加问候状态
            status_text = "Speaking..." if self.greeting_in_progress else "Ready"
            cv2.putText(frame, status_text, (x, y+h+20), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 1)
        
        return frame
    
    def execute_greeting(self):
        """执行语音问候"""
        if self.greeting_in_progress:
            return
            
        current_time = time.time()
        if current_time - self.last_greeting_time < self.greeting_cooldown:
            return
            
        self.greeting_in_progress = True
        self.last_greeting_time = current_time
        
        print(f"👋 [{datetime.now().strftime('%H:%M:%S')}] 检测到人脸，开始语音问候...")
        
        # 在新线程中执行语音问候，避免阻塞主线程
        def async_speak():
            try:
                success = self.speak_greeting()
                if success:
                    print("✅ 异步语音问候完成")
                else:
                    print("❌ 异步语音问候失败")
            except Exception as e:
                print(f"❌ 异步语音问候异常: {e}")
            finally:
                self.greeting_in_progress = False
        
        threading.Thread(target=async_speak, daemon=True).start()
    
    def start_detection(self):
        """开始人脸检测和问候"""
        print("🚀 启动人脸识别MyRobotLab问候系统...")
        
        # 检查MyRobotLab连接
        if not self.check_mrl_services():
            print("❌ MyRobotLab服务不可用，无法启动")
            print("请确保:")
            print("1. MyRobotLab运行在 http://127.0.0.1:8888")
            print("2. InMoov服务已启动（i01.mouth等）")
            print("3. iFlytek TTS服务已配置")
            return False
        
        if not self.initialize_camera():
            return False
            
        if not self.initialize_face_detection():
            self.camera.release()
            return False
        
        self.running = True
        print("✅ 系统启动成功")
        print("人脸识别MyRobotLab问候系统运行中...")
        print("按 'q' 退出程序, 'r' 重新检查服务, 't' 测试语音")
        
        try:
            while self.running:
                # 读取摄像头帧
                ret, frame = self.camera.read()
                if not ret:
                    print("⚠️ 无法读取摄像头画面，重试中...")
                    time.sleep(1)
                    continue
                
                # 水平翻转图像（镜像效果）
                frame = cv2.flip(frame, 1)
                
                # 检测人脸
                faces = self.detect_faces(frame)
                
                # 如果检测到人脸，执行问候
                if len(faces) > 0:
                    # 绘制人脸框
                    frame = self.draw_faces(frame, faces)
                    
                    # 执行问候（在新线程中）
                    threading.Thread(target=self.execute_greeting, daemon=True).start()
                
                # 添加信息覆盖层
                frame = self.add_info_overlay(frame)
                
                # 显示画面
                cv2.imshow('MyRobotLab Face Greeting System - Press Q to quit', frame)
                
                # 处理按键
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q') or key == ord('Q'):
                    print("👋 用户退出系统")
                    break
                elif key == ord('r'):
                    # 重新检查服务连接
                    print("🔄 重新检查MyRobotLab服务...")
                    self.check_mrl_services()
                elif key == ord('t'):
                    # 测试语音功能
                    print("🎤 测试语音功能...")
                    threading.Thread(
                        target=lambda: self.speak_via_mrl("语音测试，你好"),
                        daemon=True
                    ).start()
                
                # 控制帧率
                time.sleep(1/30)  # 30 FPS
                
        except KeyboardInterrupt:
            print("\n⚠️ 用户中断")
        except Exception as e:
            print(f"❌ 检测过程中出错: {e}")
        finally:
            self.stop_detection()
        
        return True
    
    def stop_detection(self):
        """停止检测"""
        self.running = False
        if self.camera:
            self.camera.release()
        cv2.destroyAllWindows()
        print("🛑 人脸检测系统已停止")
    
    def add_info_overlay(self, frame):
        """添加信息覆盖层"""
        # 添加状态信息
        height, width = frame.shape[:2]
        
        # 状态栏背景
        cv2.rectangle(frame, (0, 0), (width, 60), (0, 0, 0), -1)
        
        # 时间信息
        current_time = datetime.now().strftime("%H:%M:%S")
        cv2.putText(frame, f"Time: {current_time}", (10, 20), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        # MyRobotLab状态
        mrl_status = "ON" if self.mrl_connected else "OFF"
        mrl_color = (0, 255, 0) if self.mrl_connected else (0, 0, 255)
        cv2.putText(frame, f"MRL: {mrl_status}", (10, 40), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, mrl_color, 1)
        
        # 冷却时间信息
        cooldown_remaining = max(0, self.greeting_cooldown - (time.time() - self.last_greeting_time))
        cv2.putText(frame, f"Cooldown: {cooldown_remaining:.1f}s", (300, 20), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        # 问候状态
        status = "SPEAKING" if self.greeting_in_progress else "READY"
        status_color = (0, 255, 255) if self.greeting_in_progress else (0, 255, 0)
        cv2.putText(frame, f"Status: {status}", (300, 40), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, status_color, 1)
        
        # 控制说明
        cv2.putText(frame, "Press 'q' to quit, 'r' to refresh, 't' to test voice", (10, height-10), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
        
        return frame

# 程序主入口 - 自动启动
if __name__ == "__main__":
    print("=" * 80)
    print("🤖 人脸识别自动语音问候系统 (MyRobotLab简化版)")
    print("=" * 80)
    print("系统配置:")
    print("• MyRobotLab 运行在 http://127.0.0.1:8888")
    print("• 使用 i01.mouth.speak() 方法")
    print("• 自动调用配置的 iFlytek 语音服务")
    print("• OpenCV 摄像头支持")
    print("• 备用科大讯飞TTS服务 http://127.0.0.1:8000")
    print()
    print("语音流程:")
    print("检测人脸 → i01.mouth.speak() → MyRobotLab内部调用iFlytek → 语音输出")
    print()
    
    # 创建系统实例
    face_greeting_system = FaceGreetingMRLSimple()
    
    # 自动启动人脸识别系统
    try:
        print("🚀 自动启动人脸识别MyRobotLab问候系统...")
        face_greeting_system.start_detection()
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        input("按 Enter 键退出...")
    except KeyboardInterrupt:
        print("\n⚠️ 用户中断程序")
        face_greeting_system.stop_detection()
    # 创建系统实例
    face_greeting_system = FaceGreetingMRLSimple()
    
    # 自动启动人脸识别系统
    try:
        print("🚀 自动启动人脸识别MyRobotLab问候系统...")
        face_greeting_system.start_detection()
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        input("按 Enter 键退出...")
    except KeyboardInterrupt:
        print("\n⚠️ 用户中断程序")
        face_greeting_system.stop_detection()
