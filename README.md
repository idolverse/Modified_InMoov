# 🌸 Modified_InMoov（にゃ～这是 ROS2 分支喵！）

喵喵喵～欢迎来到这个可爱的 Modified_InMoov 项目世界！这里是专为 **ROS2（Robot Operating System 2）** 准备的分支哦~！ヾ(≧▽≦*)o

我们已经把 **ROS2 和 Unity** 嫁接在一起啦，使用的是 `ros2-unity-bridge` ✨  
这样主人大人就可以在 Unity 中操控机器人动作，还可以通过 ROS2 实现路径规划、动作发布、传感器同步等等高级功能呢！

---

## 🧠 当前特性（喵~）：

✅ 这是一个 **ROS2 专用分支**，不再兼容 ROS1 哦~！  
✅ 已集成 **ROS2 与 Unity 桥接功能**（使用 `rosbridge_server` + `ROS-TCP-Connector`）  
✅ 支持 **UDP/TCP/WebSocket/HTTP 多种通信方式**（包括图像传输与识别）  
✅ 可用于 **Unity UI 控制舵机角度、发布话题数据到 ROS2**  
✅ 正在适配 **MoveIt2、Gazebo、控制器模拟、关节轨迹控制** 等高级特性  
✅ 已移植 **手势识别功能（MediaPipe + OpenCV）**，用于控制模拟手臂动作  
✅ 已添加 **SUP Left Arm URDF（三关节测试）**

---

## 🛠️ 推荐使用工具：

- ROS2 Humble 及以上版本（Foxy 也可以试试）
- Unity 2021+（推荐使用 ROS-TCP-Connector 插件）
- rosbridge_server + ros2-web-bridge
- WebSocket 客户端 / UDP 监听器 / HTTP 测试器（任选其一）
- Arduino 或 ESP32（用于真实舵机联动）

---

## 🧪 最近更新（根据提交记录喵）：

- 🧱 添加 ros2 tcp bridge、UDP 消息转换器、HTTP 支持
- 🎮 加入 Unity 测试工程，可实现 UI 控制、图像显示
- 🤖 移植手势识别控制模块（摄像头 -> OpenCV -> ROS2）
- 🛠️ 测试并修正左臂 URDF（三关节结构）

---

## 💕 喵尾提示（注意事项）

- **初次使用建议 clone 此分支**，而不是默认分支（master 是 ROS1 的哦）  
- **如需 ROS1 支持请切回 master 分支喵~**
- URDF/Launch/Unity 部分仍在持续更新中，欢迎 PR 或 issue！

---

## 🐾 未来还想加上这些：

- [ ] 支持 MoveIt2 自动规划手臂轨迹
- [ ] Gazebo 中完整身体模型控制
- [ ] 加入语音唤醒系统？（欸欸欸！）
- [ ] 自动学习姿态 + 强化学习控制系统

---

喵～欢迎一起来开发！有问题可以开 issue 或留言告诉我哟 (ฅ´ω`ฅ)  
**Modified_InMoov**
