#pragma once
#include <WiFi.h>
#include "course_board.h"
WiFiServer courseServer(9000);
WiFiClient activeClient;
yx::LineReader networkLines;
yx::Session sequenceSession;

inline void resetClientProtocol() {networkLines.reset(); sequenceSession.reset();}
inline void serviceTcp(bool reliable) {
  if (activeClient && !activeClient.connected()) {
    activeClient.stop(); resetClientProtocol(); Serial.println("Client disconnected; output retained");
  }
  if (courseServer.hasClient()) {
    WiFiClient newcomer=courseServer.available();
    // One active phone at a time. Explicitly reject a newcomer, do not let it
    // steal control. The active client can disconnect before another joins.
    if (activeClient && activeClient.connected()) newcomer.stop();
    else {activeClient=newcomer; resetClientProtocol(); Serial.println("Client connected");}
  }
  while (activeClient && activeClient.connected() && activeClient.available()) {
    char c=static_cast<char>(activeClient.read());
    networkLines.feed(c,[reliable](const std::string &line){
      sampleInputs();
      auto reply=reliable?sequenceSession.process(line,deviceState):yx::processV1(line,deviceState);
      writeOutput(); activeClient.print(reply.c_str()); activeClient.write('\n');
    },[reliable](){activeClient.print(reliable?"0|ERR,TOO_LONG\n":"ERR,TOO_LONG\n");});
  }
}
