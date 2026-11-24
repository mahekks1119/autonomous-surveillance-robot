#define BLYNK_TEMPLATE_ID "TMPL3gtL43D8Z"
#define BLYNK_TEMPLATE_NAME "Mission Hardware"
#define BLYNK_AUTH_TOKEN "WDll1hN6tpeeRHnRt7PzdvQfIJUKN7zD"

#include <WiFi.h>
#include <BlynkSimpleEsp32.h>
#include <ESP32Servo.h>

// ---------------- WIFI ----------------
const char* ssid = "ms";
const char* password = "lalala11";

// ---------------- PINS ----------------
#define TRIG_PIN 5
#define ECHO_PIN 18
//#define PIR_PIN 27
#define SERVO_PIN 13
//#define VOLTAGE_PIN 34

#define IN1 14
#define IN2 12
#define IN3 26
#define IN4 25
#define ENA 33
#define ENB 32

// ---------------- VARIABLES ----------------
int motorSpeed = 200;
int stepCount = 0;
int maxSteps = 10;
int column = 1;

float distance;
//float batteryVoltage;

bool humanDetected = false;
bool servoActive = false;
bool faceReached = false;
bool robotEnabled = false;

int yoloDirection = 0;

// SERVO
Servo myServo;
int servoAngle = 0;
bool sweepForward = true;

// ---------------- BLYNK CONTROL ----------------
BLYNK_WRITE(V0) {
  robotEnabled = param.asInt();

  if (!robotEnabled) {
    stopMotors();
    Serial.println("🔴 ROBOT STOPPED");
  } else {
    Serial.println("🟢 ROBOT STARTED");
  }
}

// ---------------- SAFE DELAY ----------------
void safeDelay(int timeMs) {
  int elapsed = 0;
  while (elapsed < timeMs) {
    Blynk.run();
    delay(10);
    elapsed += 10;
  }
}

// ---------------- MOTOR ----------------
void setSpeed(int s) {
  analogWrite(ENA, s);
  analogWrite(ENB, s);
}

void moveForward() {
  setSpeed(motorSpeed);
  digitalWrite(IN1, LOW); digitalWrite(IN2, HIGH);
  digitalWrite(IN3, LOW); digitalWrite(IN4, HIGH);
}

void turnLeft() {
  setSpeed(motorSpeed);
  digitalWrite(IN1, LOW); digitalWrite(IN2, HIGH);
  digitalWrite(IN3, HIGH); digitalWrite(IN4, LOW);
}

void turnRight() {
  setSpeed(motorSpeed);
  digitalWrite(IN1, HIGH); digitalWrite(IN2, LOW);
  digitalWrite(IN3, LOW); digitalWrite(IN4, HIGH);
}

void stopMotors() {
  analogWrite(ENA, 0);
  analogWrite(ENB, 0);
}

// ---------------- U-TURNS ----------------
void uTurnRight() {
  turnRight(); safeDelay(600);
  moveForward(); safeDelay(300);
  turnRight(); safeDelay(700);
  stopMotors(); safeDelay(300);
}

void uTurnLeft() {
  turnLeft(); safeDelay(500);
  moveForward(); safeDelay(300);
  turnLeft(); safeDelay(600);
  stopMotors(); safeDelay(300);
}

// ---------------- ULTRASONIC ----------------
float getDistance() {
  digitalWrite(TRIG_PIN, LOW);
  delayMicroseconds(2);
  digitalWrite(TRIG_PIN, HIGH);
  delayMicroseconds(10);
  digitalWrite(TRIG_PIN, LOW);

  long duration = pulseIn(ECHO_PIN, HIGH);
  return duration * 0.034 / 2;
}

// ---------------- BATTERY ----------------
float readBatteryVoltage() {
  int raw = analogRead(VOLTAGE_PIN);
  float voltage = (raw / 4095.0) * 3.3;
  return voltage * 5.0;
}

