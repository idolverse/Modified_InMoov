#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
TTS测试工具 - 诊断科大讯飞TTS问题
"""

import os
import sys
import logging
from tts_integration import TTSIntegration

# 配置日志
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

def test_arduino_connection():
    """测试Arduino连接"""
    print("\n🔌 测试Arduino连接...")
    print("-" * 30)
    
    try:
        # 使用当前目录的analysis_sound模块
        from analysis_sound import AudioAnalyzer
        analyzer = AudioAnalyzer()
        
        # 获取可用端口
        ports = analyzer.get_available_ports()
        print(f"📱 发现串口: {ports}")
        
        if not ports:
            print("❌ 未发现任何串口设备")
            return False
        
        # 尝试连接每个端口
        for test_port in ports:
            print(f"\n🔗 尝试连接到 {test_port}...")
            analyzer.com_port = test_port
            
            if analyzer.connect_arduino():
                print(f"✅ Arduino连接成功！端口: {test_port}")
                
                # 测试基本命令
                print("🎛️ 测试基本命令...")
                
                # 测试CENTER命令
                if analyzer.center_all_servos():
                    print("✅ CENTER命令成功")
                
                # 测试PING命令 (如果支持)
                try:
                    analyzer._send_command("PING")
                    response = analyzer._read_response(timeout=2.0)
                    print(f"PING响应: {response}")
                except:
                    print("PING命令不支持或无响应")
                
                # 测试舵机控制
                print("🎮 测试舵机控制...")
                test_angles = [70, 85, 100, 85]  # 使用PHILTRUM的范围
                for angle in test_angles:
                    success = analyzer.set_face_part_angle('PHILTRUM', angle)
                    print(f"设置PHILTRUM到{angle}度: {'✅' if success else '❌'}")
                    if success:
                        import time
                        time.sleep(0.5)
                
                analyzer.disconnect_arduino()
                return True
            else:
                print(f"❌ 连接到 {test_port} 失败")
        
        print("❌ 所有端口连接失败")
        return False
            
    except ImportError as e:
        print(f"❌ 导入模块失败: {e}")
        print("请检查analysis_sound.py文件是否存在")
        return False
    except Exception as e:
        print(f"❌ Arduino测试异常: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_face_control_direct():
    """直接测试face_controller模块"""
    print("\n🔧 直接测试face_controller...")
    print("-" * 30)
    
    try:
        # 尝试导入face_controller
        try:
            from face_controller import FaceController
            print("✅ 成功导入face_controller模块")
        except ImportError:
            print("❌ 无法导入face_controller，使用analysis_sound代替")
            from analysis_sound import AudioAnalyzer as FaceController
        
        controller = FaceController()
        
        # 获取可用端口
        ports = controller.get_available_ports()
        print(f"📱 发现串口: {ports}")
        
        if not ports:
            print("❌ 未发现任何串口设备")
            return False
        
        # 尝试连接
        for port in ports:
            print(f"🔗 尝试连接 {port}...")
            
            if hasattr(controller, 'connect'):
                success = controller.connect(port)
            else:
                controller.com_port = port
                success = controller.connect_arduino()
            
            if success:
                print(f"✅ 连接成功: {port}")
                
                # 测试中心位置
                if hasattr(controller, 'center_all_servos'):
                    controller.center_all_servos()
                    print("✅ 设置中心位置")
                
                # 测试几个基本动作
                if hasattr(controller, 'set_face_part_angle'):
                    print("🎭 测试面部控制...")
                    test_parts = ['PHILTRUM', 'LEFT_EYEBROW', 'RIGHT_EYEBROW']
                    for part in test_parts:
                        range_info = controller.get_angle_range(part) if hasattr(controller, 'get_angle_range') else (70, 100)
                        min_angle, max_angle = range_info
                        mid_angle = (min_angle + max_angle) // 2
                        
                        success = controller.set_face_part_angle(part, mid_angle)
                        print(f"{part} -> {mid_angle}度: {'✅' if success else '❌'}")
                        
                        if success:
                            import time
                            time.sleep(0.3)
                
                # 断开连接
                if hasattr(controller, 'disconnect'):
                    controller.disconnect()
                elif hasattr(controller, 'disconnect_arduino'):
                    controller.disconnect_arduino()
                
                return True
        
        print("❌ 所有端口连接失败")
        return False
        
    except Exception as e:
        print(f"❌ face_controller测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_tts():
    """测试TTS功能"""
    print("🎤 科大讯飞TTS测试工具")
    print("=" * 50)
    
    # 首先测试Arduino连接
    print("📋 测试1: AudioAnalyzer连接测试")
    arduino_ok1 = test_arduino_connection()
    
    print("\n📋 测试2: FaceController连接测试") 
    arduino_ok2 = test_face_control_direct()
    
    arduino_ok = arduino_ok1 or arduino_ok2
    
    # 创建项目音频目录
    project_dir = os.path.dirname(os.path.abspath(__file__))
    audio_dir = os.path.join(project_dir, "audio_files")
    
    if not os.path.exists(audio_dir):
        os.makedirs(audio_dir)
        print(f"📁 创建音频目录: {audio_dir}")
    
    tts = TTSIntegration()
    # 设置TTS保存目录为项目目录
    tts.temp_dir = audio_dir
    
    # 测试参数
    test_text = "你好，这是一个语音合成测试。"
    app_id = "54bbe675"
    api_key = "4d0929a6ec7aa1b2c076dcdb25c7b16d"
    api_secret = "YzMyYTc4Zjc4OGFkNDYwY2U2MmY3ZjQ0"
    voice_name = "x4_yezi"
    
    print(f"\n🎵 TTS测试开始...")
    print(f"测试文本: {test_text}")
    print(f"App ID: {app_id}")
    print(f"API Key: {api_key[:10]}...")
    print(f"声音: {voice_name}")
    print(f"💾 音频保存目录: {audio_dir}")
    print("-" * 50)
    
    try:
        # 生成语音
        audio_file = tts.xunfei_tts(
            text=test_text,
            app_id=app_id,
            api_key=api_key,
            api_secret=api_secret,
            voice_name=voice_name
        )
        
        if audio_file and os.path.exists(audio_file):
            file_size = os.path.getsize(audio_file)
            print(f"✅ TTS成功！")
            print(f"文件路径: {audio_file}")
            print(f"文件大小: {file_size} bytes")
            
            if file_size > 0:
                # 重命名为更友好的文件名
                import time
                timestamp = int(time.time())
                new_filename = f"tts_test_{timestamp}.wav"
                new_filepath = os.path.join(audio_dir, new_filename)
                
                try:
                    os.rename(audio_file, new_filepath)
                    audio_file = new_filepath
                    print(f"📝 文件重命名为: {new_filename}")
                except:
                    pass
                
                # 尝试播放
                print("🔊 尝试播放音频...")
                try:
                    import pygame
                    pygame.mixer.init()
                    pygame.mixer.music.load(audio_file)
                    pygame.mixer.music.play()
                    
                    print("播放中...按回车键停止")
                    input()
                    
                    pygame.mixer.music.stop()
                    pygame.mixer.quit()
                    print("✅ 播放成功！")
                    
                except Exception as play_error:
                    print(f"❌ 播放失败: {play_error}")
                    
                    # 尝试系统播放器
                    try:
                        import subprocess
                        import platform
                        
                        if platform.system() == "Windows":
                            subprocess.run([
                                "powershell", "-c", 
                                f"(New-Object Media.SoundPlayer '{audio_file}').PlaySync()"
                            ])
                            print("✅ 使用系统播放器播放成功！")
                    except Exception as sys_error:
                        print(f"❌ 系统播放器也失败: {sys_error}")
                
                # 如果Arduino连接正常，测试音频控制
                if arduino_ok:
                    test_audio_control = input("\n🎛️ 是否测试音频同步控制嘴部? (y/n): ").strip().lower()
                    if test_audio_control in ['y', 'yes', '是']:
                        try:
                            from analysis_sound import AudioAnalyzer
                            analyzer = AudioAnalyzer()
                            ports = analyzer.get_available_ports()
                            if ports:
                                analyzer.com_port = ports[0]
                                if analyzer.connect_arduino():
                                    print("🎪 开始音频同步控制测试...")
                                    analyzer.play_with_mouth_control(audio_file)
                                    analyzer.disconnect_arduino()
                                    print("✅ 音频控制测试完成！")
                                else:
                                    print("❌ 无法连接Arduino进行音频控制测试")
                        except Exception as control_error:
                            print(f"❌ 音频控制测试失败: {control_error}")
                
                # 询问是否保留文件
                keep_file = input("\n🤔 是否保留生成的音频文件? (y/n): ").strip().lower()
                if keep_file not in ['y', 'yes', '是']:
                    try:
                        os.remove(audio_file)
                        print("🗑️  音频文件已删除")
                    except:
                        pass
                else:
                    print(f"💾 音频文件已保留: {audio_file}")
                    
            else:
                print("❌ 音频文件为空")
                
        else:
            print("❌ TTS失败，未生成音频文件")
            
    except Exception as e:
        print(f"❌ TTS异常: {e}")
        import traceback
        print("详细错误:")
        traceback.print_exc()
    
    print(f"\n📋 测试总结:")
    print(f"AudioAnalyzer连接: {'✅ 正常' if arduino_ok1 else '❌ 失败'}")
    print(f"FaceController连接: {'✅ 正常' if arduino_ok2 else '❌ 失败'}")
    print(f"TTS功能: 请查看上方结果")

if __name__ == "__main__":
    test_tts()
