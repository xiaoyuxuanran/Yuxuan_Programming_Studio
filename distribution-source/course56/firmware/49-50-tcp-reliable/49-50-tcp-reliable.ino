#include "course_tcp.h"
// 0=classroom router STA; 1=standalone SoftAP, 192.168.4.1.
#define YX_USE_SOFT_AP 0
constexpr char WIFI_SSID[]="YOUR_CLASSROOM_SSID";
constexpr char WIFI_PASSWORD[]="YOUR_CLASSROOM_PASSWORD";
bool serverStarted=false;
uint32_t lastReconnect=0;
void setup() {
  Serial.begin(115200); initBoard();
#if YX_USE_SOFT_AP
  WiFi.mode(WIFI_AP); WiFi.softAPConfig(IPAddress(192,168,4,1),IPAddress(192,168,4,1),IPAddress(255,255,255,0));
  if (WiFi.softAP("YX-ESP32-AP","YXclass88")) {courseServer.begin(); serverStarted=true; Serial.println("TCP 192.168.4.1:9000 v2 (seq|command LF)");}
#else
  WiFi.mode(WIFI_STA); WiFi.begin(WIFI_SSID,WIFI_PASSWORD); lastReconnect=millis();
#endif
}
void loop() {
  sampleInputs();
#if YX_USE_SOFT_AP
  if (serverStarted) serviceTcp(true);
#else
  if (WiFi.status()==WL_CONNECTED) {
    if (!serverStarted) {courseServer.begin(); serverStarted=true; Serial.print("TCP "); Serial.print(WiFi.localIP()); Serial.println(":9000 v2 (seq|command LF)");}
    serviceTcp(true);
  } else {
    if (serverStarted) {activeClient.stop(); courseServer.end(); resetClientProtocol(); serverStarted=false;}
    if (static_cast<uint32_t>(millis()-lastReconnect)>=10000) {lastReconnect=millis(); WiFi.reconnect(); Serial.println("Wi-Fi retry");}
  }
#endif
}
