from flask import Flask, request, jsonify
import requests
import json
import logging
from datetime import datetime
import traceback
import urllib.parse
import os
import subprocess
import platform

app = Flask(__name__)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 豆包API配置
DOUBAO_CONFIG = {
    "url": "https://ark.cn-beijing.volces.com/api/v3/chat/completions",
    "api_key": "e2dad4ed-84dd-4a4a-bd99-9991fab5fc05",
    "model": "doubao-1-5-lite-32k-250115"
}

# 音乐播放配置
MUSIC_CONFIG = {
    "guifei_zuijiu_path": r"F:\myrobotlab\object.mp3"  # 替换为实际的音乐文件路径
}


def play_music(file_path):
    """播放音乐文件"""
    try:
        if not os.path.exists(file_path):
            logger.error(f"音乐文件不存在: {file_path}")
            return False

        system = platform.system()
        logger.info(f"在{system}系统上播放音乐: {file_path}")

        if system == "Windows":
            # Windows使用默认程序播放
            os.startfile(file_path)
        elif system == "Darwin":  # macOS
            subprocess.run(["open", file_path])
        else:  # Linux
            subprocess.run(["xdg-open", file_path])

        logger.info(f"成功播放音乐: {file_path}")
        return True

    except Exception as e:
        logger.error(f"播放音乐失败: {str(e)}")
        return False


def check_music_keywords(text):
    """检查是否包含音乐关键词"""
    if not isinstance(text, str):
        return None

    # 检查贵妃醉酒相关关键词
    guifei_keywords = ["贵妃醉酒", "贵妃", "醉酒"]
    chang_keywords = ["唱", "演唱", "来一段", "播放"]

    # 检查是否同时包含"唱"和"贵妃醉酒"相关词汇
    has_chang = any(keyword in text for keyword in chang_keywords)
    has_guifei = any(keyword in text for keyword in guifei_keywords)

    if has_chang and has_guifei:
        logger.info(f"检测到音乐请求: {text}")
        logger.info(f"包含唱相关词: {[k for k in chang_keywords if k in text]}")
        logger.info(f"包含贵妃醉酒相关词: {[k for k in guifei_keywords if k in text]}")
        return "guifei_zuijiu"

    return None


def fix_encoding(text):
    """修复编码问题 - 专门处理MRL chatbot传来的编码问题"""
    if not isinstance(text, str):
        return str(text)

    # 记录原始文本用于调试
    logger.info(f"收到待修复文本: '{text}' (repr: {repr(text)})")

    # 检查是否包含乱码特征 [ä½ æ¯è±åå] 这样的模式
    if 'ä½' in text or 'æ¯' in text or 'è±' in text or 'åå' in text:
        logger.info("检测到疑似UTF-8被错误解析为Latin-1的乱码")
        try:
            # 先将文本编码为Latin-1字节，再解码为UTF-8
            fixed_text = text.encode('latin-1').decode('utf-8')
            logger.info(f"UTF-8乱码修复成功: '{text}' -> '{fixed_text}'")
            return fixed_text
        except Exception as e:
            logger.warning(f"UTF-8乱码修复失败: {e}")

    try:
        # 检查是否已经是正确的UTF-8
        text.encode('utf-8')
        if any('\u4e00' <= char <= '\u9fff' for char in text):
            logger.info("文本已是正确的UTF-8中文")
            return text
        elif all(ord(char) < 128 for char in text):
            logger.info("文本是ASCII字符")
            return text
    except UnicodeEncodeError:
        logger.warning("文本包含无法编码为UTF-8的字符")

    # 尝试各种编码修复方法
    encoding_attempts = [
        # Latin-1 -> UTF-8 (最常见的问题)
        ("latin-1->utf-8", lambda t: t.encode('latin-1').decode('utf-8')),
        # ISO-8859-1 -> UTF-8
        ("iso-8859-1->utf-8", lambda t: t.encode('iso-8859-1').decode('utf-8')),
        # Windows-1252 -> UTF-8
        ("windows-1252->utf-8", lambda t: t.encode('windows-1252').decode('utf-8')),
        # 双重编码问题
        ("double-encoding", lambda t: t.encode('utf-8').decode('utf-8')),
        # URL解码
        ("url-decode", lambda t: urllib.parse.unquote(t)),
        # URL解码 + UTF-8修复
        ("url-decode+utf8", lambda t: urllib.parse.unquote(t).encode('latin-1').decode('utf-8')),
        # 强制UTF-8
        ("force-utf8", lambda t: t.encode('utf-8', errors='ignore').decode('utf-8'))
    ]

    for method_name, attempt in encoding_attempts:
        try:
            fixed_text = attempt(text)
            # 验证修复结果
            if fixed_text != text:
                # 检查是否包含中文字符或者至少是可读的
                if any('\u4e00' <= char <= '\u9fff' for char in fixed_text):
                    logger.info(f"编码修复成功 ({method_name}): '{text}' -> '{fixed_text}'")
                    return fixed_text
                elif len(fixed_text) > 0 and all(ord(char) < 65536 for char in fixed_text):
                    logger.info(f"编码可能修复成功 ({method_name}): '{text}' -> '{fixed_text}'")
                    return fixed_text
        except Exception as e:
            logger.debug(f"编码修复尝试失败 ({method_name}): {e}")
            continue

    # 如果所有方法都失败，返回原文本
    logger.warning(f"编码修复失败，保持原文本: {text}")
    return text


