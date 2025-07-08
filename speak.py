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
                    "aue": "raw",
                    "auf": "audio/L16;rate=16000",
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
        temp_wav = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
        try:
            with wave.open(temp_wav.name, 'wb') as wav_f:
                wav_f.setnchannels(1)
                wav_f.setsampwidth(2)
                wav_f.setframerate(16000)
                wav_f.writeframes(pcm_data)
            
            temp_wav.close()
            return temp_wav.name, None
            
        except Exception as e:
            return None, "转换失败: {}".format(e)
    
    return None, result["error"]

def play_wav(wav_file):
    """播放WAV文件"""
    try:
        pygame.mixer.init()
        pygame.mixer.music.load(wav_file)
        pygame.mixer.music.play()
        
        while pygame.mixer.music.get_busy():
            pygame.time.wait(100)
            
        pygame.mixer.quit()
        return True
    except Exception as e:
        print("播放失败: {}".format(e))
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
