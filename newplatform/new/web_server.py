from flask import Flask, render_template, request, jsonify
import os
import threading
import time
# 导入 mouth_control 的核心功能模块
from analysis_sound import AudioAnalyzer
from tts_integration import TTSIntegration
from ai import DoubaoAI
from speech_recognition import XunfeiASR
import logging
import socket
client_socket = None

app = Flask(__name__, template_folder=os.path.join(os.path.dirname(__file__), "templates"))

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

audio_analyzer = AudioAnalyzer()
tts_integration = TTSIntegration()
doubao_ai = DoubaoAI()
asr = XunfeiASR()
is_playing = False

@app.route('/')
def index():
    # 欢迎来到能量满满的机器人主页！
    return render_template('index.html')

@app.route('/api/ai/chat', methods=['POST'])
def ai_chat():
    # 跟AI聊聊天，看看它今天心情如何！
    try:
        data = request.json
        message = data.get('message', '').strip()
        if not message:
            return jsonify({'success': False, 'error': '请输入消息'})
        ai_response = doubao_ai.send_message(message)
        return jsonify({'success': True, 'response': ai_response})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/ai/speak', methods=['POST'])
def ai_speak():
    # 让AI开口说话，声音也是能量！
    global is_playing
    try:
        data = request.json
        message = data.get('message', '').strip()
        voice_name = data.get('voice_name', 'x4_yezi')
        if not message:
            return jsonify({'success': False, 'error': '请输入消息'})
        if is_playing:
            return jsonify({'success': False, 'error': '正在播放中'})
        ai_response = doubao_ai.send_message(message)
        if not ai_response or ai_response.startswith('抱歉'):
            return jsonify({'success': False, 'error': 'AI回复失败'})
        audio_file = tts_integration.xunfei_tts(
            ai_response,
            app_id="54bbe675",
            api_key="4d0929a6ec7aa1b2c076dcdb25c7b16d",
            api_secret="YzMyYTc4Zjc4OGFkNDYwY2U2MmY3ZjQ0",
            voice_name=voice_name
        )
        if not audio_file:
            return jsonify({'success': True, 'response': ai_response, 'audio_generated': False, 'error': 'TTS生成失败'})
        def play_thread():
            global is_playing
            is_playing = True
            try:
                # 如果串口已连接则控制表情，否则只播放语音
                if audio_analyzer.is_connected:
                    audio_analyzer.play_with_mouth_control(audio_file)
                else:
                    import pygame
                    pygame.mixer.init()
                    pygame.mixer.music.load(audio_file)
                    pygame.mixer.music.play()
                    while pygame.mixer.music.get_busy():
                        pygame.time.wait(100)
                    pygame.mixer.quit()
            except Exception as e:
                print(f"播放错误: {e}")
            finally:
                is_playing = False
                try:
                    os.remove(audio_file)
                except:
                    pass
        threading.Thread(target=play_thread, daemon=True).start()
        return jsonify({'success': True, 'response': ai_response, 'audio_generated': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/asr/recognize', methods=['POST'])
def asr_recognize():
    # 语音识别，听你说话就是我的超能力！
    try:
        if 'audio' not in request.files:
            return jsonify({'success': False, 'error': '未上传音频文件'})
        audio_file = request.files['audio']
        temp_path = os.path.join(asr.temp_dir, f"asr_{int(time.time())}.wav")
        audio_file.save(temp_path)
        text, error = asr.recognize_from_file(temp_path)
        try:
            os.remove(temp_path)
        except:
            pass
        if text:
            return jsonify({'success': True, 'text': text})
        else:
            return jsonify({'success': False, 'error': error or "识别失败"})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/servo', methods=['POST'])
def set_servo():
    # 控制舵机，动起来才有活力！
    try:
        data = request.json
        part = data.get('part')
        channel = data.get('channel')
        angle = data.get('angle')
        # 只有舵机控制需要串口连接
        if not audio_analyzer.is_connected:
            return jsonify({'success': False, 'error': '设备未连接'})
        if channel is not None:
            success = audio_analyzer.set_servo_angle(int(channel), int(angle))
        elif part:
            success = audio_analyzer.set_face_part_angle(part, int(angle))
        else:
            return jsonify({'success': False, 'error': '参数错误'})
        if success:
            return jsonify({'success': True, 'message': f'舵机已设置'})
        else:
            return jsonify({'success': False, 'error': '设置失败'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/connect', methods=['POST'])
def connect():
    """串口连接，能量通道开启！"""
    try:
        data = request.json
        port = data.get('port')
        baud_rate = data.get('baud_rate', 115200)
        
        if not port:
            return jsonify({'success': False, 'error': '请选择串口'})
        
        logging.info(f"尝试连接到串口: {port}, 波特率: {baud_rate}")
        
        # 检查串口是否存在
        available_ports = audio_analyzer.get_available_ports()
        logging.info(f"可用串口列表: {available_ports}")
        
        if port not in available_ports:
            return jsonify({
                'success': False, 
                'error': f'串口 {port} 不存在，可用串口: {available_ports}'
            })
        
        # 详细的连接过程
        try:
            # 先断开现有连接
            if hasattr(audio_analyzer, 'is_connected') and audio_analyzer.is_connected:
                audio_analyzer.disconnect_arduino()
                time.sleep(1)
            
            audio_analyzer.com_port = port
            audio_analyzer.baud_rate = baud_rate
            
            logging.info(f"开始连接Arduino...")
            success = audio_analyzer.connect_arduino()
            
            if success:
                logging.info(f"Arduino连接成功: {port}")
                return jsonify({
                    'success': True, 
                    'message': f'已连接到 {port}',
                    'port': port,
                    'baud_rate': baud_rate
                })
            else:
                logging.error(f"Arduino连接失败: {port}")
                return jsonify({
                    'success': False, 
                    'error': '连接失败，请检查:\n1. Arduino是否正确连接到USB端口\n2. 是否烧录了正确的Arduino代码\n3. 串口是否被其他程序占用\n4. 波特率是否匹配(115200)',
                    'debug_info': {
                        'port': port,
                        'baud_rate': baud_rate,
                        'available_ports': available_ports
                    }
                })
                
        except Exception as connect_error:
            logging.error(f"连接过程异常: {connect_error}")
            return jsonify({
                'success': False, 
                'error': f'连接异常: {str(connect_error)}',
                'debug_info': {
                    'error_type': type(connect_error).__name__,
                    'port': port,
                    'baud_rate': baud_rate
                }
            })
            
    except Exception as e:
        logging.error(f"连接API异常: {e}")
        return jsonify({'success': False, 'error': f'API异常: {str(e)}'})

# 添加Arduino连接调试接口
@app.route('/api/arduino/debug', methods=['POST'])
def debug_arduino_connection():
    """Arduino连接调试，排查小怪兽！"""
    try:
        data = request.json
        port = data.get('port')
        
        if not port:
            return jsonify({'success': False, 'error': '请指定串口'})
        
        debug_info = {
            'port': port,
            'steps': [],
            'success': False
        }
        
        # 步骤1: 检查串口是否存在
        available_ports = audio_analyzer.get_available_ports()
        debug_info['available_ports'] = available_ports
        
        if port not in available_ports:
            debug_info['steps'].append({
                'step': '检查串口存在性',
                'status': 'FAILED',
                'message': f'串口 {port} 不存在'
            })
            debug_info['suggestions'] = [
                '1. 请重新插拔Arduino USB线',
                '2. 检查Arduino是否被系统识别',
                '3. 尝试重启Arduino IDE或重新安装驱动'
            ]
            return jsonify(debug_info)
        else:
            debug_info['steps'].append({
                'step': '检查串口存在性',
                'status': 'PASSED',
                'message': f'串口 {port} 存在'
            })
        
        # 步骤2: 尝试打开串口
        try:
            import serial
            test_serial = serial.Serial(
                port=port,
                baudrate=115200,
                timeout=2
            )
            debug_info['steps'].append({
                'step': '打开串口',
                'status': 'PASSED',
                'message': f'成功打开串口 {port}'
            })
            
            # 步骤3: 等待Arduino初始化
            time.sleep(3)
            
            # 步骤4: 清空缓冲区
            test_serial.flushInput()
            test_serial.flushOutput()
            
            # 步骤5: 读取启动消息
            startup_messages = []
            start_time = time.time()
            while time.time() - start_time < 3:
                if test_serial.in_waiting > 0:
                    try:
                        line = test_serial.readline().decode().strip()
                        if line:
                            startup_messages.append(line)
                    except:
                        pass
                time.sleep(0.1)
            
            debug_info['startup_messages'] = startup_messages
            
            if startup_messages:
                debug_info['steps'].append({
                    'step': '读取Arduino启动消息',
                    'status': 'PASSED',
                    'message': f'收到 {len(startup_messages)} 条消息: {startup_messages}'
                })
            else:
                debug_info['steps'].append({
                    'step': '读取Arduino启动消息',
                    'status': 'WARNING',
                    'message': '未收到Arduino启动消息，可能Arduino代码未正确烧录'
                })
            
            # 步骤6: 测试命令响应
            test_serial.write(b'CENTER\n')
            test_serial.flush()
            time.sleep(1)
            
            response_messages = []
            start_time = time.time()
            while time.time() - start_time < 2:
                if test_serial.in_waiting > 0:
                    try:
                        line = test_serial.readline().decode().strip()
                        if line:
                            response_messages.append(line)
                    except:
                        pass
                time.sleep(0.1)
            
            debug_info['response_messages'] = response_messages
            
            if response_messages:
                debug_info['steps'].append({
                    'step': '测试命令响应',
                    'status': 'PASSED',
                    'message': f'Arduino响应: {response_messages}'
                })
                debug_info['success'] = True
            else:
                debug_info['steps'].append({
                    'step': '测试命令响应',
                    'status': 'FAILED',
                    'message': 'Arduino未响应CENTER命令，请检查代码是否正确烧录'
                })
            
            test_serial.close()
            
        except Exception as serial_error:
            debug_info['steps'].append({
                'step': '打开串口',
                'status': 'FAILED',
                'message': f'串口打开失败: {str(serial_error)}'
            })
        
        # 添加解决建议
        if not debug_info['success']:
            debug_info['suggestions'] = [
                '1. 确认Arduino已正确连接到USB端口',
                '2. 确认已烧录提供的Arduino代码 (arduino_pca9685.ino)',
                '3. 检查串口是否被其他程序(如Arduino IDE串口监视器)占用',
                '4. 尝试重新插拔Arduino USB线',
                '5. 检查Arduino电源指示灯是否亮起',
                '6. 在Arduino IDE中打开串口监视器，设置115200波特率，看是否有输出'
            ]
        
        return jsonify(debug_info)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'调试过程异常: {str(e)}'
        })

@app.route('/api/ports')
def get_ports():
    """串口列表大集合，谁在线我都能看到！"""
    try:
        ports = audio_analyzer.get_available_ports()
        return jsonify({'success': True, 'ports': ports})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

# mouthcontrol2 新增：高级面部表情控制接口
@app.route('/api/face/advanced', methods=['POST'])
def advanced_face_control():
    """
    高级面部表情控制，批量发号施令，表情管理大师！
    """
    try:
        data = request.json
        actions = data.get('actions', [])  # [{"part": "LEFT_EYEBROW", "angle": 120}, ...]
        if not audio_analyzer.is_connected:
            return jsonify({'success': False, 'error': '设备未连接'})
        for act in actions:
            part = act.get('part')
            angle = act.get('angle')
            audio_analyzer.set_face_part_angle(part, angle)
        return jsonify({'success': True, 'message': '批量设置完成'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

# 添加缺失的API路由
robot_active = False
speaking_status = False

@app.route('/api/start', methods=['POST'])
def start_robot():
    """机器人启动，能量满格，Ready Go！"""
    global robot_active
    try:
        robot_active = True
        return jsonify({
            'success': True,
            'message': '机器人已启动'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/stop', methods=['POST'])
def stop_robot():
    """机器人休息，能量存储，下次再战！"""
    global robot_active
    try:
        robot_active = False
        return jsonify({
            'success': True,
            'message': '机器人已停止'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.errorhandler(404)
def not_found(error):
    """404啦，接口迷路了，快带它回家！"""
    return jsonify({'success': False, 'error': '接口不存在'}), 404

@app.errorhandler(500)
def internal_error(error):
    """服务器小宇宙爆发了，稍等我修修！"""
    return jsonify({'success': False, 'error': '服务器内部错误'}), 500

@app.route('/api/status')
def get_status():
    """机器人状态播报，随时掌握我的能量！"""
    global robot_active, speaking_status, is_playing
    try:
        # 检查ASR是否可用
        microphone_available = True
        if hasattr(asr, 'test_microphone'):
            try:
                microphone_available = asr.test_microphone()
            except:
                microphone_available = False
        
        # 检查录音状态
        recording_status = False
        if hasattr(asr, 'is_recording_active'):
            try:
                recording_status = asr.is_recording_active()
            except:
                recording_status = False
        
        return jsonify({
            'robot_active': robot_active,
            'speaking': is_playing or speaking_status,
            'recording': recording_status,
            'microphone_available': microphone_available,
            'arduino_connected': audio_analyzer.is_connected if hasattr(audio_analyzer, 'is_connected') else False
        })
    except Exception as e:
        logging.error(f"状态查询错误: {e}")
        return jsonify({
            'robot_active': False,
            'speaking': False,
            'recording': False,
            'microphone_available': False,
            'arduino_connected': False,
            'error': str(e)
        })

@app.route('/api/voice_recognition', methods=['POST'])
def voice_recognition():
    """语音识别，听你说话就是我的超能力！"""
    try:
        data = request.json
        max_duration = data.get('duration', 5)
        
        logging.info(f"开始语音识别，最大时长: {max_duration}秒")
        
        # 检查ASR是否有required method
        if not hasattr(asr, 'recognize_speech_with_stop'):
            return jsonify({
                'success': False,
                'error': 'ASR模块不支持语音识别功能'
            })
        
        # 使用ASR进行语音识别
        text, error = asr.recognize_speech_with_stop(max_duration)
        
        if error:
            logging.warning(f"语音识别失败: {error}")
            return jsonify({
                'success': False,
                'error': error
            })
        
        if text:
            logging.info(f"语音识别成功: {text}")
            return jsonify({
                'success': True,
                'text': text.strip()
            })
        else:
            return jsonify({
                'success': False,
                'error': '未识别到语音内容'
            })
            
    except Exception as e:
        logging.error(f"语音识别异常: {e}")
        return jsonify({
            'success': False,
            'error': f'语音识别异常: {str(e)}'
        })

@app.route('/api/chat', methods=['POST'])
def chat_with_ai():
    """和AI聊聊，智慧碰撞火花！"""
    global speaking_status
    try:
        data = request.json
        message = data.get('message', '').strip()
        
        if not message:
            return jsonify({
                'success': False,
                'error': '消息不能为空'
            })
        
        if not robot_active:
            return jsonify({
                'success': False,
                'error': '机器人未启动'
            })
        
        logging.info(f"用户消息: {message}")
        
        # 获取AI回复
        ai_response = doubao_ai.send_message(message)
        
        if ai_response:
            logging.info(f"AI回复: {ai_response}")
            
            # 启动语音合成和播放
            def speak_and_play():
                global speaking_status, is_playing
                speaking_status = True
                is_playing = True
                try:
                    logging.info("=== 开始语音合成流程 ===")
                    
                    # 生成临时音频文件
                    import tempfile
                    temp_dir = tempfile.gettempdir()
                    timestamp = int(time.time())
                    audio_filename = f"chat_audio_{timestamp}.mp3"
                    audio_path = os.path.join(temp_dir, audio_filename)
                    
                    # 使用改进的TTS生成
                    audio_file = generate_mp3_tts(
                        text=ai_response,
                        save_path=audio_path,
                        app_id="54bbe675",
                        api_key="4d0929a6ec7aa1b2c076dcdb25c7b16d",
                        api_secret="YzMyYTc4Zjc4OGFkNDYwY2U2MmY3ZjQ0"
                    )
                    
                    if audio_file and os.path.exists(audio_file):
                        file_size = os.path.getsize(audio_file)
                        logging.info(f"语音合成成功，文件: {audio_file}, 大小: {file_size} bytes")
                        
                        if file_size > 1000:
                            # 播放音频
                            played_successfully = False
                            
                            # 方法1: pygame播放MP3
                            try:
                                import pygame
                                logging.info("使用pygame播放MP3...")
                                
                                pygame.mixer.quit()
                                pygame.mixer.pre_init(frequency=22050, size=-16, channels=2, buffer=1024)
                                pygame.mixer.init()
                                
                                pygame.mixer.music.load(audio_file)
                                pygame.mixer.music.set_volume(1.0)
                                pygame.mixer.music.play()
                                
                                while pygame.mixer.music.get_busy():
                                    pygame.time.wait(100)
                                
                                pygame.mixer.quit()
                                logging.info("pygame播放完成")
                                played_successfully = True
                                
                            except Exception as pygame_error:
                                logging.error(f"pygame播放失败: {pygame_error}")
                                
                                # 方法2: winsound播放
                                try:
                                    import winsound
                                    logging.info("使用winsound播放...")
                                    winsound.PlaySound(audio_file, winsound.SND_FILENAME)
                                    logging.info("winsound播放完成")
                                    played_successfully = True
                                    
                                except Exception as winsound_error:
                                    logging.error(f"winsound播放失败: {winsound_error}")
                                    
                                    # 方法3: 系统默认播放器
                                    try:
                                        import subprocess
                                        import platform
                                        
                                        if platform.system() == "Windows":
                                            logging.info("使用系统默认播放器...")
                                            subprocess.run([
                                                "cmd", "/c", f"start \"\" \"{audio_file}\""
                                            ], timeout=10)
                                            time.sleep(2)  # 等待播放开始
                                            logging.info("系统播放器已启动")
                                            played_successfully = True
                                            
                                    except Exception as sys_error:
                                        logging.error(f"系统播放器失败: {sys_error}")
                            
                            if not played_successfully:
                                logging.error("所有播放方法都失败了！")
                        else:
                            logging.error(f"音频文件过小: {file_size} bytes")
                        
                        # 延迟删除临时文件
                        try:
                            time.sleep(1)  # 等待播放完成
                            os.remove(audio_file)
                            logging.info("临时文件已清理")
                        except:
                            logging.warning("临时文件清理失败")
                    else:
                        logging.error("语音合成失败")
                        
                except Exception as e:
                    logging.error(f"语音播放错误: {e}")
                    import traceback
                    logging.error(f"详细错误: {traceback.format_exc()}")
                finally:
                    speaking_status = False
                    is_playing = False
                    logging.info("=== 语音播放线程结束 ===")
            
            # 异步执行语音播放
            threading.Thread(target=speak_and_play, daemon=True).start()
            
            return jsonify({
                'success': True,
                'response': ai_response,
                'speaking': True
            })
        else:
            return jsonify({
                'success': False,
                'error': 'AI回复失败'
            })
            
    except Exception as e:
        logging.error(f"聊天接口异常: {e}")
        return jsonify({
            'success': False,
            'error': f'聊天服务异常: {str(e)}'
        })

@app.route('/api/test_microphone', methods=['POST'])
def test_microphone():
    """麦克风测试，谁在线我都能听见！"""
    try:
        # 检查ASR模块是否有测试方法
        if hasattr(asr, 'test_microphone'):
            test_result = asr.test_microphone()
        else:
            # 简单检查模块是否可用
            test_result = hasattr(asr, 'recognize_speech_with_stop')
        
        if test_result:
            return jsonify({
                'success': True,
                'message': '麦克风测试成功'
            })
        else:
            return jsonify({
                'success': False,
                'error': '麦克风测试失败'
            })
    except Exception as e:
        logging.error(f"麦克风测试异常: {e}")
        return jsonify({
            'success': False,
            'error': f'麦克风测试异常: {str(e)}'
        })

# 新增：专门的TTS测试接口，用于调试语音合成问题
@app.route('/api/debug_tts', methods=['POST'])
def debug_tts():
    """TTS调试，语音合成小能手！"""
    try:
        data = request.json
        test_text = data.get('text', '你好，这是语音测试')
        
        logging.info(f"=== TTS调试开始 ===")
        logging.info(f"测试文本: {test_text}")
        
        # 检查TTS模块是否存在
        if not hasattr(tts_integration, 'xunfei_tts'):
            return jsonify({
                'success': False,
                'error': 'TTS模块未找到xunfei_tts方法',
                'debug_info': 'TTS integration模块问题'
            })
        
        # 检查API密钥配置
        api_config = {
            'app_id': "54bbe675",
            'api_key': "4d0929a6ec7aa1b2c076dcdb25c7b16d", 
            'api_secret': "YzMyYTc4Zjc4OGFkNDYwY2U2MmY3ZjQ0"
        }
        
        logging.info(f"API配置检查:")
        logging.info(f"App ID: {api_config['app_id']}")
        logging.info(f"API Key: {api_config['api_key'][:10]}...{api_config['api_key'][-4:]}")
        logging.info(f"API Secret: {api_config['api_secret'][:10]}...{api_config['api_secret'][-4:]}")
        
        # 尝试生成语音
        logging.info("开始调用科大讯飞TTS...")
        audio_file = tts_integration.xunfei_tts(
            text=test_text,
            app_id=api_config['app_id'],
            api_key=api_config['api_key'],
            api_secret=api_config['api_secret'],
            voice_name="x4_yezi"
        )
        
        result = {
            'api_config': {
                'app_id': api_config['app_id'],
                'api_key_partial': f"{api_config['api_key'][:8]}...{api_config['api_key'][-4:]}",
                'voice_name': 'x4_yezi'
            }
        }
        
        if audio_file:
            logging.info(f"TTS返回文件路径: {audio_file}")
            
            if os.path.exists(audio_file):
                file_size = os.path.getsize(audio_file)
                logging.info(f"文件存在，大小: {file_size} bytes")
                
                if file_size > 0:
                    # 验证WAV文件格式
                    wav_info = "未检测"
                    try:
                        import wave
                        with wave.open(audio_file, 'rb') as wav_f:
                            channels = wav_f.getnchannels()
                            sample_width = wav_f.getsampwidth()
                            framerate = wav_f.getframerate()
                            frames = wav_f.getnframes()
                            duration = frames / framerate
                            
                        wav_info = f"格式验证: {channels}声道, {sample_width*8}位, {framerate}Hz, 时长{duration:.2f}秒"
                        logging.info(wav_info)
                        
                    except Exception as wav_error:
                        wav_info = f"WAV格式验证失败: {wav_error}"
                        logging.error(wav_info)
                    
                    # 优先使用winsound测试（因为聊天中已证明它有效）
                    winsound_test = "未测试"
                    pygame_test = "未测试"
                    system_test = "未测试"
                    successful_method = None
                    
                    # 测试1: winsound播放 (Windows推荐)
                    try:
                        import winsound
                        logging.info("测试winsound播放...")
                        start_time = time.time()
                        winsound.PlaySound(audio_file, winsound.SND_FILENAME)
                        duration = time.time() - start_time
                        winsound_test = f"SUCCESS (耗时{duration:.2f}秒)"
                        successful_method = "winsound"
                        logging.info(f"winsound播放测试成功，耗时{duration:.2f}秒")
                        
                    except Exception as winsound_error:
                        winsound_test = f"FAILED: {str(winsound_error)}"
                        logging.error(f"winsound测试失败: {winsound_error}")
                        
                        # 测试2: 系统播放器
                        try:
                            import subprocess
                            import platform
                            
                            if platform.system() == "Windows":
                                logging.info("测试系统播放器...")
                                start_time = time.time()
                                result_sys = subprocess.run([
                                    "powershell", "-c", 
                                    f"(New-Object Media.SoundPlayer '{audio_file}').PlaySync()"
                                ], capture_output=True, text=True, timeout=10)
                                duration = time.time() - start_time
                                
                                if result_sys.returncode == 0:
                                    system_test = f"SUCCESS (耗时{duration:.2f}秒)"
                                    successful_method = "system"
                                    logging.info(f"系统播放器测试成功，耗时{duration:.2f}秒")
                                else:
                                    system_test = f"FAILED: {result_sys.stderr}"
                        except Exception as sys_error:
                            system_test = f"FAILED: {str(sys_error)}"
                            logging.error(f"系统播放器测试失败: {sys_error}")
                        
                        # 测试3: pygame播放（最后尝试）
                        if not successful_method:
                            try:
                                import pygame
                                logging.info("测试pygame播放...")
                                start_time = time.time()
                                
                                pygame.mixer.quit()
                                pygame.mixer.pre_init(frequency=16000, size=-16, channels=1, buffer=1024)
                                pygame.mixer.init()
                                
                                pygame.mixer.music.load(audio_file)
                                pygame.mixer.music.play()
                                
                                while pygame.mixer.music.get_busy():
                                    pygame.time.wait(100)
                                
                                pygame.mixer.quit()
                                duration = time.time() - start_time
                                pygame_test = f"SUCCESS (耗时{duration:.2f}秒)"
                                successful_method = "pygame"
                                logging.info(f"pygame播放测试成功，耗时{duration:.2f}秒")
                                
                            except Exception as pygame_error:
                                pygame_test = f"FAILED: {str(pygame_error)}"
                                logging.error(f"pygame测试失败: {pygame_error}")
                    
                    # 根据测试结果确定推荐方法
                    if successful_method:
                        result.update({
                            'success': True,
                            'message': f'TTS生成和播放测试完全成功！推荐使用{successful_method}播放器',
                            'file_path': audio_file,
                            'file_size': file_size,
                            'wav_info': wav_info,
                            'winsound_test': winsound_test,
                            'system_test': system_test,
                            'pygame_test': pygame_test,
                            'recommended_player': successful_method,
                            'all_tests': {
                                'winsound': winsound_test,
                                'system': system_test,
                                'pygame': pygame_test
                            }
                        })
                    else:
                        result.update({
                            'success': False,
                            'message': 'TTS生成成功但所有播放方法都失败',
                            'file_path': audio_file,
                            'file_size': file_size,
                            'wav_info': wav_info,
                            'winsound_test': winsound_test,
                            'system_test': system_test,
                            'pygame_test': pygame_test,
                            'error': '所有播放方法均失败'
                        })
                    
                    # 清理测试文件
                    try:
                        os.remove(audio_file)
                        logging.info("测试文件已清理")
                    except Exception as cleanup_error:
                        logging.warning(f"清理测试文件失败: {cleanup_error}")
                        
                else:
                    result.update({
                        'success': False,
                        'error': '生成的音频文件为空',
                        'file_size': 0
                    })
            else:
                result.update({
                    'success': False,
                    'error': '音频文件未创建',
                    'file_path': audio_file
                })
        else:
            result.update({
                'success': False,
                'error': 'TTS返回空值，可能是API密钥问题或网络问题'
            })
        
        logging.info(f"=== TTS调试结果: {result} ===")
        return jsonify(result)
        
    except Exception as e:
        logging.error(f"TTS调试异常: {e}")
        import traceback
        logging.error(f"详细错误: {traceback.format_exc()}")
        return jsonify({
            'success': False,
            'error': f'TTS调试异常: {str(e)}',
            'traceback': traceback.format_exc()
        })

@app.route('/api/stop_recording', methods=['POST'])
def stop_recording():
    """录音停止，安静一下，蓄力再发声！"""
    try:
        if hasattr(asr, 'is_recording_active') and asr.is_recording_active():
            asr.stop_recording()
            return jsonify({
                'success': True,
                'message': '录音已停止'
            })
        else:
            return jsonify({
                'success': False,
                'message': '当前没有录音进行中'
            })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

# 添加一个简单的音频测试接口
@app.route('/api/test_audio_simple', methods=['POST'])
def test_audio_simple():
    """简单音频测试，声音就是能量！"""
    try:
        test_text = "测试音频播放，这是一个语音合成测试"
        
        logging.info("生成测试音频文件...")
        
        # 指定保存目录为项目根目录
        save_dir = os.path.dirname(__file__)  # mouthcontrol目录
        timestamp = int(time.time())
        audio_filename = f"test_audio_{timestamp}.wav"
        audio_path = os.path.join(save_dir, audio_filename)
        
        # 使用改进的TTS生成
        audio_file = generate_mp3_tts(
            text=test_text,
            save_path=audio_path,
            app_id="54bbe675",
            api_key="4d0929a6ec7aa1b2c076dcdb25c7b16d",
            api_secret="YzMyYTc4Zjc4OGFkNDYwY2U2MmY3ZjQ0"
        )
        
        if audio_file and os.path.exists(audio_file):
            file_size = os.path.getsize(audio_file)
            
            return jsonify({
                'success': True,
                'message': f'音频文件已生成并保存到项目目录',
                'file_path': audio_file,
                'file_size': file_size,
                'instruction': f'请双击播放文件: {audio_file}',
                'relative_path': audio_filename
            })
        else:
            return jsonify({
                'success': False,
                'error': '音频文件生成失败'
            })
            
    except Exception as e:
        logging.error(f"简单音频测试异常: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        })

def generate_mp3_tts(text, save_path, app_id, api_key, api_secret, voice_name="x4_yezi"):
    """语音合成魔法阵，文字秒变声音！"""
    import tempfile
    import base64
    import hmac
    import hashlib
    import json
    import urllib.parse
    import websocket
    import wave
    
    try:
        # 构造 WebSocket 认证 URL
        host = "tts-api.xfyun.cn"
        path = "/v2/tts"
        date = time.strftime("%a, %d %b %Y %H:%M:%S GMT", time.gmtime())

        signature_origin = f"host: {host}\ndate: {date}\nGET {path} HTTP/1.1"
        signature_sha = hmac.new(
            api_secret.encode('utf-8'),
            signature_origin.encode('utf-8'),
            digestmod=hashlib.sha256
        ).digest()
        signature = base64.b64encode(signature_sha).decode('utf-8')

        auth_origin = f'api_key="{api_key}", algorithm="hmac-sha256", headers="host date request-line", signature="{signature}"'
        authorization = base64.b64encode(auth_origin.encode('utf-8')).decode('utf-8')

        params = urllib.parse.urlencode({
            'authorization': authorization,
            'date': date,
            'host': host
        })
        ws_url = f"wss://{host}{path}?{params}"

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
                    result["error"] = f"API 错误 {code}: {data.get('message', '未知错误')}"
                    ws.close()
                    return

                audio_info = data.get("data", {})
                if audio_info and "audio" in audio_info:
                    audio_data = audio_info["audio"]
                    if audio_data:
                        chunk = base64.b64decode(audio_data)
                        pcm_data += chunk
                    if audio_info.get("status") == 2:
                        ws.close()

            except Exception as e:
                result["error"] = f"处理消息失败: {e}"
                ws.close()

        def on_error(ws, error):
            result["error"] = f"WebSocket 错误: {error}"

        def on_close(ws, close_status_code, close_msg):
            if not result["error"] and pcm_data:
                result["success"] = True

        def on_open(ws):
            try:
                payload = {
                    "common": {"app_id": app_id},
                    "business": {
                        "aue": "raw",  # 原始PCM格式
                        "auf": "audio/L16;rate=16000",  # 16kHz采样率
                        "vcn": voice_name,
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
                result["error"] = f"发送请求失败: {e}"
                ws.close()

        # 执行WebSocket连接
        ws_app = websocket.WebSocketApp(
            ws_url,
            on_open=on_open,
            on_message=on_message,
            on_error=on_error,
            on_close=on_close
        )
        ws_app.run_forever(ping_interval=30, ping_timeout=10)

        if result["success"] and pcm_data:
            logging.info(f"获取PCM数据: {len(pcm_data)} bytes")
            
            # 创建WAV文件
            try:
                with wave.open(save_path, 'wb') as wav_f:
                    wav_f.setnchannels(1)          # 单声道
                    wav_f.setsampwidth(2)          # 16位
                    wav_f.setframerate(16000)      # 16kHz采样率
                    wav_f.writeframes(pcm_data)
                
                logging.info(f"WAV文件已保存: {save_path}")
                return save_path
                
            except Exception as e:
                logging.error(f"音频文件处理失败: {e}")
                return None
        else:
            logging.error(f"TTS生成失败: {result['error']}")
            return None
            
    except Exception as e:
        logging.error(f"生成TTS异常: {e}")
        return None

# 添加Arduino连接状态检查接口
@app.route('/api/arduino/status')
def get_arduino_status():
    """获取Arduino连接状态"""
    try:
        return jsonify({
            'success': True,
            'connected': audio_analyzer.is_connected if hasattr(audio_analyzer, 'is_connected') else False,
            'port': getattr(audio_analyzer, 'com_port', None),
            'available_ports': audio_analyzer.get_available_ports()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'connected': False
        })

@app.route('/api/arduino/test', methods=['POST'])
def test_arduino():
    """Arduino测试，硬件小能手上线！"""
    try:
        if not audio_analyzer.is_connected:
            return jsonify({
                'success': False,
                'error': '设备未连接'
            })
        
        # 测试舵机控制
        test_result = audio_analyzer.set_face_part_angle('PHILTRUM', 90)
        
        if test_result:
            return jsonify({
                'success': True,
                'message': 'Arduino测试成功'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Arduino测试失败'
            })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/expression', methods=['POST'])
def apply_expression():
    """应用表情，机器人也有小情绪！"""
    try:
        data = request.json
        expression_name = data.get('expression', '').strip()
        
        if not expression_name:
            return jsonify({'success': False, 'error': '请指定表情名称'})
        
        if not audio_analyzer.is_connected:
            return jsonify({'success': False, 'error': '设备未连接'})
        
        # 检查是否有表情控制方法
        if hasattr(audio_analyzer, 'apply_expression'):
            success = audio_analyzer.apply_expression(expression_name)
            if success:
                return jsonify({'success': True, 'message': f'表情 {expression_name} 已应用'})
            else:
                return jsonify({'success': False, 'error': f'表情 {expression_name} 应用失败'})
        else:
            return jsonify({'success': False, 'error': '当前设备不支持表情控制'})
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/servo/center', methods=['POST'])
def center_all_servos():
    """舵机回中位，归位整装再出发！"""
    try:
        if not audio_analyzer.is_connected:
            return jsonify({'success': False, 'error': '设备未连接'})
        
        if hasattr(audio_analyzer, 'center_all_servos'):
            success = audio_analyzer.center_all_servos()
            if success:
                return jsonify({'success': True, 'message': '所有舵机已回到中位'})
            else:
                return jsonify({'success': False, 'error': '回中位操作失败'})
        else:
            # 兼容处理
            try:
                # 发送CENTER命令
                if hasattr(audio_analyzer, '_send_command'):
                    audio_analyzer._send_command("CENTER")
                    return jsonify({'success': True, 'message': '回中位命令已发送'})
                else:
                    return jsonify({'success': False, 'error': '设备不支持此操作'})
            except Exception as e:
                return jsonify({'success': False, 'error': f'操作失败: {str(e)}'})
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/arduino/setup_guide', methods=['POST'])
def arduino_setup_guide():
    """Arduino设置向导，带你一步步搞定！"""
    try:
        data = request.json
        step = data.get('step', 'check_ports')
        
        if step == 'check_ports':
            # 步骤1: 检查可用串口
            available_ports = audio_analyzer.get_available_ports()
            
            return jsonify({
                'success': True,
                'step': 'check_ports',
                'available_ports': available_ports,
                'message': f'发现 {len(available_ports)} 个串口' if available_ports else '未发现串口',
                'next_step': 'check_arduino_code' if available_ports else 'no_ports_found'
            })
            
        elif step == 'check_arduino_code':
            # 步骤2: 检查Arduino代码状态
            return jsonify({
                'success': True,
                'step': 'check_arduino_code',
                'code_options': [
                    {
                        'name': '简单舵机控制 (motor.ino)',
                        'description': '单个舵机控制，适合简单测试',
                        'baudrate': 115200,
                        'file': 'motor.ino'
                    },
                    {
                        'name': 'PCA9685多舵机控制 (arduino_pca9685.ino)',
                        'description': '16路舵机控制，完整面部表情',
                        'baudrate': 115200,
                        'file': 'arduino_pca9685.ino'
                    }
                ],
                'message': '请确认Arduino烧录的代码类型',
                'next_step': 'test_connection'
            })
            
        elif step == 'test_connection':
            # 步骤3: 测试连接
            port = data.get('port')
            baudrate = data.get('baudrate', 115200)
            
            if not port:
                return jsonify({
                    'success': False,
                    'error': '请指定串口'
                })
            
            # 修复：fuxxk xiaomi
            debug_result = debug_arduino_connection_sync(port)
            
            return jsonify({
                'success': True,
                'step': 'test_connection',
                'debug_result': debug_result,
                'next_step': 'connection_result'
            })
            
        else:
            return jsonify({
                'success': False,
                'error': '未知步骤'
            })
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'设置向导异常: {str(e)}'
        })

def debug_arduino_connection_sync(port):
    """Arduino连接调试，排查每一步，绝不放过小问题！"""
    try:
        debug_info = {
            'port': port,
            'steps': [],
            'success': False,
            'suggestions': []
        }
        
        # 我要来了
        available_ports = audio_analyzer.get_available_ports()
        if port not in available_ports:
            debug_info['steps'].append({
                'step': '检查串口存在性',
                'status': 'FAILED',
                'message': f'串口 {port} 不存在'
            })
            debug_info['suggestions'] = [
                '1. 请重新插拔Arduino USB线',
                '2. 检查Arduino是否被系统识别',
                '3. 尝试重启Arduino IDE或重新安装驱动'
            ]
            return debug_info
        
        debug_info['steps'].append({
            'step': '检查串口存在性',
            'status': 'PASSED',
            'message': f'串口 {port} 存在'
        })
        
        #喜喜
        import serial
        try:
            test_serial = serial.Serial(
                port=port,
                baudrate=115200,
                timeout=2
            )
            
            debug_info['steps'].append({
                'step': '打开串口',
                'status': 'PASSED',
                'message': f'成功打开串口 {port}'
            })
            
            # 等待Arduino启动
            time.sleep(3)
            test_serial.flushInput()
            test_serial.flushOutput()
            
            # 读取启动消息
            startup_messages = []
            start_time = time.time()
            while time.time() - start_time < 3:
                if test_serial.in_waiting > 0:
                    try:
                        line = test_serial.readline().decode().strip()
                        if line:
                            startup_messages.append(line)
                    except:
                        pass
                time.sleep(0.1)
            
            if startup_messages:
                debug_info['steps'].append({
                    'step': '读取启动消息',
                    'status': 'PASSED',
                    'message': f'收到消息: {startup_messages}'
                })
                
                # 检查消息内容判断代码类型
                code_type = 'unknown'
                if any('Face Control System' in msg for msg in startup_messages):
                    if any('Simple Servo Controller' in msg for msg in startup_messages):
                        code_type = 'motor.ino (简单舵机)'
                    else:
                        code_type = 'arduino_pca9685.ino (多舵机)'
                
                debug_info['detected_code'] = code_type
            else:
                debug_info['steps'].append({
                    'step': '读取启动消息',
                    'status': 'WARNING',
                    'message': '未收到启动消息，可能代码未正确烧录'
                })
            
            # 测试命令响应
            test_serial.write(b'CENTER\n')
            test_serial.flush()
            time.sleep(1)
            
            response_messages = []
            start_time = time.time()
            while time.time() - start_time < 2:
                if test_serial.in_waiting > 0:
                    try:
                        line = test_serial.readline().decode().strip()
                        if line:
                            response_messages.append(line)
                    except:
                        pass
                time.sleep(0.1)
            
            if response_messages:
                debug_info['steps'].append({
                    'step': '测试命令响应',
                    'status': 'PASSED',
                    'message': f'Arduino响应: {response_messages}'
                })
                debug_info['success'] = True
            else:
                debug_info['steps'].append({
                    'step': '测试命令响应',
                    'status': 'FAILED',
                    'message': 'Arduino未响应CENTER命令'
                })
            
            test_serial.close()
            
        except Exception as serial_error:
            debug_info['steps'].append({
                'step': '串口连接',
                'status': 'FAILED',
                'message': f'串口连接失败: {str(serial_error)}'
            })
        
        # 添加针对性建议
        if not debug_info['success']:
            debug_info['suggestions'] = [
                '1. 确认Arduino已烧录正确代码（motor.ino或arduino_pca9685.ino）',
                '2. 检查代码中的波特率是否为115200',
                '3. 关闭Arduino IDE串口监视器',
                '4. 重新上传Arduino代码',
                '5. 检查Arduino电源和USB连接',
                '6. 尝试重启Arduino（按reset按钮）'
            ]
            
            # 检查是否是波特率问题
            if '串口连接失败' in str(debug_info['steps'][-1]['message']):
                debug_info['suggestions'].insert(0, '⚠️ 可能是波特率不匹配！请确认Arduino代码使用115200波特率')
        
        return debug_info
        
    except Exception as e:
        return {
            'success': False,
            'error': f'调试异常: {str(e)}'
        }

@app.route('/api/tcp/send', methods=['POST'])
def tcp_send():
    """字节流发射，底层硬刚，能量直达下位机！"""
    global tcp_client, tcp_addr
    try:
        if not tcp_client or not tcp_addr:
            return jsonify({'success': False, 'error': '未连接下位机'})
        # 前端传递 base64 编码的字节流
        data = request.json.get('data')
        if not data:
            return jsonify({'success': False, 'error': '缺少data字段'})
        # 解码 base64 得到 bytes
        try:
            send_bytes = base64.b64decode(data)
        except Exception as e:
            return jsonify({'success': False, 'error': f'base64解码失败: {e}'})
        tcp_client.sendall(send_bytes)
        return jsonify({'success': True, 'message': '已发送字节流'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

if __name__ == '__main__':
    print("🚀 智能语音机器人控制系统启动中...")
    print("=" * 60)
    print("📍 访问地址: http://localhost:5000")
    print("🎤 TTS: 科大讯飞语音合成")
    print("🎙️  ASR: 科大讯飞语音识别") 
    print("🤖 AI: 豆包大模型对话")
    print("⚙️  控制: Arduino舵机系统")
    print("=" * 60)
    print("海百川公司新平台，能量满满！")
    app.run(host='0.0.0.0', port=5000, debug=True)