// ---------------- SERVO ----------------
void handleServo() {

  if (faceReached) {
    myServo.write(0);
    Serial.println("🎯 Servo Reset");
    return;
  }

  if (servoActive) {

    if (sweepForward) {
      servoAngle += 5;
      if (servoAngle >= 120) sweepForward = false;
    } else {
      servoAngle -= 5;
      if (servoAngle <= 0) sweepForward = true;
    }

    myServo.write(servoAngle);

    Serial.print("Servo Angle: ");
    Serial.println(servoAngle);

    // FIXED DELAY
    for (int i = 0; i < 5; i++) {
      Blynk.run();
      delay(10);
    }
  }
}

void handleHumanDetection() {

  static int detectCount = 0;
  static int noDetectCount = 0;

  bool pirState = digitalRead(PIR_PIN);

  // ✅ FILTER: require continuous detection
  if (pirState) {
    detectCount++;
    noDetectCount = 0;
  } else {
    noDetectCount++;
    detectCount = 0;
  }

  // Trigger only if stable HIGH
  if (detectCount >= 5) {   // adjust sensitivity here

    humanDetected = true;

    Serial.println("🧍 HUMAN DETECTED (CONFIRMED)");
    Blynk.virtualWrite(V5, "YES");

    stopMotors();
    safeDelay(1500);

    int center = 90;

    for (int pos = center; pos <= 150; pos += 2) {
      myServo.write(pos);
      Blynk.run();
      delay(15);
    }

    for (int pos = 150; pos >= center; pos -= 2) {
      myServo.write(pos);
      Blynk.run();
      delay(15);
    }

    for (int pos = center; pos >= 30; pos -= 2) {
      myServo.write(pos);
      Blynk.run();
      delay(15);
    }

    for (int pos = 30; pos <= center; pos += 2) {
      myServo.write(pos);
      Blynk.run();
      delay(15);
    }

    Serial.println("✅ Servo Scan Complete");

    // Wait until human gone (filtered)
    while (detectCount >= 3) {
      Blynk.run();
      delay(50);

      if (digitalRead(PIR_PIN)) detectCount++;
      else detectCount--;
    }

  } 
  else if (noDetectCount >= 5) {

    humanDetected = false;
    Blynk.virtualWrite(V5, "NO");
  }
}

// void handleHumanDetection() {

//   humanDetected = digitalRead(PIR_PIN);

//   if (humanDetected) {

//     Serial.println("🧍 HUMAN DETECTED");
//     Blynk.virtualWrite(V5, "YES");

//     // ✅ STEP 1: STOP ROBOT
//     stopMotors();

//     // ✅ STEP 2: WAIT (>1000ms)
//     safeDelay(1500);

//     // ✅ STEP 3: SERVO MOVEMENT SEQUENCE

//     // Center position
//     int center = 90;

//     // Move: 90 → 150 (0 → +60)
//     for (int pos = center; pos <= 150; pos += 2) {
//       myServo.write(pos);
//       Serial.print("Servo: "); Serial.println(pos);
//       Blynk.run();
//       delay(15);
//     }

//     // Move: 150 → 90
//     for (int pos = 150; pos >= center; pos -= 2) {
//       myServo.write(pos);
//       Serial.print("Servo: "); Serial.println(pos);
//       Blynk.run();
//       delay(15);
//     }

//     // Move: 90 → 30 (0 → -60)
//     for (int pos = center; pos >= 30; pos -= 2) {
//       myServo.write(pos);
//       Serial.print("Servo: "); Serial.println(pos);
//       Blynk.run();
//       delay(15);
//     }

//     // Return to center (optional but recommended)
//     for (int pos = 30; pos <= center; pos += 2) {
//       myServo.write(pos);
//       Blynk.run();
//       delay(15);
//     }

//     Serial.println("✅ Servo Scan Complete");

//     // Keep robot stopped until human gone
//     while (digitalRead(PIR_PIN)) {
//       Blynk.run();
//       delay(50);
//     }

