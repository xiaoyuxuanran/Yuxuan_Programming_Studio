// Lesson43: USB serial terminal on the COMPUTER, 115200 baud, LF ending.
#include "course_board.h"
yx::LineReader serialLines;
void setup() {
  Serial.begin(115200); initBoard();
  Serial.println("YX lesson43 serial protocol ready; use LF, 115200 baud");
}
void loop() {
  sampleInputs();
  while (Serial.available()) serialLines.feed(static_cast<char>(Serial.read()),
    [](const std::string &line){Serial.println(commandV1(line).c_str());},
    [](){Serial.println("ERR,TOO_LONG");});
}
