#include <WiFi.h>
#include <WiFiUdp.h>
#include <ESP32Servo.h>
#include <ArduinoJson.h>

const char* ssid = "MOJOY";
const char* password = "123456789.";
const int UDP_PORT = 4210;
WiFiUDP Udp;

const int NUM_SERVOS = 2;
const int SERVO_PINS[NUM_SERVOS] = {2, 4};  // 只用 GPIO2 和 GPIO4
Servo servos[NUM_SERVOS];

char incomingPacket[512];

void setup() {
  Serial.begin(115200);

  // 舵机初始化
  for (int i = 0; i < NUM_SERVOS; i++) {
    servos[i].setPeriodHertz(50);
    servos[i].attach(SERVO_PINS[i], 500, 2400);
  }

  // WiFi 连接
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500); Serial.print(".");
  }
  Serial.println("\nWiFi connected.");
  Serial.println(WiFi.localIP());

  Udp.begin(UDP_PORT);
  Serial.printf("Listening on UDP port %d\n", UDP_PORT);
}

void loop() {
  int packetSize = Udp.parsePacket();
  if (packetSize) {
    int len = Udp.read(incomingPacket, sizeof(incomingPacket) - 1);
    if (len > 0) {
      incomingPacket[len] = '\0';
      Serial.printf("Received JSON: %s\n", incomingPacket);

      // 解析 JSON
      StaticJsonDocument<512> doc;
      DeserializationError error = deserializeJson(doc, incomingPacket);
      if (error) {
        Serial.print("JSON parse error: ");
        Serial.println(error.f_str());
        return;
      }

      // 提取 keys 和 values 数组
      JsonArray keys = doc["keys"];
      JsonArray values = doc["values"];

      for (int i = 0; i < keys.size() && i < values.size(); i++) {
        String key = keys[i].as<String>();     // e.g., "servo1"
        float angle = values[i].as<float>();   // e.g., 32.0

        // 提取舵机编号 servo1 → 0
        if (key.startsWith("servo")) {
          int index = key.substring(5).toInt() - 1;
          if (index >= 0 && index < NUM_SERVOS) {
            angle = constrain(angle, 0, 180);
            servos[index].write(angle);
            Serial.printf("%s = %.2f\n", key.c_str(), angle);
          }
        }
      }
    }
  }
}

