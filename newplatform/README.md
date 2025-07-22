# 新平台项目说明

欢迎来到海百川公司新平台！本项目集成了机器人控制、语音识别、AI对话、TCP通信等多种功能模块，支持STM32、Arduino、ESP32等硬件，以及Python/Flask/Web等上位机。下面详细介绍每个主要文件的作用和用法。

---

## 目录结构与主要文件说明

### 1. `test_tcp_api.py`
- **位置**：`c:\Users\a's\Desktop\newplatform\test_tcp_api.py`
- **作用**：TCP通信测试脚本，通过HTTP API向下位机发送控制命令（支持JSON和字节流），带重试机制和进度统计。
- **特色**：注释风格活泼，适合开发者快速测试和调试TCP通信。支持批量和异步发送。

### 2. `new\web_server.py`
- **位置**：`c:\Users\a's\Desktop\newplatform\new\web_server.py`
- **作用**：主Web服务，基于Flask，提供AI聊天、语音合成、语音识别、舵机控制、串口管理等RESTful API。
- **特色**：每个接口注释都很有活力，易于理解和扩展。支持与硬件（Arduino/STM32）和AI模块联动。

### 3. `new\speech_recognition.py`
- **位置**：`c:\Users\a's\Desktop\newplatform\new\speech_recognition.py`
- **作用**：科大讯飞语音识别模块，支持录音、实时识别、麦克风检测等功能。
- **特色**：注释风格有趣，接口清晰，支持随时停止录音和检测麦克风状态。

### 4. `new\tts_integration.py`
- **位置**：`c:\Users\a's\Desktop\newplatform\new\tts_integration.py`
- **作用**：集成豆包TTS和科大讯飞TTS，支持文本转语音，自动生成临时音频文件，支持清理和重命名。
- **特色**：支持mp3格式，注释简明，方便扩展。

### 5. `new\ai.py`
- **位置**：`c:\Users\a's\Desktop\newplatform\new\ai.py`
- **作用**：豆包AI对话模块，支持多轮对话、性格自定义、命令系统。
- **特色**：注释详细，支持命令行交互和API调用。

### 6. `new\face_controller.py`
- **位置**：`c:\Users\a's\Desktop\newplatform\new\face_controller.py`
- **作用**：面部控制器，管理串口连接、舵机控制、表情应用等。
- **特色**：支持批量设置、预设表情、角度范围限制，注释风格实用。

### 7. `new\debug_chin_test.py`
- **位置**：`c:\Users\a's\Desktop\newplatform\new\debug_chin_test.py`
- **作用**：自动检测所有串口，区分PCA9685和face_control版本，测试下巴控制。
- **特色**：输出详细测试建议，便于硬件调试。

### 8. `new\audio_gui.py`
- **位置**：`c:\Users\a's\Desktop\newplatform\new\audio_gui.py`
- **作用**：TTS测试工具，支持音频播放、面部控制、敏感度设置、日志记录。
- **特色**：界面友好，功能丰富，适合开发和调试。

### 9. `new\ui\main_window.py`
- **位置**：`c:\Users\a's\Desktop\newplatform\new\ui\main_window.py`
- **作用**：Tkinter界面，集成面部控制、串口管理、音频分析、日志显示等。
- **特色**：分区清晰，交互友好，注释详细。

### 10. `stm32_tcp_server.c`
- **位置**：`c:\Users\a's\Desktop\newplatform\stm32_tcp_server.c`
- **作用**：STM32端TCP服务器，监听9000端口，接收上位机指令（如JSON），解析命令控制硬件（如LED、舵机）。
- **特色**：代码结构清晰，注释简明，适合嵌入式开发者移植和扩展。

### 11. `new\arduino_pca9685\arduino_pca9685.ino`
- **位置**：`c:\Users\a's\Desktop\newplatform\new\arduino_pca9685\arduino_pca9685.ino`
- **作用**：Arduino端PCA9685多舵机控制器，支持面部表情控制，串口命令解析。
- **特色**：注释详细，支持多种命令格式，易于扩展。

### 12. `esp32_uart_json\esp32_uart_json.ino`
- **位置**：`c:\Users\a's\Desktop\newplatform\esp32_uart_json\esp32_uart_json.ino`
- **作用**：ESP32串口JSON命令解析，支持控制GPIO、舵机等。
- **特色**：代码简洁，易于扩展更多命令。

### 13. `新建 文本文档.py`
- **位置**：`c:\Users\a's\Desktop\newplatform\新建 文本文档.py`
- **作用**：发送速度诊断工具，测试连接、发送、网络延迟、批量发送，并给出优化建议。
- **特色**：支持异步发送示例，输出详细性能分析。

### 14. `new\启动控制器.bat`
- **位置**：`c:\Users\a's\Desktop\newplatform\new\启动控制器.bat`
- **作用**：一键启动控制器，自动检查依赖库和核心文件，启动Web服务。
- **特色**：自动安装依赖，友好提示，适合新手快速部署。

### 15. `new\templates\index.html`
- **位置**：`c:\Users\a's\Desktop\newplatform\new\templates\index.html`
- **作用**：Web前端主页，集成机器人状态、控制面板、对话界面、Arduino连接、舵机调试等。
- **特色**：界面美观，交互丰富，支持语音和文字聊天。

---

## 快速启动指南

1. **启动Web服务**
   - 进入 `new` 目录，运行 `web_server.py`：
     ```
     python web_server.py
     ```
   - 默认监听 `localhost:5000`，可通过浏览器访问主页或调用API。

2. **测试TCP通信**
   - 运行 `test_tcp_api.py`，自动连接TCP下位机并发送测试指令。
   - 支持JSON和字节流两种发送方式，适合测试STM32/Arduino等硬件端。

3. **语音识别/合成**
   - 通过Web API `/api/asr/recognize` 或 `/api/ai/speak` 实现语音识别和合成。
   - 依赖讯飞API，请确保API Key等参数有效。

4. **STM32端TCP服务器**
   - 编译并烧录 `stm32_tcp_server.c` 到STM32设备。
   - 确保设备与上位机在同一局域网，端口为9000。

5. **Arduino端多舵机控制**
   - 烧录 `arduino_pca9685.ino` 到Arduino，连接PCA9685模块。
   - 支持串口命令控制面部表情。

6. **ESP32串口JSON控制**
   - 烧录 `esp32_uart_json.ino` 到ESP32，支持串口JSON命令解析。

7. **一键启动控制器**
   - 运行 `启动控制器.bat`，自动检查依赖并启动Web服务。

---

## 主要API接口说明（部分）

- `/api/tcp/send`：发送字节流到下位机（支持base64编码）。
- `/api/tcp/connect`：连接TCP下位机。
- `/api/ai/chat`：AI对话接口。
- `/api/ai/speak`：AI语音合成接口。
- `/api/asr/recognize`：语音识别接口。
- `/api/servo`：舵机控制接口。
- `/api/arduino/debug`：Arduino连接调试。
- `/api/face/advanced`：批量面部表情控制。
- `/api/ports`：获取可用串口列表。
- `/api/status`：获取机器人整体状态。

---

## 其它说明

- 所有Python代码注释都经过个性化处理，阅读体验轻松愉快。
- 支持多硬件、多协议，适合机器人、智能硬件、语音交互等场景。
- 如需扩展或定制，请参考各模块注释和接口文档。
- 前端页面美观，支持语音和文字交互，适合演示和实际应用。

---

## 联系与支持

如有问题或建议，欢迎联系海百川公司技术团队。祝你开发愉快，能量满满！

