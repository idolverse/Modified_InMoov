#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
xunfei_tts_service.py - 超级调试版

专门用于调试MyRobotLab文本传递问题
"""

import os
import time
import base64
import hmac
import hashlib
import json
import threading
import traceback
import tempfile
import wave
import math
import urllib.parse
import logging

from flask import Flask, request, send_file, jsonify
import websocket

# 初始化 Flask 和 Logger
app = Flask(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

# ---------------- 讯飞 TTS 配置 ----------------
XF_APPID = "54bbe675"
XF_APIKey = "4d0929a6ec7aa1b2c076dcdb25c7b16d"
XF_APISecret = "YzMyYTc4Zjc4OGFkNDYwY2U2MmY3ZjQ0"
# ---------------------------------------------

# MyRobotLab RemoteSpeech 默认保存路径
SAVE_PATH = r"F:\myrobotlab\audioFile\RemoteSpeech\default"
os.makedirs(SAVE_PATH, exist_ok=True)


def log_msg(message):
    """日志打印，带时间戳前缀。"""
    logger.info(message)
    print(message)  # 同时打印到控制台


def xunfei_tts_to_wav(text):
    """调用讯飞 WebSocket TTS 接口"""
    try:
        log_msg("🎤 讯飞TTS 开始合成: {}".format(text))

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

        # 临时存储 PCM 文件
        temp_pcm = tempfile.NamedTemporaryFile(delete=False, suffix='.pcm')
        temp_pcm.close()

        pcm_data = b""
        result = {"success": False, "error": None}

        def on_message(ws, message):
            nonlocal pcm_data
            try:
                data = json.loads(message)
                code = data.get("code", 0)

                if code != 0:
                    result["error"] = "API 错误 {}: {}".format(code, data.get('message', '未知错误'))
                    ws.close()
                    return

                audio_info = data.get("data", {})
                if "audio" in audio_info:
                    chunk = base64.b64decode(audio_info["audio"])
                    pcm_data += chunk
                    if audio_info.get("status") == 2:
                        log_msg("✅ 讯飞音频接收完成")
                        ws.close()

            except Exception as e:
                result["error"] = "处理消息失败: {}".format(e)
                ws.close()

        def on_error(ws, error):
            result["error"] = "WebSocket 错误: {}".format(error)

        def on_close(ws, close_status_code, close_msg):
            if not result["error"] and pcm_data:
                try:
                    with open(temp_pcm.name, "wb") as f:
                        f.write(pcm_data)
                    result["success"] = True
                    log_msg("✅ 讯飞TTS 成功，收到 PCM {} bytes".format(len(pcm_data)))
                except Exception as e:
                    result["error"] = "保存 PCM 失败: {}".format(e)
            elif not pcm_data:
                result["error"] = "未接收到任何音频数据"

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
                log_msg("📤 已发送 TTS 合成请求")
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

        if result["success"]:
            wav_file = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
            wav_file.close()
            try:
                with open(temp_pcm.name, "rb") as pcm_f:
                    raw_pcm = pcm_f.read()
                with wave.open(wav_file.name, 'wb') as wav_f:
                    wav_f.setnchannels(1)
                    wav_f.setsampwidth(2)
                    wav_f.setframerate(16000)
                    wav_f.writeframes(raw_pcm)
                log_msg("✅ WAV 文件已生成: {}".format(wav_file.name))
                return wav_file.name, None
            except Exception as e:
                result["error"] = "PCM 转 WAV 失败: {}".format(e)
            finally:
                try:
                    os.remove(temp_pcm.name)
                except:
                    pass

        return None, result["error"]

    except Exception as e:
        log_msg("❌ 讯飞TTS 异常: {}".format(e))
        return None, str(e)


def create_fallback_wav(text):
    """当讯飞 TTS 合成失败时，生成备用音频"""
    try:
        duration = min(len(text) * 0.15 + 0.5, 3.0)
        sample_rate = 16000
        frequency = 440 + (len(text) % 10) * 20

        total_samples = int(sample_rate * duration)
        pcm_frames = []
        for i in range(total_samples):
            sample = int(12000 * math.sin(2 * math.pi * frequency * i / sample_rate))
            pcm_frames.append(sample.to_bytes(2, byteorder='little', signed=True))

        temp_wav = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
        with wave.open(temp_wav.name, 'wb') as wav_f:
            wav_f.setnchannels(1)
            wav_f.setsampwidth(2)
            wav_f.setframerate(sample_rate)
            wav_f.writeframes(b''.join(pcm_frames))

        temp_wav.close()
        log_msg("🔔 备用音频已生成: {}".format(temp_wav.name))
        return temp_wav.name, None

    except Exception as e:
        log_msg("❌ 备用音频生成失败: {}".format(e))
        return None, str(e)


def extract_text_from_request():
    """超级调试版文本提取"""
    log_msg("=" * 80)
    log_msg("🚨 【超级调试模式】MyRobotLab请求分析")
    log_msg("=" * 80)

    # 打印所有请求信息
    log_msg("🌐 完整URL: {}".format(request.url))
    log_msg("📍 基础URL: {}".format(request.base_url))
    log_msg("🛤️ 路径: {}".format(request.path))
    log_msg("🔧 方法: {}".format(request.method))
    log_msg("🔍 查询字符串原始: '{}'".format(request.query_string.decode()))
    log_msg("📋 GET参数: {}".format(dict(request.args)))

    # 打印所有HTTP头部
    log_msg("📨 HTTP头部:")
    for key, value in request.headers:
        log_msg("   {}: {}".format(key, value))

    if request.method == "POST":
        log_msg("📄 POST表单数据: {}".format(dict(request.form)))
        log_msg("🗂️ JSON数据: {}".format(request.get_json()))

        raw_data = request.get_data()
        if raw_data:
            try:
                decoded_data = raw_data.decode('utf-8')
                log_msg("📃 原始POST数据: '{}'".format(decoded_data))
                log_msg("📏 POST数据长度: {} bytes".format(len(raw_data)))
            except:
                log_msg("📃 原始POST数据: {} bytes (二进制)".format(len(raw_data)))

    # 尝试各种方式提取文本
    text = ""
    found_source = ""

    # 方法1: 检查所有可能的GET参数
    possible_params = ["text", "message", "speech", "content", "q", "query", "t", "msg", "input", "string", "data"]
    for param in possible_params:
        value = request.args.get(param, "")
        if value:
            text = value
            found_source = "GET参数 '{}'".format(param)
            log_msg("✅ 从GET参数 '{}' 找到文本: '{}'".format(param, text))
            break

    # 方法2: 检查POST表单数据
    if not text and request.method == "POST":
        for param in possible_params:
            value = request.form.get(param, "")
            if value:
                text = value
                found_source = "POST表单 '{}'".format(param)
                log_msg("✅ 从POST表单 '{}' 找到文本: '{}'".format(param, text))
                break

    # 方法3: 检查JSON数据
    if not text and request.is_json:
        json_data = request.get_json() or {}
        for param in possible_params:
            if param in json_data:
                text = str(json_data[param])
                found_source = "JSON参数 '{}'".format(param)
                log_msg("✅ 从JSON参数 '{}' 找到文本: '{}'".format(param, text))
                break

    # 方法4: 检查URL路径
    if not text and request.path not in ["/", "/test", "/health", "/status"]:
        path_text = urllib.parse.unquote(request.path.strip("/"))
        if path_text:
            text = path_text
            found_source = "URL路径"
            log_msg("✅ 从URL路径找到文本: '{}'".format(text))

    # 方法5: 检查原始查询字符串
    if not text:
        query_string = request.query_string.decode()
        if query_string and "=" not in query_string:
            decoded_query = urllib.parse.unquote(query_string)
            if decoded_query:
                text = decoded_query
                found_source = "原始查询字符串"
                log_msg("✅ 从原始查询字符串找到文本: '{}'".format(text))

    # 方法6: 检查POST原始数据
    if not text and request.method == "POST":
        raw_data = request.get_data()
        if raw_data:
            try:
                decoded_data = raw_data.decode('utf-8')
                if decoded_data and not decoded_data.startswith('{'):  # 不是JSON
                    text = decoded_data
                    found_source = "POST原始数据"
                    log_msg("✅ 从POST原始数据找到文本: '{}'".format(text))
            except:
                pass

    # 如果还没找到，使用默认文本
    if not text:
        text = "TTS测试"
        found_source = "默认文本"
        log_msg("❌ 未找到任何文本参数，使用默认值")

    log_msg("🎯 最终结果:")
    log_msg("   文本来源: {}".format(found_source))
    log_msg("   提取文本: '{}'".format(text))
    log_msg("   文本长度: {} 字符".format(len(text)))
    log_msg("=" * 80)

    return text


@app.route("/", methods=["GET", "POST"])
@app.route("/<path:path_text>", methods=["GET", "POST"])
def main_tts(path_text=None):
    """主 TTS 接口 - 超级调试版"""
    text = extract_text_from_request()

    wav_file, error = xunfei_tts_to_wav(text)
    if not wav_file:
        log_msg("⚠️ 讯飞合成失败: {}，使用备用合成".format(error))
        wav_file, error = create_fallback_wav(text)

    if wav_file:
        try:
            timestamp = int(time.time())
            save_name = "mrl_tts_{}.wav".format(timestamp)
            save_path = os.path.join(SAVE_PATH, save_name)
            with open(wav_file, "rb") as src, open(save_path, "wb") as dst:
                dst.write(src.read())
            log_msg("💾 副本已保存到 MRL 目录: {}".format(save_name))
        except Exception as e:
            log_msg("⚠️ 保存副本失败: {}".format(e))

        log_msg("📤 返回 WAV 文件: {}".format(wav_file))
        response = send_file(
            wav_file,
            mimetype='audio/wav',
            as_attachment=False,
            download_name="tts_{}.wav".format(int(time.time()))
        )
        response.headers['Content-Type'] = 'audio/wav'
        response.headers['Cache-Control'] = 'no-cache'
        response.headers['Accept-Ranges'] = 'bytes'

        def cleanup():
            time.sleep(5)
            try:
                os.remove(wav_file)
            except:
                pass

        threading.Thread(target=cleanup, daemon=True).start()

        return response
    else:
        log_msg("❌ TTS 完全失败: {}".format(error))
        return "TTS Error: {}".format(error), 500


# 其他路由
@app.route("/translate_tts", methods=["GET", "POST"])
def google_tts_compat():
    return main_tts()


@app.route("/process", methods=["GET", "POST"])
def mary_tts_compat():
    return main_tts()


@app.route("/api/tts", methods=["GET", "POST"])
@app.route("/tts", methods=["GET", "POST"])
@app.route("/speak", methods=["GET", "POST"])
@app.route("/voice", methods=["GET", "POST"])
@app.route("/synthesize", methods=["GET", "POST"])
def api_tts():
    return main_tts()


@app.route("/test", methods=["GET"])
def test():
    return """🎵 MRL兼容讯飞TTS服务 - 超级调试版

