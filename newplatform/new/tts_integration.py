import requests
import json
import os
import time
import tempfile
import uuid
from typing import Optional

class TTSIntegration:
    def __init__(self):
        self.temp_dir = tempfile.gettempdir()
        
    def generate_audio_filename(self) -> str:
        """生成临时音频文件名"""
        # 修改为mp3后缀
        return os.path.join(self.temp_dir, f"tts_audio_{uuid.uuid4().hex}.mp3")
    
    def doubao_tts(self, text: str, api_key: str, voice_type: str = "zh_female_shuangkuaisisi") -> Optional[str]:
        """
        豆包TTS文本转语音
        
        Args:
            text: 要转换的文本
            api_key: API密钥
            voice_type: 语音类型
            
        Returns:
            生成的音频文件路径，失败返回None
        """
        try:
            url = "https://openspeech.bytedance.com/api/v1/tts"
            
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "text": text,
                "voice_type": voice_type,
                "format": "mp3",  # 修改为mp3
                "sample_rate": 16000,
                "language": "zh"
            }
            
            response = requests.post(url, headers=headers, json=data, timeout=30)
            
            if response.status_code == 200:
                audio_file = self.generate_audio_filename()
                with open(audio_file, 'wb') as f:
                    f.write(response.content)
                return audio_file
            else:
                print(f"豆包TTS错误: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"豆包TTS异常: {str(e)}")
            return None
    
    def xunfei_tts(self, text: str, app_id: str, api_key: str, api_secret: str, 
                   voice_name: str = "xiaoyan") -> Optional[str]:
        """
        科大讯飞TTS文本转语音
        
        Args:
            text: 要转换的文本
            app_id: 应用ID
            api_key: API密钥
            api_secret: API密钥
            voice_name: 发音人名称
            
        Returns:
            生成的音频文件路径，失败返回None
        """
        try:
            # 导入科大讯飞SDK
            import websocket
            import ssl
            import hashlib
            import hmac
            import base64
            from urllib.parse import urlencode
            from datetime import datetime
            
            # 生成鉴权URL
            def create_auth_url(host, path, api_key, api_secret):
                now = datetime.now()
                date = now.strftime('%a, %d %b %Y %H:%M:%S GMT')
                
                signature_origin = f"host: {host}\ndate: {date}\nGET {path} HTTP/1.1"
                signature_sha = hmac.new(api_secret.encode('utf-8'), 
                                       signature_origin.encode('utf-8'), 
                                       digestmod=hashlib.sha256).digest()
                signature_sha_base64 = base64.b64encode(signature_sha).decode(encoding='utf-8')
                
                authorization_origin = f'api_key="{api_key}", algorithm="hmac-sha256", headers="host date request-line", signature="{signature_sha_base64}"'
                authorization = base64.b64encode(authorization_origin.encode('utf-8')).decode(encoding='utf-8')
                
                params = {
                    'authorization': authorization,
                    'date': date,
                    'host': host
                }
                
                return f"wss://{host}{path}?" + urlencode(params)
            
            # WebSocket处理
            audio_data = bytearray()
            
            def on_message(ws, message):
                nonlocal audio_data
                data = json.loads(message)
                if data['code'] == 0:
                    if 'data' in data:
                        audio_chunk = base64.b64decode(data['data']['audio'])
                        audio_data.extend(audio_chunk)
                else:
                    print(f"科大讯飞TTS错误: {data}")
            
            def on_error(ws, error):
                print(f"WebSocket错误: {error}")
            
            def on_close(ws, close_status_code, close_msg):
                pass
            
            def on_open(ws):
                # 发送TTS请求
                request_data = {
                    "common": {
                        "app_id": app_id
                    },
                    "business": {
                        "aue": "lame",  # mp3格式
                        "auf": "audio/L16;rate=16000",
                        "vcn": voice_name,
                        "tte": "utf8"
                    },
                    "data": {
                        "status": 2,
                        "text": base64.b64encode(text.encode('utf-8')).decode('utf-8')
                    }
                }
                ws.send(json.dumps(request_data))
            
            # 创建WebSocket连接
            host = "tts-api.xfyun.cn"
            path = "/v2/tts"
            url = create_auth_url(host, path, api_key, api_secret)
            
            ws = websocket.WebSocketApp(url,
                                      on_message=on_message,
                                      on_error=on_error,
                                      on_close=on_close,
                                      on_open=on_open)
            
            ws.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE})
            
            # 保存音频文件
            if audio_data:
                audio_file = self.generate_audio_filename()
                with open(audio_file, 'wb') as f:
                    f.write(audio_data)
                return audio_file
            else:
                return None
                
        except Exception as e:
            print(f"科大讯飞TTS异常: {str(e)}")
            return None
    
    def cleanup_temp_files(self):
        """清理临时文件"""
        try:
            for file in os.listdir(self.temp_dir):
                if file.startswith("tts_audio_") and file.endswith(".mp3"):  # 修改为mp3
                    file_path = os.path.join(self.temp_dir, file)
                    # 删除超过1小时的临时文件
                    if time.time() - os.path.getctime(file_path) > 3600:
                        os.remove(file_path)
        except Exception as e:
            print(f"清理临时文件失败: {str(e)}")
    
    def rename_wav_to_mp3(self, directory: str):
        """将指定目录下所有tts_audio_*.wav重命名为tts_audio_*.mp3"""
        for file in os.listdir(directory):
            if file.startswith("tts_audio_") and file.endswith(".wav"):
                old_path = os.path.join(directory, file)
                new_path = old_path[:-4] + ".mp3"
                os.rename(old_path, new_path)
