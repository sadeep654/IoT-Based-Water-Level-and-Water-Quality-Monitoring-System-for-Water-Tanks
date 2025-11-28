/* ESP32 Water Level & Quality -> Blynk
   - Ultrasonic HC-SR04
   - pH (analog)
   - Turbidity (analog)
   - Relay for pump (controlled by dashboard V1)
   - Values sent to Blynk virtual pins V2 (level), V3 (gauge), V4 (pH), V5 (turbidity)
   - Notifications via Blynk.notify on alarms

   Calibrate PH and turbidity constants for your sensors.
*/

#define BLYNK_PRINT Serial
#include <WiFi.h>
#include <BlynkSimpleEsp32.h>

char auth[] = "YOUR_BLYNK_AUTH_TOKEN";     // <-- put your Blynk auth token
char ssid[] = "YOUR_WIFI_SSID";
char pass[] = "YOUR_WIFI_PASSWORD";

/* ----------------- PIN ASSIGNMENTS ----------------- */
// Ultrasonic
const int TRIG_PIN = 18;
const int ECHO_PIN = 19;

// Analog sensors (ESP32 ADC1 pins)
const int PH_PIN = 34;    // ADC1_CH6
const int TURB_PIN = 35;  // ADC1_CH7

// Relay
const int RELAY_PIN = 5;

// LEDs / Buzzer (optional)
const int LED_RED = 16;
const int LED_YELLOW = 4;
const int LED_GREEN = 2;
const int BUZZER_PIN = 17;

/* ----------------- PARAMETERS ----------------- */
const float TANK_DEPTH_CM = 100.0;         // set to your tank depth
const float LEVEL_LOW_THRESHOLD_CM = 10.0; // low-water alarm
const float LEVEL_OVERFLOW_THRESHOLD_CM = TANK_DEPTH_CM - 5.0; // near top

// ADC scaling for ESP32: analogRead returns 0-4095 (0..Vref~3.3V)
const int ADC_MAX = 4095;
const float ADC_VREF = 3.3;

// pH calibration (example, must calibrate)
const float PH_OFFSET = 2.5;   // example offset
const float PH_SLOPE = -3.0;   // example slope

// Turbidity calibration raw->% (example)
const int TURB_CLEAN_ADC = 300;
const int TURB_DIRTY_ADC = 3500;

/* ----------------- Timers ----------------- */
unsigned long lastReadMs = 0;
const unsigned long READ_INTERVAL_MS = 2000; // 2 seconds between sensor reads

// For rate-limiting notifications
unsigned long lastNotifyMs = 0;
const unsigned long NOTIFY_COOLDOWN_MS = 30UL * 60UL * 1000UL; // 30 min

// Blynk virtual pins
#define VPIN_POWER   V1
#define VPIN_LEVELNUM V2
#define VPIN_LEVELGAUGE V3
#define VPIN_PH V4
#define VPIN_TURB V5

// store pump state
bool pumpOn = false;

/* ----------------- setup ----------------- */
BlynkTimer timer;

void setup() {
  Serial.begin(115200);
  pinMode(TRIG_PIN, OUTPUT);
  pinMode(ECHO_PIN, INPUT);
  pinMode(RELAY_PIN, OUTPUT);
  pinMode(LED_RED, OUTPUT);
  pinMode(LED_YELLOW, OUTPUT);
  pinMode(LED_GREEN, OUTPUT);
  pinMode(BUZZER_PIN, OUTPUT);

  digitalWrite(RELAY_PIN, LOW); // pump off (active HIGH assumed)
  digitalWrite(LED_RED, LOW);
  digitalWrite(LED_YELLOW, LOW);
  digitalWrite(LED_GREEN, LOW);
  digitalWrite(BUZZER_PIN, LOW);

  // connect to WiFi + Blynk
  Blynk.begin(auth, ssid, pass);

  // schedule recurring sensor reads
  timer.setInterval(READ_INTERVAL_MS, readAndSendSensors);
}

/* ----------------- Blynk handler: remote power button ----------------- */
// Write handler for virtual pin V1 (switch) - sets pump state
BLYNK_WRITE(VPIN_POWER) {
  int value = param.asInt(); // 0 or 1
  pumpOn = (value == 1);
  digitalWrite(RELAY_PIN, pumpOn ? HIGH : LOW);
  updateLedByPump(pumpOn);
  // ack back the numeric label or status if you want:
  Blynk.virtualWrite(VPIN_POWER, pumpOn ? 1 : 0);
}

/* ----------------- core loop ----------------- */
void loop() {
  Blynk.run();
  timer.run();
}

