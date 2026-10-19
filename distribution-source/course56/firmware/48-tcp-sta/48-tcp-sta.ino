#include "course_tcp.h"
constexpr char WIFI_SSID[]="YOUR_CLASSROOM_SSID";
constexpr char WIFI_PASSWORD[]="YOUR_CLASSROOM_PASSWORD";
bool serverStarted=false;
uint32_t lastReconnect=0;
void setup() {
  Serial.begin(115200); initBoard(); WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID,WIFI_PASSWORD); lastReconnect=millis();
  Serial.println("Joining classroom Wi-Fi without a blocking wait...");
}
void loop() {
  sampleInputs();
  if (WiFi.status()==WL_CONNECTED) {
    if (!serverStarted) {courseServer.begin(); serverStarted=true; Serial.print("Phone must use TCP "); Serial.print(WiFi.localIP()); Serial.println(":9000 v1");}
    serviceTcp(false);
  } else {
    if (serverStarted) {activeClient.stop(); courseServer.end(); resetClientProtocol(); serverStarted=false;}
    if (static_cast<uint32_t>(millis()-lastReconnect)>=10000) {lastReconnect=millis(); WiFi.reconnect(); Serial.println("Wi-Fi retry; check SSID/password/router");}
  }
}