def process_message_content(content):
    """处理消息内容，确保编码正确"""
    if isinstance(content, str):
        # 修复编码
        fixed_content = fix_encoding(content)

        # 记录处理结果
        if fixed_content != content:
            logger.info(f"消息编码已修复: {content} -> {fixed_content}")

        return fixed_content

    return str(content)


def call_doubao_api(messages, temperature=0.7, max_tokens=2000, stream=False):
    """调用豆包API"""
    headers = {
        "Content-Type": "application/json; charset=utf-8",
        "Authorization": f"Bearer {DOUBAO_CONFIG['api_key']}"
    }

    # 处理消息编码
    processed_messages = []
    for msg in messages:
        processed_msg = msg.copy()
        if 'content' in processed_msg:
            processed_msg['content'] = process_message_content(processed_msg['content'])
        processed_messages.append(processed_msg)

    payload = {
        "model": DOUBAO_CONFIG["model"],
        "messages": processed_messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "stream": stream
    }

    try:
        logger.info(f"调用豆包API，消息数量: {len(processed_messages)}")
        for i, msg in enumerate(processed_messages):
            logger.info(f"消息 {i + 1}: {msg.get('role', 'unknown')} - {msg.get('content', '')[:50]}...")

        response = requests.post(
            DOUBAO_CONFIG["url"],
            headers=headers,
            json=payload,
            timeout=30,
            verify=True
        )

        if response.status_code == 200:
            result = response.json()
            logger.info("豆包API调用成功")
            logger.debug(f"豆包响应: {result}")
            return result
        else:
            logger.error(f"豆包API错误: {response.status_code} - {response.text}")
            return None

    except Exception as e:
        logger.error(f"调用豆包API异常: {str(e)}")
        logger.error(traceback.format_exc())
        return None


@app.before_request
def log_request():
    """记录所有请求信息，帮助调试编码问题"""
    logger.info(f"收到请求: {request.method} {request.url}")
    logger.info(f"Content-Type: {request.headers.get('Content-Type', 'Not set')}")
    logger.info(f"User-Agent: {request.headers.get('User-Agent', 'Not set')}")

    if request.is_json:
        try:
            data = request.get_json()
            logger.info(f"JSON数据: {json.dumps(data, ensure_ascii=False)[:200]}...")
        except Exception as e:
            logger.warning(f"无法解析JSON数据: {e}")

    if hasattr(request, 'data') and request.data:
        try:
            raw_data = request.data.decode('utf-8')
            logger.info(f"原始数据: {raw_data[:200]}...")
        except Exception as e:
            logger.warning(f"无法解码原始数据: {e}")
            try:
                # 尝试其他编码
                raw_data = request.data.decode('latin-1')
                logger.info(f"Latin-1原始数据: {raw_data[:200]}...")
            except Exception as e2:
                logger.warning(f"无法以Latin-1解码原始数据: {e2}")

    # 尝试直接获取请求体作为文本
    try:
        raw_text = request.get_data(as_text=True)
        if raw_text:
            logger.info(f"请求体文本: {raw_text[:200]}...")
    except Exception as e:
        logger.warning(f"无法获取请求体文本: {e}")


