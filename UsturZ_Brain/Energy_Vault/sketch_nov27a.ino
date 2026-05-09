/*
  ESP32 Adaptive Motor Control + Soft Start + RPM Monitoring
  - Soft start: 10 Hz → 50 Hz, har 5 sekundda +5 Hz
  - Adaptive control: Motor Current (A), Output Frequency (Hz), Supply Voltage (V)
  - RPM monitoring (VFD register)
  - FreeRTOS tasks: Feedback reading + control + heartbeat
  - Serial interface: start, stop, setfreq <Hz>, resetfault
*/

#include <ModbusMaster.h>
#include <Arduino.h>

// ---------- Hardware & Modbus ----------
HardwareSerial RS485Serial(2); // UART2: RX=16, TX=17
ModbusMaster vfd;
const uint8_t VFD_SLAVE_ID = 1;
const unsigned long MODBUS_BAUD = 9600;

const int RS485_DE_PIN = 4; // DE/RE pin for RS485

// ---------- VFD register map ----------
uint16_t REG_CMD            = 0x2000;
uint16_t REG_MODE           = 0x2001;
uint16_t REG_FREQ_SET       = 0x0001;
uint16_t REG_OUTPUT_FREQ    = 0x2103;
uint16_t REG_OUTPUT_CURRENT = 0x2104;
uint16_t REG_SUPPLY_VOLT    = 0x2102;
uint16_t REG_MOTOR_RPM      = 0x2105; // VFD RPM register

// ---------- Control parameters ----------
int desiredFreqHz = 30;
const int FREQ_MIN = 5;
const int FREQ_MAX = 50;

const float I_nominal = 10.0;
const float I_max_trip = 18.0;
const float I_warn = 12.0;
const float I_reduce_step = 2.0;

const float V_nominal = 380.0;
const float V_min_safe = 320.0;
const float V_warn = 350.0;

const float FREQ_TOLERANCE_HZ = 2.0;

float Kp = 0.5;
float Ki = 0.02;
float integrator = 0.0;
float integrator_max = 100.0;

const unsigned long CONTROL_INTERVAL_MS = 500;
const float EMA_ALPHA = 0.2;
float ema_current = 0.0;
float ema_freq = 0.0;
float ema_volt = 0.0;
float ema_rpm = 0.0;

const float MAX_HZ_RATE = 10.0;

volatile bool motorRun = false;
volatile bool fault_tripped = false;
float last_setpoint_hz = 0.0;

// ---------- SOFT START PARAMETERS ----------
float softStartFreq = 10.0;            // Start at 10 Hz
float softEndFreq   = 50.0;            // End at 50 Hz
float softStep      = 5.0;             // Every step = +5 Hz
unsigned long softInterval = 30000;     // 30 seconds
unsigned long lastSoftStep = 0;
bool softStartActive = true;           // Only runs once

// ---------- Helper functions ----------
void rs485TxEnable() { digitalWrite(RS485_DE_PIN, HIGH); delayMicroseconds(100); }
void rs485TxDisable() { delayMicroseconds(100); digitalWrite(RS485_DE_PIN, LOW); }

float regToFreqHz(uint16_t reg) { return ((float)reg) / 100.0; }
uint16_t freqHzToReg(float hz) { if (hz < 0) hz = 0; return (uint16_t)round(hz * 100.0); }
float regToCurrent(uint16_t reg) { return ((float)reg) / 10.0; }
float regToVoltage(uint16_t reg) { return ((float)reg); }
float regToRPM(uint16_t reg) { return (float)reg; } // RPM from VFD register

bool readInputRegisterUint16(uint16_t addr, uint16_t &out) {
  rs485TxDisable();
  uint8_t result = vfd.readInputRegisters(addr, 1);
  if (result == vfd.ku8MBSuccess) { out = vfd.getResponseBuffer(0); return true; }
  return false;
}

bool writeSingleRegister(uint16_t addr, uint16_t value) {
  rs485TxEnable();
  uint8_t result = vfd.writeSingleRegister(addr, value);
  rs485TxDisable();
  return (result == vfd.ku8MBSuccess);
}

// ---------- SOFT START FUNCTION ----------
void softStartControl() {
  if (!softStartActive || !motorRun) return;

  unsigned long now = millis();
  if (now - lastSoftStep >= softInterval) {
    lastSoftStep = now;

    if (softStartFreq < softEndFreq) {
      softStartFreq += softStep;
      if (softStartFreq > softEndFreq) softStartFreq = softEndFreq;

      uint16_t regVal = freqHzToReg(softStartFreq);
      writeSingleRegister(REG_FREQ_SET, regVal);

      Serial.printf("[SOFT START] Freq → %.2f Hz\n", softStartFreq);
    }

    if (softStartFreq >= softEndFreq) {
      softStartActive = false;
      Serial.println("[SOFT START] Completed! Now adaptive control continues normally.");
    }
  }
}

// ---------- Adaptive control ----------
unsigned long last_control_ms = 0;

