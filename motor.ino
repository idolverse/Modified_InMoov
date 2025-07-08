/*
 * 简单舵机控制程序
 * 接收串口角度值，控制连接在5号引脚的舵机
 */

#include <Servo.h>

Servo mouthServo;  // 创建舵机对象
const int servoPin = 5;  // 舵机信号线连接5号引脚

void setup() {
  // 初始化串口通信
  Serial.begin(9600);
  
  // 连接舵机到5号引脚
  mouthServo.attach(servoPin);
  
  // 初始化舵机到0度位置
  mouthServo.write(0);
  
  Serial.println("嘴部舵机控制系统已启动");
  Serial.println("请发送0-90之间的角度值");
}

void loop() {
  // 检查是否有串口数据
  if (Serial.available() > 0) {
    // 读取角度值
    String angleStr = Serial.readStringUntil('\n');
    angleStr.trim();  // 去除空格和换行符
    
    // 转换为整数
    int angle = angleStr.toInt();
    
    // 检查角度范围
    if (angle >= 0 && angle <= 90) {
      // 控制舵机转动
      mouthServo.write(angle);
      
      // 反馈当前角度
      Serial.print("舵机角度设置为: ");
      Serial.print(angle);
      Serial.println("度");
    } else {
      Serial.println("错误: 角度必须在0-90之间");
    }
  }
  
  delay(50);  // 小延时，避免过于频繁的检查
}
