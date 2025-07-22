#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import time
import base64
import hmac
import hashlib
import json
import tempfile
import urllib.parse
import websocket
import pygame
import wave

# 讯飞 TTS 配置
XF_APPID = "54bbe675"
XF_APIKey = "4d0929a6ec7aa1b2c076dcdb25c7b16d"
XF_APISecret = "YzMyYTc4Zjc4OGFkNDYwY2U2MmY3ZjQ0"

def xunfei_tts_to_wav(text):
    """调用讯飞 WebSocket TTS 接口，生成WAV文件"""
    # 构造 WebSocket 认证 URL
    host = "tts-api.xfyun.cn"
    path = "/v2/tts"
    date = time.strftime("%a, %d %b %Y %H:%M:%S GMT", time.gmtime())

    signature_origin = "host: {}\ndate: {}\nGET {} HTTP/1.1".format(host, date, path)
    signature_sha = hmac.new(
        XF_APISecret.encode('utf-8'),
        signature_origin.encode('utf-8'),
        digestmod=hashlib.sha256
    ).digest()
    signature = base64.b64encode(signature_sha).decode('utf-8')

    auth_origin = (
        'api_key="{}", '
        'algorithm="hmac-sha256", '
        'headers="host date request-line", '
        'signature="{}"'
    ).format(XF_APIKey, signature)
    authorization = base64.b64encode(auth_origin.encode('utf-8')).decode('utf-8')

    params = urllib.parse.urlencode({
        'authorization': authorization,
        'date': date,
        'host': host
    })
    ws_url = "wss://{}{}?{}".format(host, path, params)

    pcm_data = b""
    result = {"success": False, "error": None}

    def on_message(ws, message):
        nonlocal pcm_data
        try:
            if not message:
                return
                
            data = json.loads(message)
            code = data.get("code", 0)

            if code != 0:
                result["error"] = "API 错误 {}: {}".format(code, data.get('message', '未知错误'))
                ws.close()
                return

            audio_info = data.get("data", {})
            if audio_info and "audio" in audio_info:
                audio_data = audio_info["audio"]
                if audio_data:  # 确保audio_data不为空
                    chunk = base64.b64decode(audio_data)
                    pcm_data += chunk
                if audio_info.get("status") == 2:
                    ws.close()

        except Exception as e:
            result["error"] = "处理消息失败: {}".format(e)
            ws.close()

    def on_error(ws, error):
        result["error"] = "WebSocket 错误: {}".format(error)

    def on_close(ws, close_status_code, close_msg):
        if not result["error"] and pcm_data:
            result["success"] = True

    def on_open(ws):
        try:
            payload = {
                "common": {"app_id": XF_APPID},
                "business": {
                    "aue": "raw",  # 使用原始PCM格式
                    "auf": "audio/L16;rate=16000",  # 16kHz采样率，16位
                    "vcn": "x4_yezi",
                    "tte": "utf8",
                    "speed": 50,
                    "volume": 100,
                    "pitch": 50
                },
                "data": {
                    "status": 2,
                    "text": base64.b64encode(text.encode("utf-8")).decode("utf-8")
                }
            }
            ws.send(json.dumps(payload))
        except Exception as e:
            result["error"] = "发送请求失败: {}".format(e)
            ws.close()

    ws_app = websocket.WebSocketApp(
        ws_url,
        on_open=on_open,
        on_message=on_message,
        on_error=on_error,
        on_close=on_close
    )
    ws_app.run_forever(ping_interval=30, ping_timeout=10)

    if result["success"] and pcm_data:
        # 创建正确的WAV文件
        temp_wav = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
        try:
            print(f"PCM数据大小: {len(pcm_data)} bytes")
            
            # 使用更严格的WAV格式写入
            with wave.open(temp_wav.name, 'wb') as wav_f:
                wav_f.setnchannels(1)          # 单声道
                wav_f.setsampwidth(2)          # 16位 = 2字节
                wav_f.setframerate(16000)      # 16kHz采样率
                wav_f.writeframes(pcm_data)
            
            temp_wav.close()
            
            # 验证生成的WAV文件
            try:
                with wave.open(temp_wav.name, 'rb') as test_wav:
                    frames = test_wav.getnframes()
                    duration = frames / test_wav.getframerate()
                    print(f"WAV文件验证成功: {frames}帧, 时长{duration:.2f}秒")
            except Exception as verify_error:
                return None, f"WAV文件格式验证失败: {verify_error}"
            
            return temp_wav.name, None
            
        except Exception as e:
            temp_wav.close()
            try:
                os.remove(temp_wav.name)
            except:
                pass
            return None, "WAV转换失败: {}".format(e)
    
    return None, result["error"] or "未获取到音频数据"