@app.route('/api/generate', methods=['POST'])
def ollama_generate():
    """模拟Ollama的generate接口"""
    try:
        # 尝试多种方式获取JSON数据
        data = None

        # 方法1: 标准JSON解析
        try:
            data = request.get_json()
        except Exception as e:
            logger.warning(f"标准JSON解析失败: {e}")

        # 方法2: 强制UTF-8解析
        if data is None:
            try:
                raw_data = request.get_data(as_text=True)
                data = json.loads(raw_data)
            except Exception as e:
                logger.warning(f"UTF-8 JSON解析失败: {e}")
        # 方法3: 从表单数据解析
        if data is None and request.form:
            try:
                # 可能是通过表单发送的JSON
                for key, value in request.form.items():
                    try:
                        data = json.loads(value)
                        break
                    except:
                        continue
            except Exception as e:
                logger.warning(f"表单JSON解析失败: {e}")

        if data is None:
            return jsonify({"error": "无法解析请求数据"}), 400

        logger.info("收到Ollama generate请求")

        prompt = data.get('prompt', '')
        if not prompt:
            return jsonify({"error": "缺少prompt参数"}), 400

        # 处理prompt编码
        prompt = process_message_content(prompt)

        # 🎵 检查是否为音乐请求
        music_type = check_music_keywords(prompt)
        if music_type:
            logger.info(f"检测到音乐请求: {music_type}")

            # 播放音乐
            if music_type == "guifei_zuijiu":
                success = play_music(MUSIC_CONFIG["guifei_zuijiu_path"])
                if success:
                    response_content = "好的，为您播放音乐！"
                    logger.info(f"音乐播放成功，回复: {response_content}")
                else:
                    response_content = "抱歉，音乐文件播放失败，请检查文件路径。"
                    logger.error("音乐播放失败")
            else:
                response_content = "音乐播放功能暂时不可用。"

            # 返回音乐响应，不调用大模型
            model = data.get('model', DOUBAO_CONFIG['model'])
            ollama_response = {
                "model": model,
                "created_at": datetime.now().isoformat() + "Z",
                "response": response_content,
                "done": True,
                "context": [],
                "total_duration": 500000000,  # 更短的响应时间
                "load_duration": 50000000,
                "prompt_eval_count": len(prompt.split()),
                "prompt_eval_duration": 100000000,
                "eval_count": len(response_content.split()),
                "eval_duration": 350000000
            }

            logger.info("返回音乐播放响应")
            response = app.response_class(
                response=json.dumps(ollama_response, ensure_ascii=False),
                status=200,
                mimetype='application/json; charset=utf-8'
            )
            return response

        # 普通对话请求，调用大模型
        model = data.get('model', DOUBAO_CONFIG['model'])
        temperature = data.get('options', {}).get('temperature', 0.7)

        # 转换为chat格式
        messages = [{"role": "user", "content": prompt}]

        # 调用豆包API
        doubao_response = call_doubao_api(messages, temperature)

        if doubao_response and 'choices' in doubao_response:
            content = doubao_response['choices'][0]['message']['content']

            # 返回Ollama格式的响应
            ollama_response = {
                "model": model,
                "created_at": datetime.now().isoformat() + "Z",
                "response": content,
                "done": True,
                "context": [],
                "total_duration": 1000000000,
                "load_duration": 100000000,
                "prompt_eval_count": len(prompt.split()),
                "prompt_eval_duration": 200000000,
                "eval_count": len(content.split()),
                "eval_duration": 700000000
            }

            logger.info("成功返回generate响应")
            response = app.response_class(
                response=json.dumps(ollama_response, ensure_ascii=False),
                status=200,
                mimetype='application/json; charset=utf-8'
            )
            return response
        else:
            error_msg = "豆包API调用失败"
            logger.error(error_msg)
            return jsonify({"error": error_msg}), 500

    except Exception as e:
        error_msg = f"处理generate请求异常: {str(e)}"
        logger.error(error_msg)
        logger.error(traceback.format_exc())
        return jsonify({"error": error_msg}), 500


