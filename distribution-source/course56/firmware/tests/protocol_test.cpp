#include "../shared/course_protocol.h"
#include <cassert>
#include <iostream>
#include <vector>

int main() {
  yx::State s; s.adc=2048; s.button=0;
  unsigned checks=0;
  auto expect=[&](const std::string &command,const std::string &reply) {
    assert(yx::processV1(command,s)==reply); ++checks;
  };
  expect("LED,1","OK,LED,1"); assert(s.led==1 && s.pwm==255); ++checks;
  expect("LED,0","OK,LED,0"); assert(s.led==0 && s.pwm==0); ++checks;
  expect("PWM,128","OK,PWM,128"); assert(s.led==1 && s.pwm==128); ++checks;
  expect("GET","STATE,1,128,2048,0"); expect("PING","PONG");
  for (auto bad:{"LED,2","LED,-1","LED,abc","PWM,256","PWM,","PWM,1.5","PWM,99999999999999999999999999999"}) {
    expect(bad,"ERR,BAD_VALUE"); assert(s.led==1 && s.pwm==128); ++checks;
  }
  for (auto bad:{"LED","LED,1,0","WHAT,1","led,1","GET,0",""}) expect(bad,"ERR,BAD_CMD");
  yx::Session session;
  assert(session.process("1|LED,1",s)=="1|OK,LED,1"); ++checks;
  s.pwm=17; // proves duplicate reply does not re-execute LED,1.
  assert(session.process("1|LED,1",s)=="1|OK,LED,1" && s.pwm==17); ++checks;
  assert(session.process("1|LED,0",s)=="1|ERR,SEQ_REUSE" && s.pwm==17); ++checks;
  assert(session.process("2|GET",s)=="2|STATE,1,17,2048,0"); ++checks;
  assert(session.process("1|LED,0",s)=="1|ERR,STALE_SEQ"); ++checks;
  for (auto bad:{"0|GET","-1|GET","2147483648|GET","x|GET","1|GET|X","GET"}) {assert(session.process(bad,s)=="0|ERR,BAD_SEQ"); ++checks;}
  session.reset(); assert(session.process("1|LED,0",s)=="1|OK,LED,0"); ++checks;
  yx::LineReader lines;
  std::vector<std::string> frames; unsigned overflow=0;
  auto feed=[&](const std::string &fragment) {
    for (char c:fragment) lines.feed(c,[&](const std::string &line){frames.push_back(line);},[&](){++overflow;});
  };
  feed("LED,"); assert(frames.empty()); ++checks;
  feed("1\nGET\r\nPW"); assert(frames.size()==2 && frames[0]=="LED,1" && frames[1]=="GET"); ++checks;
  feed("M,128\n"); assert(frames.back()=="PWM,128"); ++checks;
  feed(std::string(64,'A')+"\r\n"); assert(frames.back()==std::string(64,'A')); ++checks;
  auto before=frames.size(); feed(std::string(65,'B')+"\nPING\n");
  assert(overflow==1 && frames.size()==before+1 && frames.back()=="PING"); ++checks;
  feed("half"); lines.reset(); feed("GET\n"); assert(frames.back()=="GET"); ++checks;
  std::cout << "PASS " << checks << " protocol assertions (host only; no hardware)\n";
}
