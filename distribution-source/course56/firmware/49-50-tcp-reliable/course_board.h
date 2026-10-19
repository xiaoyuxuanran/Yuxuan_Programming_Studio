#pragma once
#include <Arduino.h>
#include <esp_arduino_version.h>
#include "course_protocol.h"

// Reference board: ORIGINAL ESP32-WROOM DevKit, not a universal C3/S3 pinout.
constexpr int LED_PIN=23;       // GPIO -> 330 ohm -> LED anode; cathode -> GND.
constexpr int ADC_PIN=34;       // ADC1, input only; pot 3.3 V / GND / wiper.
constexpr int BUTTON_PIN=27;    // Button to GND; internal pull-up; LOW=pressed.
constexpr int PWM_CHANNEL=0;
constexpr unsigned PWM_FREQUENCY=5000;
constexpr unsigned PWM_BITS=8;
yx::State deviceState;
int rawButton=HIGH, stableButton=HIGH;
uint32_t rawChangedAt=0;

inline void writeOutput() {
#if ESP_ARDUINO_VERSION_MAJOR >= 3
  ledcWrite(LED_PIN,deviceState.pwm);
#else
  ledcWrite(PWM_CHANNEL,deviceState.pwm);
#endif
}

inline void initBoard() {
  pinMode(LED_PIN,OUTPUT); digitalWrite(LED_PIN,LOW);
  pinMode(BUTTON_PIN,INPUT_PULLUP);
  analogReadResolution(12);
#if ESP_ARDUINO_VERSION_MAJOR >= 3
  if (!ledcAttach(LED_PIN,PWM_FREQUENCY,PWM_BITS)) Serial.println("LEDC attach failed");
#else
  ledcSetup(PWM_CHANNEL,PWM_FREQUENCY,PWM_BITS); ledcAttachPin(LED_PIN,PWM_CHANNEL);
#endif
  writeOutput();
  rawButton=stableButton=digitalRead(BUTTON_PIN);
  deviceState.button=stableButton;
  rawChangedAt=millis();
}

inline void sampleInputs() {
  int now=digitalRead(BUTTON_PIN);
  if (now!=rawButton) { rawButton=now; rawChangedAt=millis(); }
  if (static_cast<uint32_t>(millis()-rawChangedAt)>=20) stableButton=rawButton;
  deviceState.button=stableButton;
  deviceState.adc=static_cast<unsigned>(analogRead(ADC_PIN));
}

inline std::string commandV1(const std::string &line) {
  sampleInputs(); auto result=yx::processV1(line,deviceState); writeOutput(); return result;
}
