#include <WiFi.h>
#include <WiFiUdp.h>
#include <ESP32Servo.h>
#include <ArduinoJson.h>
#include <math.h>

const char* ssid = "MOJOY";
const char* password = "123456789.";
const int UDP_PORT = 4210;
WiFiUDP Udp;

const int NUM_SERVOS = 2;
const int SERVO_PINS[NUM_SERVOS] = {2, 4};
Servo servos[NUM_SERVOS];

char incomingPacket[512];

// 舵机状态
float currentAngles[NUM_SERVOS] = {0};
float targetAngles[NUM_SERVOS] = {0};
float startAngles[NUM_SERVOS] = {0};
unsigned long startTime[NUM_SERVOS] = {0};
bool isMoving[NUM_SERVOS] = {false};
float durations[NUM_SERVOS] = {1000};  // 每个舵机当前的插值时间

// Logistic 参数
const float k = 0.02;                 // Logistic 斜率
const float minDuration = 100.0;      // 最短插值时间
const float maxDuration = 1000.0;     // 最大插值时间
const float minStepTime = 15;         // 最小刷新间隔
unsigned long lastUpdateTime = 0;

void setup() {
  Serial.begin(115200);

  for (int i = 0; i < NUM_SERVOS; i++) {
    servos[i].setPeriodHertz(50);
    servos[i].attach(SERVO_PINS[i], 500, 2400);
    servos[i].write(0);
  }

  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500); Serial.print(".");
  }
  Serial.println("\nWiFi connected.");
  Serial.println(WiFi.localIP());

  Udp.begin(UDP_PORT);
  Serial.printf("Listening on UDP port %d\n", UDP_PORT);
}

// 简易 map 函数（float 版本）
float fmap(float x, float in_min, float in_max, float out_min, float out_max) {
  return out_min + (out_max - out_min) * ((x - in_min) / (in_max - in_min));
}

void loop() {
  // -------------------- 接收 JSON 指令 --------------------
  int packetSize = Udp.parsePacket();
  if (packetSize) {
    int len = Udp.read(incomingPacket, sizeof(incomingPacket) - 1);
    if (len > 0) {
      incomingPacket[len] = '\0';
      Serial.printf("Received JSON: %s\n", incomingPacket);

      StaticJsonDocument<512> doc;
      DeserializationError error = deserializeJson(doc, incomingPacket);
      if (error) {
        Serial.print("JSON parse error: ");
        Serial.println(error.f_str());
        return;
      }

      JsonArray keys = doc["keys"];
      JsonArray values = doc["values"];

      for (int i = 0; i < keys.size() && i < values.size(); i++) {
        String key = keys[i].as<String>();
        float value = values[i].as<float>();

        if (key.startsWith("servo")) {
          int index = key.substring(5).toInt() - 1;
          if (index >= 0 && index < NUM_SERVOS) {
            value = constrain(value, 0, 180);

            float delta = abs(value - currentAngles[index]);
            if (delta < 1.0) {
              // 小角度直接跳转
              servos[index].write(value);
              currentAngles[index] = value;
              isMoving[index] = false;
              Serial.printf("servo%d direct jump to %.2f\n", index + 1, value);
            } else {
              // 设置新插值路径
              startAngles[index] = currentAngles[index];
              targetAngles[index] = value;
              startTime[index] = millis();
              isMoving[index] = true;
              durations[index] = fmap(delta, 1.0, 90.0, minDuration, maxDuration);
              durations[index] = constrain(durations[index], minDuration, maxDuration);

              Serial.printf("servo%d set target=%.2f (duration=%.0f ms)\n", index + 1, value, durations[index]);
            }
          }
        }
      }
    }
  }

  // -------------------- 插值更新 --------------------
  unsigned long now = millis();
  if (now - lastUpdateTime < minStepTime) return;
  lastUpdateTime = now;

  for (int i = 0; i < NUM_SERVOS; i++) {
    if (!isMoving[i]) continue;

    float elapsed = now - startTime[i];
    float duration = durations[i];
    if (elapsed >= duration) {
      currentAngles[i] = targetAngles[i];
      servos[i].write(targetAngles[i]);
      isMoving[i] = false;
      Serial.printf("servo%d done → %.2f\n", i + 1, targetAngles[i]);
      continue;
    }

    float t0 = duration / 2.0;
    float delta = targetAngles[i] - startAngles[i];
    float progress = 1.0 / (1.0 + exp(-k * (elapsed - t0)));
    float angle = startAngles[i] + delta * progress;

    angle = constrain(angle, 0, 180);
    servos[i].write(angle);
    currentAngles[i] = angle;

    Serial.printf("servo%d = %.2f (%.0fms/%.0fms)\n", i + 1, angle, elapsed, duration);
  }
}