/* ----------------- sensor + send ----------------- */
void readAndSendSensors() {
  float distanceCm = readUltrasonicCm();
  float levelCm = TANK_DEPTH_CM - distanceCm;
  if (levelCm < 0) levelCm = 0;
  if (levelCm > TANK_DEPTH_CM) levelCm = TANK_DEPTH_CM;

  float phValue = readPH();
  int turbAdc = analogRead(TURB_PIN);
  float turbPercent = map(turbAdc, TURB_CLEAN_ADC, TURB_DIRTY_ADC, 0, 100);
  turbPercent = constrain(turbPercent, 0, 100);

  // send to dashboard
  Blynk.virtualWrite(VPIN_LEVELNUM, levelCm);       // text value
  Blynk.virtualWrite(VPIN_LEVELGAUGE, levelCm);     // gauge expects numeric
  Blynk.virtualWrite(VPIN_PH, phValue);
  Blynk.virtualWrite(VPIN_TURB, turbPercent);

  Serial.printf("Level: %.1f cm, pH: %.2f, turb ADC: %d (%.0f%%)\n",
                levelCm, phValue, turbAdc, turbPercent);

  // status LEDs and alarms
  handleStatusAndAlarms(levelCm, phValue, turbPercent);
}

/* ----------------- ultrasonic read ----------------- */
float readUltrasonicCm() {
  digitalWrite(TRIG_PIN, LOW);
  delayMicroseconds(2);
  digitalWrite(TRIG_PIN, HIGH);
  delayMicroseconds(10);
  digitalWrite(TRIG_PIN, LOW);

  long duration = pulseIn(ECHO_PIN, HIGH, 30000); // timeout 30 ms
  if (duration == 0) return TANK_DEPTH_CM; // no echo -> assume empty

  float distanceCm = (duration / 2.0) * 0.0343; // cm (speed ~343 m/s)
  return distanceCm;
}

/* ----------------- pH reading (simple) ----------------- */
float readPH() {
  int raw = analogRead(PH_PIN);
  float voltage = (raw / (float)ADC_MAX) * ADC_VREF;
  float ph = PH_OFFSET + PH_SLOPE * voltage;
  ph = constrain(ph, 0.0, 14.0);
  return ph;
}

/* ----------------- alarms & status ----------------- */
void handleStatusAndAlarms(float levelCm, float phValue, float turbPercent) {
  // Pump-led logic: if pumpOn show green, else yellow for idle
  updateLedByPump(pumpOn);

  unsigned long now = millis();

  if (levelCm >= LEVEL_OVERFLOW_THRESHOLD_CM) {
    // overflow - red LED + buzzer + notify
    digitalWrite(LED_RED, HIGH);
    digitalWrite(LED_YELLOW, LOW);
    digitalWrite(LED_GREEN, LOW);
    buzz(3);
    if (now - lastNotifyMs > NOTIFY_COOLDOWN_MS) {
      lastNotifyMs = now;
      Blynk.notify("ALERT: Tank near overflow.");
    }
  } else if (levelCm <= LEVEL_LOW_THRESHOLD_CM) {
    // low - notify
    if (now - lastNotifyMs > NOTIFY_COOLDOWN_MS) {
      lastNotifyMs = now;
      Blynk.notify("ALERT: Water level low.");
    }
  }

  if (phValue < 6.5 || phValue > 8.5) {
    if (now - lastNotifyMs > NOTIFY_COOLDOWN_MS) {
      lastNotifyMs = now;
      Blynk.notify(String("ALERT: pH out of range: ") + String(phValue,1));
    }
    buzz(2);
  }

  if (turbPercent > 60.0) {
    if (now - lastNotifyMs > NOTIFY_COOLDOWN_MS) {
      lastNotifyMs = now;
      Blynk.notify(String("ALERT: High turbidity: ") + String((int)turbPercent) + "%");
    }
    buzz(2);
  }
}

void updateLedByPump(bool on) {
  if (on) {
    digitalWrite(LED_GREEN, HIGH);
    digitalWrite(LED_YELLOW, LOW);
    digitalWrite(LED_RED, LOW);
  } else {
    digitalWrite(LED_GREEN, LOW);
    digitalWrite(LED_YELLOW, HIGH);
    digitalWrite(LED_RED, LOW);
  }
}

void buzz(int times) {
  for (int i=0; i<times; ++i) {
    digitalWrite(BUZZER_PIN, HIGH);
    delay(150);
    digitalWrite(BUZZER_PIN, LOW);
    delay(150);
  }
}