@app.route('/api/chat', methods=['POST'])
def ollama_chat():
    """模拟Ollama的chat接口"""
    try:
        # 尝试多种方式获取JSON数据
        data = None

        # 方法1: 标准JSON解析
        try:
            data = request.get_json()
        except Exception as e:
            logger.warning(f"标准JSON解析失败: {e}")

        # 方法2: 强制UTF-8解析
        if data is None:
            try:
                raw_data = request.get_data(as_text=True)
                data = json.loads(raw_data)
            except Exception as e:
                logger.warning(f"UTF-8 JSON解析失败: {e}")

        if data is None:
            return jsonify({"error": "无法解析请求数据"}), 400

        logger.info("收到Ollama chat请求")

        messages = data.get('messages', [])
        model = data.get('model', DOUBAO_CONFIG['model'])
        temperature = data.get('options', {}).get('temperature', 0.7)

        if not messages:
            return jsonify({"error": "缺少messages参数"}), 400

        # 获取最后一条用户消息检查音乐关键词
        last_user_message = ""
        for msg in reversed(messages):
            if msg.get('role') == 'user':
                last_user_message = process_message_content(msg.get('content', ''))
                break

        # 🎵 检查是否为音乐请求
        music_type = check_music_keywords(last_user_message)
        if music_type:
            logger.info(f"检测到音乐请求: {music_type}")

            # 播放音乐
            if music_type == "guifei_zuijiu":
                success = play_music(MUSIC_CONFIG["guifei_zuijiu_path"])
                if success:
                    response_content = "好的，为您播放音乐！"
                    logger.info(f"音乐播放成功，回复: {response_content}")
                else:
                    response_content = "抱歉，音乐文件播放失败，请检查文件路径。"
                    logger.error("音乐播放失败")
            else:
                response_content = "音乐播放功能暂时不可用。"

            # 返回音乐响应，不调用大模型
            ollama_response = {
                "model": model,
                "created_at": datetime.now().isoformat() + "Z",
                "message": {
                    "role": "assistant",
                    "content": response_content
                },
                "done": True,
                "total_duration": 500000000,
                "load_duration": 50000000,
                "prompt_eval_count": len(last_user_message.split()),
                "prompt_eval_duration": 100000000,
                "eval_count": len(response_content.split()),
                "eval_duration": 350000000
            }

            logger.info("返回音乐播放响应")
            response = app.response_class(
                response=json.dumps(ollama_response, ensure_ascii=False),
                status=200,
                mimetype='application/json; charset=utf-8'
            )
            return response

        # 普通对话请求，调用大模型
        doubao_response = call_doubao_api(messages, temperature)

        if doubao_response and 'choices' in doubao_response:
            content = doubao_response['choices'][0]['message']['content']

            # 返回Ollama格式的响应
            ollama_response = {
                "model": model,
                "created_at": datetime.now().isoformat() + "Z",
                "message": {
                    "role": "assistant",
                    "content": content
                },
                "done": True,
                "total_duration": 1000000000,
                "load_duration": 100000000,
                "prompt_eval_count": sum(len(msg.get('content', '').split()) for msg in messages),
                "prompt_eval_duration": 200000000,
                "eval_count": len(content.split()),
                "eval_duration": 700000000
            }

            logger.info("成功返回chat响应")
            response = app.response_class(
                response=json.dumps(ollama_response, ensure_ascii=False),
                status=200,
                mimetype='application/json; charset=utf-8'
            )
            return response
        else:
            error_msg = "豆包API调用失败"
            logger.error(error_msg)
            return jsonify({"error": error_msg}), 500

    except Exception as e:
        error_msg = f"处理chat请求异常: {str(e)}"
        logger.error(error_msg)
        logger.error(traceback.format_exc())
        return jsonify({"error": error_msg}), 500


@app.route('/api/tags', methods=['GET'])
def list_models():
    """模拟Ollama的模型列表接口"""
    logger.info("收到模型列表请求")
    return jsonify({
        "models": [
            {
                "name": DOUBAO_CONFIG['model'],
                "size": 4000000000,
                "digest": "sha256:doubao1234567890abcdef",
                "details": {
                    "parent_model": "",
                    "format": "gguf",
                    "family": "doubao",
                    "families": ["doubao"],
                    "parameter_size": "32B",
                    "quantization_level": "Q4_0"
                },
                "expires_at": "0001-01-01T00:00:00Z",
                "size_vram": 0,
                "modified_at": datetime.now().isoformat() + "Z"
            }
        ]
    })


