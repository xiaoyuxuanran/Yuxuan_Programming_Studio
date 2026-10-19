#pragma once
// Portable command parser: no Arduino dependencies, testable on the desktop.
#include <cstdint>
#include <string>

namespace yx {
struct State { unsigned led=0, pwm=0, adc=0, button=1; };

inline bool decimal(const std::string &s, uint32_t maximum, uint32_t &out) {
  if (s.empty()) return false;
  uint32_t n=0;
  for (char c:s) {
    if (c<'0'||c>'9') return false;
    unsigned digit=static_cast<unsigned>(c-'0');
    if (n>maximum/10 || (n==maximum/10 && digit>maximum%10)) return false;
    n=n*10+digit;
  }
  out=n; return true;
}

inline std::string processV1(const std::string &line, State &s) {
  if (line=="PING") return "PONG";
  if (line=="GET") return "STATE,"+std::to_string(s.led)+","+std::to_string(s.pwm)+","+std::to_string(s.adc)+","+std::to_string(s.button);
  auto comma=line.find(',');
  if (comma==std::string::npos || line.find(',',comma+1)!=std::string::npos) return "ERR,BAD_CMD";
  auto command=line.substr(0,comma), value=line.substr(comma+1);
  uint32_t n=0;
  if (command=="LED") {
    if (!decimal(value,1,n)) return "ERR,BAD_VALUE";
    s.led=n; s.pwm=n?255:0;
    return "OK,LED,"+std::to_string(n);
  }
  if (command=="PWM") {
    if (!decimal(value,255,n)) return "ERR,BAD_VALUE";
    s.pwm=n; s.led=n?1:0;
    return "OK,PWM,"+std::to_string(n);
  }
  return "ERR,BAD_CMD";
}

class Session {
  bool haveLast_=false;
  uint32_t lastSequence_=0;
  std::string lastCommand_, lastReply_;
public:
  void reset() { haveLast_=false; lastSequence_=0; lastCommand_.clear(); lastReply_.clear(); }
  std::string process(const std::string &line, State &state) {
    auto bar=line.find('|'); uint32_t sequence=0;
    if (bar==std::string::npos || line.find('|',bar+1)!=std::string::npos || !decimal(line.substr(0,bar),2147483647u,sequence) || sequence==0) return "0|ERR,BAD_SEQ";
    std::string command=line.substr(bar+1), prefix=std::to_string(sequence)+"|";
    if (haveLast_ && sequence==lastSequence_) return command==lastCommand_?lastReply_:prefix+"ERR,SEQ_REUSE";
    if (haveLast_ && sequence<lastSequence_) return prefix+"ERR,STALE_SEQ";
    auto reply=prefix+processV1(command,state);
    haveLast_=true; lastSequence_=sequence; lastCommand_=command; lastReply_=reply;
    return reply;
  }
};

class LineReader {
  std::string partial_;
  bool overflow_=false;
public:
  void reset() { partial_.clear(); overflow_=false; }
  // Only calls one callback when LF completes a line; retains partial chunks.
  template<class Line, class Overflow> void feed(char c, Line line, Overflow overflow) {
    if (c=='\n') {
      if (overflow_) overflow();
      else {
        if (!partial_.empty() && partial_.back()=='\r') partial_.pop_back();
        if (!partial_.empty()) line(partial_);
      }
      reset(); return;
    }
    if (overflow_) return;
    // A terminal CR is allowed in addition to the 64 command characters.
    if (partial_.size()>=64 && !(partial_.size()==64 && c=='\r')) {
      partial_.clear(); overflow_=true; return;
    }
    partial_+=c;
  }
};
}
