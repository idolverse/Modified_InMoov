#include <Arduino.h>
#include <ArduinoJson.h>

void setup() {
  Serial.begin(115200);
  while (!Serial) ; // 等待串口连接
  Serial.println("ESP32 Ready");
}

void loop() {
  if (Serial.available()) {
    String input = Serial.readStringUntil('\n'); // 读取一行
    StaticJsonDocument<128> doc;
    DeserializationError error = deserializeJson(doc, input);
    if (!error) {
      const char* cmd = doc["cmd"];
      int value = doc["value"];
      Serial.print("收到指令: ");
      Serial.print(cmd);
      Serial.print(", value: ");
      Serial.println(value);
      // 根据cmd和value执行动作
      if (strcmp(cmd, "hello") == 0) {
        // 这里可以控制GPIO、舵机等
        Serial.println("执行hello动作");
      }
      // 可扩展更多命令
    } else {
      Serial.println("JSON解析失败");
    }
  }
}