//   } else {
//     Blynk.virtualWrite(V5, "NO");
//   }
// }

// // ---------------- HUMAN ----------------
// void handleHumanDetection() {

//   humanDetected = digitalRead(PIR_PIN);

//   if (humanDetected) {

//     Serial.println("🧍 HUMAN DETECTED");
//     Blynk.virtualWrite(V5, "YES");

//     stopMotors();
//     servoActive = true;

//     safeDelay(1000);

//     while (humanDetected && !faceReached) {

//       Blynk.run();

//       yoloDirection = 0;

//       if (yoloDirection == 0) moveForward();
//       else if (yoloDirection == 1) turnLeft();
//       else if (yoloDirection == 2) turnRight();

//       handleServo();

//       humanDetected = digitalRead(PIR_PIN);

//       delay(10);
//     }

//     if (faceReached) {
//       stopMotors();
//       servoActive = false;
//     }

//   } else {
//     Blynk.virtualWrite(V5, "NO");
//   }
// }

// ---------------- OBSTACLE ----------------
void avoidObstacle() {

  Serial.println("🚧 OBSTACLE AVOIDING");

  stopMotors(); safeDelay(300);

  turnRight(); safeDelay(500);
  moveForward(); safeDelay(800);

  turnLeft(); safeDelay(500);
  moveForward(); safeDelay(1200);

  turnLeft(); safeDelay(500);
  moveForward(); safeDelay(800);

  turnRight(); safeDelay(500);
  moveForward(); safeDelay(500);

  stopMotors();
}

// ---------------- VOLTAGE ----------------
void handleVoltage() {

  batteryVoltage = readBatteryVoltage();

  Serial.print("🔋 Voltage: ");
  Serial.println(batteryVoltage);

  Blynk.virtualWrite(V1, batteryVoltage);

  if (batteryVoltage < 4.0) {
    Blynk.virtualWrite(V2, "LOW");
  } else if (batteryVoltage > 8.0) {
    Blynk.virtualWrite(V2, "HIGH");
  } else {
    Blynk.virtualWrite(V2, "NORMAL");
  }
}

// ---------------- SETUP ----------------
void setup() {

  Serial.begin(115200);

  pinMode(TRIG_PIN, OUTPUT);
  pinMode(ECHO_PIN, INPUT);
  pinMode(PIR_PIN, INPUT);
  pinMode(VOLTAGE_PIN, INPUT);

  pinMode(IN1, OUTPUT);
  pinMode(IN2, OUTPUT);
  pinMode(IN3, OUTPUT);
  pinMode(IN4, OUTPUT);
  pinMode(ENA, OUTPUT);
  pinMode(ENB, OUTPUT);

  myServo.attach(SERVO_PIN);

  // ✅ STABLE WIFI INIT
  WiFi.begin(ssid, password);
  Serial.print("Connecting WiFi");

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println("\n✅ WiFi Connected");

  Blynk.config(BLYNK_AUTH_TOKEN);
  Blynk.connect();
}

// ---------------- LOOP ----------------
void loop() {

  Blynk.run();

  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("⚠️ WiFi Lost!");
  }

  if (!robotEnabled) return;

  distance = getDistance();

  Serial.print("📏 Distance: ");
  Serial.println(distance);

  Blynk.virtualWrite(V3, distance);
  Blynk.virtualWrite(V4, distance < 40 ? "OBSTACLE" : "CLEAR");

  handleVoltage();

  // PRIORITY 1: HUMAN
  handleHumanDetection();
  if (faceReached) return;
  if (humanDetected) return;

  // PRIORITY 2: OBSTACLE
  if (distance < 40) {
    avoidObstacle();
    return;
  }

  // NORMAL ZIGZAG
  moveForward();
  safeDelay(500);
  stepCount++;

  if (stepCount >= maxSteps) {

    stopMotors();
    safeDelay(300);

    if (column % 2 == 1) uTurnRight();
    else uTurnLeft();

    stepCount = 0;
    column++;
  }
}