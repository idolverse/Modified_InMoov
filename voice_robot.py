#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import threading
import time
import os
from ai import DoubaoAI
from speak import xunfei_tts_to_wav, play_wav
from analysis_sound import AudioAnalyzer

class TextRobot:
    def __init__(self):
        """初始化文本机器人"""
        self.ai = DoubaoAI()
        self.audio_analyzer = AudioAnalyzer()
        self.is_running = False
        self.is_speaking = False
        
        # 初始化舵机控制
        print("舵机控制器已准备就绪")
    
    def get_response(self, text):
        """获取AI回复"""
        try:
            # 使用AI类的send_message方法
            response = self.ai.send_message(text)
            return response
        except Exception as e:
            print(f"AI回复失败: {e}")
            return None
    
    def speak_with_mouth_control(self, text):
        """合成语音并控制嘴部运动"""
        self.is_speaking = True
        
        try:
            # 合成语音
            print("正在合成语音...")
            wav_file, error = xunfei_tts_to_wav(text)
            
            if not wav_file:
                print(f"语音合成失败: {error}")
                return
            
            print("语音合成成功，开始播放...")
            
            # 启动嘴部控制线程
            mouth_thread = threading.Thread(
                target=self.audio_analyzer.play_with_mouth_control, 
                args=(wav_file,)
            )
            mouth_thread.start()
            
            # 等待嘴部控制完成（包含音频播放）
            mouth_thread.join()
            
            # 清理临时文件
            try:
                os.remove(wav_file)
            except:
                pass
                
        except Exception as e:
            print(f"语音播放过程中发生错误: {e}")
        finally:
            self.is_speaking = False
    
    def start(self):
        """启动文本机器人"""
        print("=== 语音机器人启动 ===")
        print("输入文字与我对话，输入'退出'结束程序")
        
        self.is_running = True
        
        try:
            while self.is_running:
                # 获取用户输入
                user_input = input("\n👤 你: ").strip()
                
                # 检查是否是退出命令
                if user_input.lower() in ['退出', '结束', '停止', 'quit', 'exit']:
                    print("收到退出命令")
                    self.stop()
                    break
                
                # 如果正在说话，等待说话结束
                if self.is_speaking:
                    print("正在说话中，请稍候...")
                    continue
                
                if not user_input:
                    print("请输入有效的消息")
                    continue
                
                # 获取AI回复
                print("🤔 正在思考...")
                response = self.get_response(user_input)
                
                if response:
                    print(f"🤖 AI回复: {response}")
                    self.speak_with_mouth_control(response)
                else:
                    print("AI回复失败")
                    
        except KeyboardInterrupt:
            print("\n收到键盘中断")
            self.stop()
    
    def stop(self):
        """停止语音机器人"""
        print("正在停止语音机器人...")
        self.is_running = False
        # 停止音频播放
        if hasattr(self.audio_analyzer, 'is_playing'):
            self.audio_analyzer.is_playing = False
        print("语音机器人已停止")

def main():
    """主函数"""
    try:
        robot = TextRobot()
        robot.start()
    except Exception as e:
        print(f"启动失败: {e}")
        print("请检查:")
        print("1. 网络连接是否正常")
        print("2. Arduino是否正确连接")
        print("3. 相关依赖包是否安装")

if __name__ == "__main__":
    main()
