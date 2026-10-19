#include "course_tcp.h"
constexpr char AP_SSID[]="YX-ESP32-AP";
constexpr char AP_PASSWORD[]="YXclass88"; // classroom example; change per group
void setup() {
  Serial.begin(115200); initBoard(); WiFi.mode(WIFI_AP);
  WiFi.softAPConfig(IPAddress(192,168,4,1),IPAddress(192,168,4,1),IPAddress(255,255,255,0));
  if (!WiFi.softAP(AP_SSID,AP_PASSWORD)) {Serial.println("SoftAP start failed"); return;}
  courseServer.begin();
  Serial.print("Join YX-ESP32-AP; TCP "); Serial.print(WiFi.softAPIP()); Serial.println(":9000 v1");
}
void loop() {sampleInputs(); serviceTcp(false);}