✅ 服务运行正常
🔍 调试模式: 已启用
🎤 发音人: xiaoyan (讯飞小燕)
📁 保存路径: {}
⏰ 时间: {}

🧪 测试接口:
• /?text=你好世界 - 直接 TTS
• /api/tts?text=测试 - API 风格

🔧 MRL配置建议:
Type: Piper
URL: http://127.0.0.1:5000/?text={{{{text}}}}&format=wav
Verb: GET
Template: null

🚨 超级调试功能:
• 完整HTTP请求分析
• 所有参数提取尝试
• 详细的错误追踪
• 实时请求监控

专门用于解决MyRobotLab文本传递问题！""".format(
        SAVE_PATH, time.strftime('%Y-%m-%d %H:%M:%S')
    )


if __name__ == "__main__":
    print("🎵 MRL兼容讯飞TTS服务 - 超级调试版")
    print("=" * 60)
    print("🔍 调试模式: 已启用")
    print("端口: 5000")
    print("讯飞 APPID: {}".format(XF_APPID))
    print("发音人: xiaoyan")
    print("保存路径: {}".format(SAVE_PATH))
    print()
    print("🚨 超级调试功能:")
    print("• 完整HTTP请求分析")
    print("• 多种参数提取方式")
    print("• 详细的日志输出")
    print("• 实时监控MyRobotLab请求")
    print("=" * 60)

    try:
        app.run(host="0.0.0.0", port=5000, debug=False)
    except Exception as e:
        print("❌ 启动失败: {}".format(e))