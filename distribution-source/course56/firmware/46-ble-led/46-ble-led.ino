// MIT BluetoothLE extension: UTF-8 single-byte "0" or "1", no LF or NUL.
// Reference wiring is original ESP32-WROOM. C3/S3 require pin remapping.
#include <Arduino.h>
#include <BLEDevice.h>
#include <BLEServer.h>
#include <BLEUtils.h>
#include <BLE2902.h>
constexpr int LED_PIN=23;
constexpr char SERVICE_UUID[]="6e400001-b5a3-f393-e0a9-e50e24dcca9e";
constexpr char RX_UUID[]="6e400002-b5a3-f393-e0a9-e50e24dcca9e";
constexpr char TX_UUID[]="6e400003-b5a3-f393-e0a9-e50e24dcca9e";
BLECharacteristic *tx=nullptr;
volatile bool connected=false, restartAdvertising=false;
volatile int pendingWrite=-1;
bool ledOn=false;

class ServerEvents:public BLEServerCallbacks {
  void onConnect(BLEServer*) override {connected=true;}
  void onDisconnect(BLEServer*) override {connected=false; restartAdvertising=true;}
};
class WriteEvents:public BLECharacteristicCallbacks {
  void onWrite(BLECharacteristic *characteristic) override {
    // getValue() is std::string in core2, Arduino String in core3; both expose
    // length() and operator[]. Transfer the short command to loop(), not GPIO.
    auto value=characteristic->getValue();
    pendingWrite=value.length()==1 && (value[0]=='0'||value[0]=='1')?value[0]-'0':2;
  }
};
void setup() {
  Serial.begin(115200); pinMode(LED_PIN,OUTPUT); digitalWrite(LED_PIN,LOW);
  BLEDevice::init("YX-ESP32-BLE");
  auto server=BLEDevice::createServer(); server->setCallbacks(new ServerEvents());
  auto service=server->createService(SERVICE_UUID);
  tx=service->createCharacteristic(TX_UUID,BLECharacteristic::PROPERTY_READ|BLECharacteristic::PROPERTY_NOTIFY);
  tx->addDescriptor(new BLE2902()); tx->setValue("LED,0");
  auto rx=service->createCharacteristic(RX_UUID,BLECharacteristic::PROPERTY_WRITE);
  rx->setCallbacks(new WriteEvents()); service->start();
  auto advertising=BLEDevice::getAdvertising(); advertising->addServiceUUID(SERVICE_UUID);
  advertising->setScanResponse(true); BLEDevice::startAdvertising();
  Serial.println("YX-ESP32-BLE ready. Subscribe TX, write ASCII 0 or 1 to RX.");
}
void loop() {
  int value=pendingWrite;
  if (value>=0) {
    pendingWrite=-1;
    if (value<=1) {ledOn=value==1; digitalWrite(LED_PIN,ledOn?HIGH:LOW); tx->setValue(ledOn?"LED,1":"LED,0");}
    else tx->setValue("ERR");
    if (connected) tx->notify();
  }
  if (restartAdvertising) {restartAdvertising=false; BLEDevice::startAdvertising();}
  delay(1);  // yield to BLE task; no long blocking waits
}