void controlStep(float curA, float outHz, float voltV) {

  if (fault_tripped || softStartActive) return;

  unsigned long now = millis();
  if (now - last_control_ms < CONTROL_INTERVAL_MS) return;
  float dt = (now - last_control_ms) / 1000.0;
  if (dt <= 0) dt = 0.001;
  last_control_ms = now;

  ema_current = (EMA_ALPHA * curA) + (1.0 - EMA_ALPHA) * ema_current;
  ema_freq = (EMA_ALPHA * outHz) + (1.0 - EMA_ALPHA) * ema_freq;
  ema_volt = (EMA_ALPHA * voltV) + (1.0 - EMA_ALPHA) * ema_volt;

  if (ema_current >= I_max_trip) {
    Serial.println("[SAFETY] HARD TRIP - Overcurrent!");
    writeSingleRegister(REG_CMD, 0);
    motorRun = false;
    fault_tripped = true;
    return;
  }

  if (ema_volt < V_min_safe) {
    Serial.println("[SAFETY] Voltage low - reduce speed");
    desiredFreqHz = max(FREQ_MIN, desiredFreqHz - 10);
  }

  if (ema_current > I_warn) {
    desiredFreqHz = max(FREQ_MIN, desiredFreqHz - (int)I_reduce_step);
    Serial.printf("[ADAPT] High current (%.2fA). Reducing freq -> %d Hz\n", ema_current, desiredFreqHz);
  } else if (ema_current < I_nominal * 0.6) {
    desiredFreqHz = min(FREQ_MAX, desiredFreqHz + 1);
  }

  float freq_err = (float)desiredFreqHz - ema_freq;
  integrator += freq_err * Ki * dt;
  if (integrator > integrator_max) integrator = integrator_max;
  if (integrator < -integrator_max) integrator = -integrator_max;

  float pi_adjust = Kp * freq_err + integrator;
  float new_setpoint = (float)desiredFreqHz + pi_adjust;

  float max_step = MAX_HZ_RATE * dt;
  if (new_setpoint - last_setpoint_hz > max_step) new_setpoint = last_setpoint_hz + max_step;
  if (last_setpoint_hz - new_setpoint > max_step) new_setpoint = last_setpoint_hz - max_step;

  if (new_setpoint > FREQ_MAX) new_setpoint = FREQ_MAX;
  if (new_setpoint < FREQ_MIN) new_setpoint = FREQ_MIN;

  if (fabs(new_setpoint - last_setpoint_hz) >= 0.1) {
    uint16_t regVal = freqHzToReg(new_setpoint);
    if (writeSingleRegister(REG_FREQ_SET, regVal)) {
      Serial.printf("[WRITE] SetFreq -> %.2f Hz (reg=%u)\n", new_setpoint, regVal);
      last_setpoint_hz = new_setpoint;
    }
  }
}

// ---------- FreeRTOS tasks ----------
void TaskReadFeedback(void *pv) {
  (void)pv;
  while (1) {
    uint16_t raw;
    float curA = 0.0, outHz = 0.0, voltV = 0.0, rpm = 0.0;

    if(readInputRegisterUint16(REG_OUTPUT_CURRENT, raw)) curA = regToCurrent(raw);
    if(readInputRegisterUint16(REG_OUTPUT_FREQ, raw)) outHz = regToFreqHz(raw);
    if(readInputRegisterUint16(REG_SUPPLY_VOLT, raw)) voltV = regToVoltage(raw);
    if(readInputRegisterUint16(REG_MOTOR_RPM, raw)) rpm = regToRPM(raw);
    ema_rpm = rpm; // EMA not strictly needed, optional

    Serial.printf("Telemetry: I=%.2f A, F=%.2f Hz, V=%.1f V, RPM=%.0f\n", curA, outHz, voltV, rpm);

    softStartControl();
    controlStep(curA, outHz, voltV);

    vTaskDelay(300 / portTICK_PERIOD_MS);
  }
}

void TaskHeartbeat(void *pv) {
  (void)pv;
  while (1) {
    Serial.print(".");
    vTaskDelay(1000 / portTICK_PERIOD_MS);
  }
}

// ---------- Setup & loop ----------
void setup() {
  Serial.begin(115200);
  pinMode(RS485_DE_PIN, OUTPUT);
  rs485TxDisable();

  RS485Serial.begin(MODBUS_BAUD, SERIAL_8N1, 16, 17);
  vfd.begin(VFD_SLAVE_ID, RS485Serial);

  ema_current = 0.0;
  ema_freq = desiredFreqHz;
  ema_volt = V_nominal;
  ema_rpm = 0.0;

  // Soft start initial write
  uint16_t regVal = freqHzToReg(softStartFreq);
  writeSingleRegister(REG_FREQ_SET, regVal);
  Serial.printf("[SOFT START] Begin at %.2f Hz\n", softStartFreq);

  xTaskCreatePinnedToCore(TaskReadFeedback, "ReadFB", 4096, NULL, 2, NULL, 0);
  xTaskCreatePinnedToCore(TaskHeartbeat, "HB", 2048, NULL, 1, NULL, 1);

  Serial.println("Adaptive control + Soft Start + RPM monitoring started.");
}

void loop() {
  if (Serial.available()) {
    String cmd = Serial.readStringUntil('\n');
    cmd.trim();

    if (cmd.equalsIgnoreCase("start")) {
      motorRun = true;
      softStartActive = true;
      softStartFreq = 10.0;
      lastSoftStep = millis();
      writeSingleRegister(REG_CMD, 1);
      Serial.println("Motor START");
    }

    else if (cmd.equalsIgnoreCase("stop")) {
      motorRun = false;
      writeSingleRegister(REG_CMD, 0);
      Serial.println("Motor STOP");
    }

    else if (cmd.startsWith("setfreq")) {
      int hz = cmd.substring(7).toInt();
      if (hz >= FREQ_MIN && hz <= FREQ_MAX) {
        desiredFreqHz = hz;
        Serial.printf("Desired freq set to %d Hz\n", hz);
      } else Serial.println("setfreq out of range");
    }

    else if (cmd.equalsIgnoreCase("resetfault")) {
      fault_tripped = false;
      integrator = 0;
      Serial.println("Fault reset");
    }

    else Serial.println("Unknown command.");
  }

  vTaskDelay(50 / portTICK_PERIOD_MS);
}