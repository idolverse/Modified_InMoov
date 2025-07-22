/*
 * PCA9685多舵机控制器
 * 控制面部表情舵机
 * 
 * 硬件连接：
 * PCA9685 -> Arduino Uno
 * VCC -> 5V
 * GND -> GND
 * SCL -> A5
 * SDA -> A4
 * 
 * 舵机通道：
 * 0 - 左眼球上下
 * 1 - 左眼球左右
 * 2 - 右眼球上下
 * 3 - 右眼球左右
 * 4 - 人中
 * 5 - 下巴
 * 6 - 左上眼皮
 * 7 - 左下眼皮
 * 8 - 右上眼皮
 * 9 - 右下眼皮
 * 10 - 左眉毛
 * 11 - 右眉毛
 * 12 - 左前额
 * 13 - 右前额
 * 14 - 左脸颊
 * 15 - 右脸颊
 */

#include <Wire.h>
#include <Adafruit_PWMServoDriver.h>

// =====================================================
// 配置定义部分
// =====================================================

// PCA9685配置
#define PCA9685_ADDRESS 0x40
#define SERVO_FREQ 50 // 舵机频率50Hz

// 舵机PWM值范围
#define SERVO_MIN 150  // 对应0度的PWM值
#define SERVO_MAX 600  // 对应180度的PWM值

// 面部舵机通道映射
enum FaceServoChannels {
  // 眼球控制
  LEFT_EYE_VERTICAL = 0,    // 左眼球上下控制
  LEFT_EYE_HORIZONTAL = 1,  // 左眼球左右控制
  RIGHT_EYE_VERTICAL = 2,   // 右眼球上下控制
  RIGHT_EYE_HORIZONTAL = 3, // 右眼球左右控制
  
  // 嘴部控制
  PHILTRUM = 4,            // 人中
  CHIN = 5,                // 下巴
  
  // 眼皮控制
  LEFT_UPPER_EYELID = 6,   // 左上眼皮
  LEFT_LOWER_EYELID = 7,   // 左下眼皮
  RIGHT_UPPER_EYELID = 8,  // 右上眼皮
  RIGHT_LOWER_EYELID = 9,  // 右下眼皮
  
  // 眉毛控制
  LEFT_EYEBROW = 10,       // 左眉毛
  RIGHT_EYEBROW = 11,      // 右眉毛
  
  // 前额控制
  LEFT_FOREHEAD = 12,      // 左前额
  RIGHT_FOREHEAD = 13,     // 右前额
  
  // 脸颊控制
  LEFT_CHEEK = 14,         // 左脸颊
  RIGHT_CHEEK = 15         // 右脸颊
};

// 舵机中位角度（初始位置）
#define DEFAULT_ANGLE 90

// 各个舵机的角度限制
struct ServoLimit {
  int minAngle;
  int maxAngle;
};

// 定义各个舵机的角度范围
const ServoLimit servoLimits[16] = {
  {30, 150},   // LEFT_EYE_VERTICAL
  {30, 150},   // LEFT_EYE_HORIZONTAL
  {30, 150},   // RIGHT_EYE_VERTICAL
  {30, 150},   // RIGHT_EYE_HORIZONTAL
  {45, 135},   // PHILTRUM
  {45, 135},   // CHIN
  {45, 135},   // LEFT_UPPER_EYELID
  {45, 135},   // LEFT_LOWER_EYELID
  {45, 135},   // RIGHT_UPPER_EYELID
  {45, 135},   // RIGHT_LOWER_EYELID
  {30, 150},   // LEFT_EYEBROW
  {30, 150},   // RIGHT_EYEBROW
  {30, 150},   // LEFT_FOREHEAD
  {30, 150},   // RIGHT_FOREHEAD
  {45, 135},   // LEFT_CHEEK
  {45, 135}    // RIGHT_CHEEK
};

// =====================================================
// 舵机控制类定义
// =====================================================

class ServoController {
private:
  Adafruit_PWMServoDriver pwm;
  int currentAngles[16];
  int targetAngles[16];
  unsigned long lastUpdateTime;
  
  int angleToPWM(int angle) {
    return map(angle, 0, 180, SERVO_MIN, SERVO_MAX);
  }
  
  int constrainAngle(int channel, int angle) {
    if (channel >= 0 && channel <= 15) {
      return constrain(angle, servoLimits[channel].minAngle, servoLimits[channel].maxAngle);
    }
    return angle;
  }
  
public:
  ServoController() : pwm(PCA9685_ADDRESS) {
    lastUpdateTime = 0;
    
    // 初始化角度数组
    for (int i = 0; i < 16; i++) {
      currentAngles[i] = DEFAULT_ANGLE;
      targetAngles[i] = DEFAULT_ANGLE;
    }
  }
  
  void init() {
    pwm.begin();
    pwm.setPWMFreq(SERVO_FREQ);
    
    // 设置所有舵机到中位
    setAllServosToCenter();
    
    delay(100);
  }
  
  void setServoAngle(int channel, int angle) {
    if (channel >= 0 && channel <= 15) {
      angle = constrainAngle(channel, angle);
      targetAngles[channel] = angle;
    }
  }
  