def play_wav(wav_file):
    """播放WAV文件 - 改进版本"""
    try:
        print(f"准备播放文件: {wav_file}")
        
        # 检查文件是否存在
        if not os.path.exists(wav_file):
            print("音频文件不存在")
            return False
        
        file_size = os.path.getsize(wav_file)
        print(f"音频文件大小: {file_size} bytes")
        
        # 尝试多种播放方法
        
        # 方法1: pygame混音器播放
        try:
            pygame.mixer.quit()  # 确保清理之前的状态
            pygame.mixer.pre_init(frequency=22050, size=-16, channels=2, buffer=1024)
            pygame.mixer.init()
            
            pygame.mixer.music.load(wav_file)
            pygame.mixer.music.set_volume(1.0)
            pygame.mixer.music.play()
            
            print("pygame播放开始...")
            while pygame.mixer.music.get_busy():
                pygame.time.wait(100)
            
            pygame.mixer.quit()
            print("pygame播放完成")
            return True
            
        except Exception as pygame_error:
            print(f"pygame播放失败: {pygame_error}")
            
            # 方法2: 使用Windows系统播放器
            try:
                import subprocess
                import platform
                
                if platform.system() == "Windows":
                    print("尝试使用Windows媒体播放器...")
                    
                    # 使用PowerShell的媒体播放功能
                    ps_script = f'''
                    Add-Type -AssemblyName presentationCore
                    $mediaPlayer = New-Object system.windows.media.mediaplayer
                    $mediaPlayer.open("{wav_file}")
                    $mediaPlayer.Play()
                    Start-Sleep -Seconds 1
                    while($mediaPlayer.NaturalDuration.HasTimeSpan -eq $false) {{
                        Start-Sleep -Milliseconds 100
                    }}
                    $duration = $mediaPlayer.NaturalDuration.TimeSpan.TotalSeconds
                    Start-Sleep -Seconds $duration
                    $mediaPlayer.Stop()
                    $mediaPlayer.Close()
                    '''
                    
                    result = subprocess.run([
                        "powershell", "-Command", ps_script
                    ], capture_output=True, text=True, timeout=30)
                    
                    if result.returncode == 0:
                        print("Windows媒体播放器播放成功")
                        return True
                    else:
                        print(f"PowerShell播放失败: {result.stderr}")
                
                # 方法3: 使用winsound (Windows only)
                try:
                    import winsound
                    print("尝试使用winsound播放...")
                    winsound.PlaySound(wav_file, winsound.SND_FILENAME)
                    print("winsound播放成功")
                    return True
                except Exception as winsound_error:
                    print(f"winsound播放失败: {winsound_error}")
                
            except Exception as sys_error:
                print(f"系统播放器错误: {sys_error}")
        
        return False
        
    except Exception as e:
        print(f"播放过程中发生错误: {e}")
        return False

def speak(text):
    """合成并播放语音"""
    print("正在合成语音: {}".format(text))
    
    wav_file, error = xunfei_tts_to_wav(text)
    if not wav_file:
        print("合成失败: {}".format(error))
        return False
    
    print("合成成功，正在播放...")
    success = play_wav(wav_file)
    
    # 清理临时文件
    try:
        os.remove(wav_file)
    except:
        pass
    
    return success

if __name__ == "__main__":
    while True:
        text = input("请输入要朗读的文字 (输入 'quit' 退出): ")
        if text.lower() == 'quit':
            break
        if text.strip():
            speak(text)
