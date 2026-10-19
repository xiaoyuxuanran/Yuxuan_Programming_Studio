// Original ESP32-WROOM only. ESP32-C3/S3 do NOT implement Classic SPP.
#include <BluetoothSerial.h>
#include "course_board.h"
#if !defined(CONFIG_BT_SPP_ENABLED)
#error "Lessons44/45 require original ESP32 with Bluetooth Classic SPP enabled."
#endif
BluetoothSerial SerialBT;
yx::LineReader serialLines, bluetoothLines;
bool previouslyConnected=false;
void setup() {
  Serial.begin(115200); initBoard();
  if (!SerialBT.begin("YX-ESP32-SPP")) Serial.println("SPP start failed");
  Serial.println("Pair YX-ESP32-SPP in Android settings first. Protocol v1; LF.");
}
void loop() {
  sampleInputs(); bool connected=SerialBT.hasClient();
  if (connected!=previouslyConnected) {
    bluetoothLines.reset(); previouslyConnected=connected;
    Serial.println(connected?"SPP connected":"SPP disconnected; output retained");
  }
  while (SerialBT.available()) bluetoothLines.feed(static_cast<char>(SerialBT.read()),
    [](const std::string &line){SerialBT.println(commandV1(line).c_str());},
    [](){SerialBT.println("ERR,TOO_LONG");});
  while (Serial.available()) serialLines.feed(static_cast<char>(Serial.read()),
    [](const std::string &line){Serial.println(commandV1(line).c_str());},
    [](){Serial.println("ERR,TOO_LONG");});
}