  void setFacePartAngle(String part, int angle) {
    part.toUpperCase();
    
    if (part == "LEFT_EYEBROW") {
      setServoAngle(LEFT_EYEBROW, angle);
    }
    else if (part == "RIGHT_EYEBROW") {
      setServoAngle(RIGHT_EYEBROW, angle);
    }
    else if (part == "LEFT_CHEEK") {
      setServoAngle(LEFT_CHEEK, angle);
    }
    else if (part == "RIGHT_CHEEK") {
      setServoAngle(RIGHT_CHEEK, angle);
    }
    else if (part == "LEFT_UPPER_EYELID") {
      setServoAngle(LEFT_UPPER_EYELID, angle);
    }
    else if (part == "LEFT_LOWER_EYELID") {
      setServoAngle(LEFT_LOWER_EYELID, angle);
    }
    else if (part == "RIGHT_UPPER_EYELID") {
      setServoAngle(RIGHT_UPPER_EYELID, angle);
    }
    else if (part == "RIGHT_LOWER_EYELID") {
      setServoAngle(RIGHT_LOWER_EYELID, angle);
    }
    else if (part == "LEFT_FOREHEAD") {
      setServoAngle(LEFT_FOREHEAD, angle);
    }
    else if (part == "RIGHT_FOREHEAD") {
      setServoAngle(RIGHT_FOREHEAD, angle);
    }
    else if (part == "LEFT_EYE_V") {
      setServoAngle(LEFT_EYE_VERTICAL, angle);
    }
    else if (part == "LEFT_EYE_H") {
      setServoAngle(LEFT_EYE_HORIZONTAL, angle);
    }
    else if (part == "RIGHT_EYE_V") {
      setServoAngle(RIGHT_EYE_VERTICAL, angle);
    }
    else if (part == "RIGHT_EYE_H") {
      setServoAngle(RIGHT_EYE_HORIZONTAL, angle);
    }
    else if (part == "PHILTRUM") {
      setServoAngle(PHILTRUM, angle);
    }
    else if (part == "CHIN") {
      setServoAngle(CHIN, angle);
    }
  }
  
  void setAllServosToCenter() {
    for (int i = 0; i < 16; i++) {
      setServoAngle(i, DEFAULT_ANGLE);
    }
  }
  
  void update() {
    unsigned long currentTime = millis();
    
    // 每20ms更新一次
    if (currentTime - lastUpdateTime >= 20) {
      for (int i = 0; i < 16; i++) {
        if (currentAngles[i] != targetAngles[i]) {
          // 平滑移动到目标角度
          int diff = targetAngles[i] - currentAngles[i];
          if (abs(diff) <= 2) {
            currentAngles[i] = targetAngles[i];
          } else {
            currentAngles[i] += (diff > 0) ? 2 : -2;
          }
          
          // 更新PWM输出
          int pwmValue = angleToPWM(currentAngles[i]);
          pwm.setPWM(i, 0, pwmValue);
        }
      }
      lastUpdateTime = currentTime;
    }
  }
  
  int getCurrentAngle(int channel) {
    if (channel >= 0 && channel <= 15) {
      return currentAngles[channel];
    }
    return -1;
  }
};

// =====================================================
// 全局变量
// =====================================================

ServoController servoController;

// =====================================================
// 主程序部分
// =====================================================

void setup() {
  Serial.begin(115200);
  Serial.println("Face Control System Starting...");
  
  // 初始化舵机控制器
  servoController.init();
  
  // 将所有舵机设置到中位
  servoController.setAllServosToCenter();
  
  Serial.println("Face Control System Ready");
}

void loop() {
  // 检查串口数据
  if (Serial.available() > 0) {
    processSerialCommand();
  }
  
  // 更新舵机位置
  servoController.update();
  
  delay(20); // 50Hz更新频率
}

// =====================================================
// 串口命令处理函数
// =====================================================

void processSerialCommand() {
  String command = Serial.readStringUntil('\n');
  command.trim();
  
  if (command.startsWith("SERVO:")) {
    // 格式: SERVO:channel,angle
    int colonIndex = command.indexOf(':');
    int commaIndex = command.indexOf(',');
    
    if (colonIndex != -1 && commaIndex != -1) {
      int channel = command.substring(colonIndex + 1, commaIndex).toInt();
      int angle = command.substring(commaIndex + 1).toInt();
      
      if (channel >= 0 && channel <= 15 && angle >= 0 && angle <= 180) {
        servoController.setServoAngle(channel, angle);
        Serial.println("OK");
      } else {
        Serial.println("ERROR: Invalid parameters");
      }
    } else {
      Serial.println("ERROR: Invalid format");
    }
  }
  else if (command.startsWith("FACE:")) {
    // 格式: FACE:part,angle
    int colonIndex = command.indexOf(':');
    int commaIndex = command.indexOf(',');
    
    if (colonIndex != -1 && commaIndex != -1) {
      String part = command.substring(colonIndex + 1, commaIndex);
      int angle = command.substring(commaIndex + 1).toInt();
      
      servoController.setFacePartAngle(part, angle);
      Serial.println("OK");
    } else {
      Serial.println("ERROR: Invalid format");
    }
  }
  else if (command == "CENTER") {
    servoController.setAllServosToCenter();
    Serial.println("OK");
  }
  // 兼容旧版本的单个角度命令
  else if (command.length() > 0 && command.toInt() >= 0 && command.toInt() <= 180) {
    int angle = command.toInt();
    servoController.setServoAngle(PHILTRUM, angle);
    Serial.println("OK");
  }
  else {
    Serial.println("ERROR: Unknown command");
  }
}


