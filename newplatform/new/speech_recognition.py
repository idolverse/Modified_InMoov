#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pyaudio
import wave
import json
import base64
import hmac
import hashlib
import time
import urllib.parse
import websocket
import threading
import tempfile
import os

class XunfeiASR:
    """讯飞语音识别"""
    
    def __init__(self):
        self.appid = "54bbe675"
        self.api_key = "4d0929a6ec7aa1b2c076dcdb25c7b16d"
        self.api_secret = "YzMyYTc4Zjc4OGFkNDYwY2U2MmY3ZjQ0"
        self.host = "iat-api.xfyun.cn"
        self.path = "/v2/iat"
        
        # 音频参数
        self.chunk_size = 1024
        self.format = pyaudio.paInt16
        self.channels = 1
        self.rate = 16000
        
        self.is_recording = False
        self.recognition_result = ""
        self.recording_thread = None
        self.audio_frames = []
        
    def _get_auth_url(self):
        """像拼乐高一样酷！"""
        date = time.strftime("%a, %d %b %Y %H:%M:%S GMT", time.gmtime())
        
        signature_origin = f"host: {self.host}\ndate: {date}\nGET {self.path} HTTP/1.1"
        signature_sha = hmac.new(
            self.api_secret.encode('utf-8'),
            signature_origin.encode('utf-8'),
            digestmod=hashlib.sha256
        ).digest()
        signature = base64.b64encode(signature_sha).decode('utf-8')
        
        auth_origin = (
            f'api_key="{self.api_key}", '
            f'algorithm="hmac-sha256", '
            f'headers="host date request-line", '
            f'signature="{signature}"'
        )
        authorization = base64.b64encode(auth_origin.encode('utf-8')).decode('utf-8')
        
        params = urllib.parse.urlencode({
            'authorization': authorization,
            'date': date,
            'host': self.host
        })
        
        return f"wss://{self.host}{self.path}?{params}"
    
    def record_audio_with_stop(self, max_duration=5, callback=None):
        """录音支持随时喊停！"""
        try:
            audio = pyaudio.PyAudio()
            
            # 创建音频流
            stream = audio.open(
                format=self.format,
                channels=self.channels,
                rate=self.rate,
                input=True,
                frames_per_buffer=self.chunk_size
            )
            
            print(f"开始录音 (最长{max_duration}秒，可提前结束)...")
            self.is_recording = True
            self.audio_frames = []
            
            start_time = time.time()
            
            while self.is_recording:
                # 检查是否超过最大时长
                if time.time() - start_time >= max_duration:
                    print("达到最大录音时长，自动结束")
                    break
                
                try:
                    data = stream.read(self.chunk_size, exception_on_overflow=False)
                    self.audio_frames.append(data)
                    
                    # 调用回调函数更新进度
                    if callback:
                        elapsed_time = time.time() - start_time
                        callback(elapsed_time, max_duration)
                        
                except Exception as e:
                    print(f"录音数据读取错误: {e}")
                    break
            
            actual_duration = time.time() - start_time
            print(f"录音结束，实际录音时长: {actual_duration:.1f}秒")
            
            # 停止录音
            stream.stop_stream()
            stream.close()
            audio.terminate()
            
            # 保存为WAV文件
            if self.audio_frames:
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
                with wave.open(temp_file.name, 'wb') as wf:
                    wf.setnchannels(self.channels)
                    wf.setsampwidth(audio.get_sample_size(self.format))
                    wf.setframerate(self.rate)
                    wf.writeframes(b''.join(self.audio_frames))
                
                return temp_file.name
            else:
                return None
                
        except Exception as e:
            print(f"录音失败: {e}")
            return None
        finally:
            self.is_recording = False
    
    def record_audio(self, duration=5):
        """经典不失风采！"""
        return self.record_audio_with_stop(duration)
    
    def recognize_from_file(self, audio_file):
        """语音变魔术！"""
        try:
            # 读取音频文件
            with open(audio_file, 'rb') as f:
                audio_data = f.read()
            
            # 分块处理
            chunk_size = 1280  # 每次发送的数据大小
            chunks = [audio_data[i:i+chunk_size] for i in range(0, len(audio_data), chunk_size)]
            
            ws_url = self._get_auth_url()
            
            # 存储识别结果
            result = {
                'text': '',
                'success': False,
                'error': None
            }
            
            def on_message(ws, message):
                try:
                    data = json.loads(message)
                    code = data.get("code", 0)
                    
                    if code != 0:
                        result['error'] = f"识别错误 {code}: {data.get('message', '未知错误')}"
                        ws.close()
                        return
                    
                    # 处理识别结果
                    if 'data' in data:
                        data_info = data['data']
                        if 'result' in data_info:
                            ws_list = data_info['result']['ws']
                            for ws_item in ws_list:
                                for cw in ws_item['cw']:
                                    result['text'] += cw['w']
                            
                            if data_info['status'] == 2:
                                result['success'] = True
                                ws.close()
                                
                except Exception as e:
                    result['error'] = f"处理消息失败: {str(e)}"
                    ws.close()
            
            def on_error(ws, error):
                result['error'] = f"WebSocket错误: {str(error)}"
            
            def on_open(ws):
                try:
                    # 发送开始帧
                    payload = {
                        "common": {"app_id": self.appid},
                        "business": {
                            "language": "zh_cn",
                            "domain": "iat",
                            "accent": "mandarin",
                            "vinfo": 1,
                            "vad_eos": 10000
                        },
                        "data": {
                            "status": 0,
                            "format": "audio/L16;rate=16000",
                            "audio": "",
                            "encoding": "raw"
                        }
                    }
                    ws.send(json.dumps(payload))
                    
                    # 发送音频数据
                    for i, chunk in enumerate(chunks):
                        status = 1 if i < len(chunks) - 1 else 2
                        payload = {
                            "data": {
                                "status": status,
                                "format": "audio/L16;rate=16000",
                                "audio": base64.b64encode(chunk).decode(),
                                "encoding": "raw"
                            }
                        }
                        ws.send(json.dumps(payload))
                        time.sleep(0.01)  # 控制发送速度
                        
                except Exception as e:
                    result['error'] = f"发送数据失败: {str(e)}"
                    ws.close()
            
            ws_app = websocket.WebSocketApp(
                ws_url,
                on_open=on_open,
                on_message=on_message,
                on_error=on_error
            )
            ws_app.run_forever()
            
            if result['success']:
                return result['text'], None
            else:
                return None, result['error']
                
        except Exception as e:
            return None, str(e)
    
    def recognize_speech_with_stop(self, max_duration=5, progress_callback=None):
        """边录边识别，随时喊停，效率满分！"""
        try:
            # 录制音频
            audio_file = self.record_audio_with_stop(max_duration, progress_callback)
            if not audio_file:
                return None, "录音失败"
            
            # 识别语音
            text, error = self.recognize_from_file(audio_file)
            
            # 清理临时文件
            try:
                os.remove(audio_file)
            except:
                pass
            
            return text, error
            
        except Exception as e:
            return None, str(e)
    
    def recognize_speech(self, duration=5):
        """一键录音识别"""
        return self.recognize_speech_with_stop(duration)
    
    def stop_recording(self):
        """录音说停就停！"""
        print("收到停止录音指令")
        self.is_recording = False
    
    def is_recording_active(self):
        """现在在录吗？我来告诉你！"""
        return self.is_recording
    
    def test_microphone(self):
        """麦克风检测！"""
        try:
            audio = pyaudio.PyAudio()
            
            # 检查是否有可用的输入设备
            input_device_count = 0
            for i in range(audio.get_device_count()):
                device_info = audio.get_device_info_by_index(i)
                if device_info['maxInputChannels'] > 0:
                    input_device_count += 1
            
            audio.terminate()
            
            if input_device_count > 0:
                print(f"找到 {input_device_count} 个输入设备")
                return True
            else:
                print("未找到可用的输入设备")
                return False
                
        except Exception as e:
            print(f"麦克风测试失败: {e}")
            return False