@app.route('/api/show', methods=['POST'])
def show_model():
    """模拟Ollama的模型信息接口"""
    try:
        data = request.get_json()
        model_name = data.get('name', DOUBAO_CONFIG['model'])
        logger.info(f"收到模型信息请求: {model_name}")

        return jsonify({
            "license": "豆包API代理服务",
            "modelfile": f"# Modelfile generated by doubao-proxy\n\nFROM {model_name}\n\nPARAMETER temperature 0.7\nPARAMETER top_p 0.9\n",
            "parameters": "temperature                0.7\ntop_p                      0.9\n",
            "template": "{{ .System }}{{ .Prompt }}",
            "details": {
                "parent_model": "",
                "format": "gguf",
                "family": "doubao",
                "families": ["doubao"],
                "parameter_size": "32B",
                "quantization_level": "Q4_0"
            },
            "model_info": {
                "general.architecture": "doubao",
                "general.file_type": 2,
                "general.parameter_count": 32000000000,
                "general.quantization_version": 2
            },
            "modified_at": datetime.now().isoformat() + "Z"
        })

    except Exception as e:
        logger.error(f"处理show请求异常: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/pull', methods=['POST'])
def pull_model():
    """模拟Ollama的模型拉取接口"""
    try:
        data = request.get_json()
        model_name = data.get('name', DOUBAO_CONFIG['model'])
        logger.info(f"收到模型拉取请求: {model_name}")

        # 模拟拉取完成
        return jsonify({
            "status": "success",
            "digest": "sha256:doubao1234567890abcdef",
            "total": 4000000000,
            "completed": 4000000000
        })

    except Exception as e:
        logger.error(f"处理pull请求异常: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route('/health', methods=['GET'])
def health():
    """健康检查"""
    return jsonify({
        "status": "healthy",
        "service": "doubao-ollama-proxy",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat(),
        "doubao_model": DOUBAO_CONFIG['model']
    })


@app.route('/', methods=['GET'])
def root():
    """根路径信息"""
    return jsonify({
        "message": "豆包-Ollama兼容代理服务器",
        "version": "1.0.0",
        "description": "将Ollama API调用转换为豆包API调用",
        "endpoints": {
            "chat": "/api/chat",
            "generate": "/api/generate",
            "models": "/api/tags",
            "show": "/api/show",
            "pull": "/api/pull",
            "health": "/health"
        },
        "target_api": "豆包API",
        "model": DOUBAO_CONFIG['model']
    })


@app.route('/api/version', methods=['GET'])
def version():
    """版本信息"""
    return jsonify({
        "version": "0.1.48"  # 模拟Ollama版本
    })


@app.errorhandler(404)
def not_found(error):
    """404处理"""
    logger.warning(f"404请求: {request.url}")
    return jsonify({
        "error": "接口不存在",
        "available_endpoints": [
            "/api/chat",
            "/api/generate",
            "/api/tags",
            "/api/show",
            "/api/pull",
            "/health",
            "/"
        ]
    }), 404


@app.errorhandler(500)
def internal_error(error):
    """500处理"""
    logger.error(f"内部服务器错误: {str(error)}")
    return jsonify({
        "error": "内部服务器错误",
        "message": str(error)
    }), 500


def test_doubao_connection():
    """启动时测试豆包连接"""
    logger.info("测试豆包API连接...")
    test_messages = [{"role": "user", "content": "你好"}]
    result = call_doubao_api(test_messages)

    if result:
        logger.info("豆包API连接测试成功")
        return True
    else:
        logger.error("豆包API连接测试失败")
        return False


if __name__ == '__main__':
    print("=" * 60)
    print("🚀 豆包-Ollama兼容代理服务器")
    print("=" * 60)
    print(f"📡 服务地址: http://localhost:11434")
    print(f"🔄 豆包模型: {DOUBAO_CONFIG['model']}")
    print(f"🎯 目标API: {DOUBAO_CONFIG['url']}")
    print()
    print("📋 InMoov2配置:")
    print("   - 选择: Ollama")
    print("   - URL: http://localhost:11434")
    print(f"   - Model: {DOUBAO_CONFIG['model']}")
    print("   - API Key: 留空")
    print()
    print("🔗 可用接口:")
    print("   - /api/chat        (聊天)")
    print("   - /api/generate    (生成)")
    print("   - /api/tags        (模型列表)")
    print("   - /api/show        (模型信息)")
    print("   - /health          (健康检查)")
    print()
    print("🎵 音乐功能:")
    print("   - 检测关键词: '唱' + '贵妃醉酒'")
    print("   - 音乐文件: F:\\guyi\\object.mp3")
    print("   - 触发示例: '唱贵妃醉酒', '来一段贵妃醉酒'")
    print("   - 不调用大模型，直接播放音乐")
    print()

    # 测试豆包连接
    if test_doubao_connection():
        print("✅ 豆包API连接正常")
    else:
        print("❌ 豆包API连接失败，请检查网络和API密钥")
        print("   继续启动服务器，可能是网络临时问题...")

    print()
    print("🚀 正在启动服务器...")
    print("   按 Ctrl+C 停止服务")
    print("=" * 60)

    try:
        app.run(
            host='0.0.0.0',
            port=11434,
            debug=False,
            threaded=True,
            use_reloader=False
        )
    except KeyboardInterrupt:
        print("\n👋 服务器已停止")
    except Exception as e:
        print(f"\n❌ 服务器启动失败: {str(e)}")
        print("可能的原因:")
        print("1. 端口11434被占用")
        print("2. 权限不足")
        print("3. 防火墙阻止")
        print("\n解决方法:")
        print("1. 检查端口占用: netstat -an | grep 11434")
        print("2. 尝试其他端口: 修改代码中的port=11434")
        print("3. 以管理员权限运行")