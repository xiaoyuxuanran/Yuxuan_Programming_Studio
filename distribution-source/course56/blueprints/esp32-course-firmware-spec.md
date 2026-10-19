# 第43～50课 ESP32 配套固件与协议规格

2026-10-18核对官方主源和平台内扩展元数据。本文件是制作与验收规格，不表示硬件已接线实测。主教学目标是手机APP，教师课前烧录配套固件并完成实物联调。不得把桌面模拟器结果标为手机/ESP32测试。

## 芯片、开发板与电气约束

默认板：**原始ESP32**（ESP32-WROOM系列的DevKit），具有经典蓝牙SPP和BLE。ESP32-C3与ESP32-S3仅支持BLE，**不能用于第44/45课的BluetoothSerial/SPP固件**。第46课BLE可以移植到C3/S3，但引脚、板型与USB串口设置必须分别配置，不能沿用原始ESP32接线作为通用引脚表。第47～50课Wi-Fi原则上可移植，参考编译目标仍为原始ESP32。

默认接线：

| 项目 | 原始ESP32引脚 | 连接及约束 |
|---|---|---|
| LED输出 | GPIO23 | 引脚→330Ω限流电阻→LED正极，LED负极→GND；上电默认熄灭；不用不确定型号的板载LED |
| 电位器 | GPIO34（ADC1） | 两端3.3V/GND，滑端GPIO34；输入范围不得超过板上3.3V供电；不接5V |
| 实体按钮 | GPIO27 | 引脚接按钮一端，另一端GND；`INPUT_PULLUP`；0按下、1松开；20ms软件去抖 |
| 固件调试 | USB串口 | 115200，USB数据线；不得把供电线当数据线 |

GPIO34为只输入且无内部上下拉，适合本示例ADC，不可拿来驱动LED。Wi-Fi同时使用时选ADC1避免原始ESP32的ADC2资源限制。GPIO6～11通常用于flash，启动绑带脚也不随意接会改变启动电平的外设。所有外接模块共地，GPIO为3.3V逻辑，不直接接入5V信号；本课程只控制限流LED，不让GPIO直接驱动电机、继电器线圈或市电负载。

读数`adc`为默认12位原始值0～4095（固件显式`analogReadResolution(12)`）；不称其为精确电压、温度或湿度。ADC映射百分比只是相对旋钮位置。PWM范围0～255；频率5000Hz、分辨率8位。

## 固件文件划分

1. `43-serial-protocol/43-serial-protocol.ino`：Serial115200接收v1行协议，LED、PWM、GET、PING。
2. `44-45-classic-spp/44-45-classic-spp.ino`：原始ESP32，`BluetoothSerial.h`，广播/配对名`YX-ESP32-SPP`；Serial同时提供调试，SPP使用同一解析器。
3. `46-ble-led/46-ble-led.ino`：Arduino核心自带BLE API，广播`YX-ESP32-BLE`，仅短字符串开关与通知，协议与流式SPP区分。
4. `47-tcp-ap/47-tcp-ap.ino`：Wi-Fi SoftAP `YX-ESP32-AP`，教学口令`YXclass88`（仅示范；按小组更改），明确配置IP 192.168.4.1/24，TCP9000，v1协议。
5. `48-tcp-sta/48-tcp-sta.ino`：Wi-Fi Station，配置占位SSID/PASSWORD，串口打印分配IP，TCP9000，v1协议。
6. `49-50-tcp-reliable/49-50-tcp-reliable.ino`：默认STA（可编译配置AP），TCP9000，v2序号协议、重复请求缓存；v1与v2不混用。

共享解析器应复制进每个独立草图文件夹或使用明确可打包的本地头文件；不能让分发包依赖工作区外的私有绝对路径。全局变量、引脚和网络模式都在文件顶部有注释。兼容平台实际Arduino-ESP32核心版本：核心2.x使用`ledcSetup/channel`、`ledcAttachPin`、`ledcWrite(channel,duty)`；核心3.x使用`ledcAttach(pin,freq,resolution)`、`ledcWrite(pin,duty)`。通过`ESP_ARDUINO_VERSION_MAJOR`条件编译提供两条路径，并在验证说明记录实际编译核心版本，不把只在最新版能编译写成全版本支持。

固件loop不用长时间阻塞`readStringUntil`或无限等待Wi-Fi。字节到达则逐字节入缓存，LF结束才解析；保留下一条半行；移除行尾CR。每条最大64个ASCII字符（不含LF），溢出丢弃至下一LF并返回`ERR,TOO_LONG\n`。先校验字段/范围，成功才执行，未知命令不改输出。定时采样/按钮去抖用millis差值，避免大delay。TCP每次仅1个活动客户端，新连接明确替换或拒绝旧连接并记录；断开清连接缓存，重连默认LED关/PWM0或保留需在文档明确，本规格规定保留输出、清协议等待。

## v1文本行协议（43、44、45、47、48）

UTF-8的ASCII子集，逗号分字段，**一条命令以字节LF(10)结束**。文档中的`\n`表示LF，不能发送反斜线+n两个字符代替。允许CRLF，解析前移除CR。协议无空格修复魔法，APP按精确格式发送。

| 请求（+LF） | 应答（+LF） | 执行规则 |
|---|---|---|
| `LED,1` | `OK,LED,1` | 数字输出为开；确认内部led=1，pwm=255 |
| `LED,0` | `OK,LED,0` | 输出关；led=0，pwm=0 |
| `PWM,128` | `OK,PWM,128` | 整数0..255；led为pwm>0；设置实际PWM |
| `GET` | `STATE,1,128,2048,0` | 依次led、pwm、adc、button；示例ADC值不是固定真实读数 |
| `PING` | `PONG` | 不改设备状态 |
| `LED,2` / `PWM,abc` / `PWM,256` | `ERR,BAD_VALUE` | 不执行、不改变状态 |
| 未知命令或错误字段数 | `ERR,BAD_CMD` | 不执行 |

原生BluetoothClient不提供Connected/Disconnected事件。系统先配对，APP `AddressesAndNames`给ListPicker；Connect返回bool决定成功。轮询IsConnected，读取`BytesAvailableToReceive`确切数量，`ReceiveText(数量)`追加到APP缓存；不要在只有半行时使用`ReceiveText(-1)`等待LF。组帧循环处理所有完整LF行，APP缓存上限512字符。主动断开关轮询、清缓存、禁用控制。

## 第46课 BLE GATT短消息

本平台内扩展类型`edu.mit.appinventor.ble.BluetoothLE`，版本`20230728`，实际AIX内components.json已核对。将AIX完整打包至各AIA的external_comps，包含许可与图标，不依赖用户再次安装。

- 广播名`YX-ESP32-BLE`。
- 服务：`6e400001-b5a3-f393-e0a9-e50e24dcca9e`。
- RX写特征：`6e400002-b5a3-f393-e0a9-e50e24dcca9e`，WRITE，接收UTF-8短字符串`0`或`1`，不带LF，不带NUL。
- TX通知特征：`6e400003-b5a3-f393-e0a9-e50e24dcca9e`，READ|NOTIFY，含CCCD；值为`LED,0`或`LED,1`，遇非法写返回`ERR`通知。
- BLE每次写入独立处理，不称作TCP字节流。消息小于20字节，不要求提高MTU。连接后支持读当前TX状态；收到合法写先执行再通知。
- 断开后重新开始广播；上电LED关。

APP `StartScanning`；`DeviceFound`更新设备列表；5秒后`StopScanning`。本地扩展`DeviceList`属性类型为text，应放入ListPicker.ElementsFromString，连接用`Connect(SelectionIndex)`，列表与扫描索引保持一致。Connected里`RegisterForStrings(serviceUuid,txUuid,false)`；`NullTerminateStrings=false`；发送`WriteStringsWithResponse(serviceUuid,rxUuid,false,含文字"1"的单项列表)`。`StringsReceived(serviceUuid,characteristicUuid,stringValues)`核对UUID后逐条解析列表。`StringsWritten`只是写完成，不能直接当LED应用层成功。

Android蓝牙权限随版本变化；本地扩展2023构建，课堂需验证目标Android版本的扫描/连接权限并处理PermissionDenied，不宣称所有手机免权限。BLE扫描与经典配对列表不同。

## TCP扩展真实契约

平台内 `com.gmail.at.moicjarod.ClientSocketAI2Ext`，v4。真实方法：`Connect()`、`Disconnect()`、`SendData(data:text)`；真实事件：`DataReceived(data:text)`、`RemoteConnectionClosed()`。**没有Connected、ConnectionFailed或Error事件**。属性`ServerAddress:text`、`ServerPort:text`、`TimeoutMs:number`、`HexaStringMode:boolean`、`ConnectionState:read-only boolean`。连接状态用Clock轮询，在状态变化时更新界面；通用组件异常通过Screen.ErrorOccurred恢复。TCP实际收到片段的分帧方式需用拆包/连包脚本实测该扩展，不能仅凭方法名推断。

## v2可靠协议（49、50）

格式：`seq|v1命令\n`，seq为1..2147483647整数。应答`seq|v1应答\n`。例：`12|LED,1\n`→`12|OK,LED,1\n`。命令最长64字符包括序号，不含LF。一次只允许一条待确认命令，不主动推送无序号telemetry；GET成功即以STATE回复并完成该序号。

固件针对当前连接保存最近一条`seq+command+reply`。同seq同command重复到达，返回缓存reply，不重复执行。相同seq不同command返回`seq|ERR,SEQ_REUSE`。旧序号拒绝或返回`ERR,STALE_SEQ`，连接重建清缓存后APP也清等待并从1或新会话序号开始。APP等待1500ms未确认只重发**同一原文**一次；再次超时标记“结果未确认”，不显示设备未执行。这里只使用幂等的LED/PWM设置与GET，不拓展为无幂等保护的累计/扣费指令。

APP接收缓冲按LF `while`提取。先校验序号/分隔符，再处理应答；只有等待序号匹配才清等待。旧应答记日志而不改变当前命令状态。匹配ERR也结束等待但显示失败。断开时清等待与半行，不自动无限重连。日志保留最近20行。第50课收到确认后保存本地接收时间，超过10秒标记旧状态，不称作设备实时状态。

## 无硬件也可复现的验证与硬件验证边界

制作代理提供标准库Python TCP协议测试服务，与相同v1/v2命令匹配：可把回复拆成`12|OK,LE`和`D,1\n`；可把两条完整应答一次发送；可延迟1500ms以上；可重复旧序号；可关闭连接。只能称为TCP解析/可靠性模拟，不能冒充ESP32或蓝牙实物。

固件应做实际编译（记录板型与核心版本）；解析器做合法/非法/越界/半行/连行/溢出测试。硬件LED、PWM、电位器、按键、SPP、BLE和Wi-Fi接入保留教师检查表，未做则写“未进行硬件实测”。用户已明确不需要Android真机验证，不擅自声称完成。

## 官方证据与信心

| 结论 | 官方依据 | 信心与范围 |
|---|---|---|
| BluetoothSerial为Classic，SPP仅原始ESP32 | https://docs.espressif.com/projects/arduino-esp32/en/latest/api/bluetooth.html （示例的CONFIG_BT_SPP_ENABLED检查） | 高；不依据通用ESP-IDF导航中“两个host stack”推断芯片硬件支持 |
| C3仅BLE | https://www.espressif.com/sites/default/files/documentation/esp32-c3_datasheet_en.pdf （v2.4，第1～3页） | 高；产品概览与Bluetooth特性明确LE |
| S3仅BLE | https://www.espressif.com/sites/default/files/documentation/esp32-s3_datasheet_en.pdf （v2.2，第1～3页） | 高；同上 |
| 原始ESP32 GPIO34只输入、无内部上下拉；ADC2与Wi-Fi限制 | https://docs.espressif.com/projects/esp-idf/en/stable/esp32/api-reference/peripherals/gpio.html | 高；仅原始ESP32引脚表 |
| SoftAP/Station API | https://docs.espressif.com/projects/arduino-esp32/en/latest/api/wifi.html | 高；具体板型配置仍以实际核心编译为准 |
| ADC读数与分辨率 | https://docs.espressif.com/projects/arduino-esp32/en/latest/api/adc.html | 高；精确电压需另做校准，本课不宣称 |
| LEDC核心API | https://docs.espressif.com/projects/arduino-esp32/en/latest/api/ledc.html | 高；当前文档偏核心3.x，兼容代码应记录实际版本 |
| MIT BLE方法与事件 | https://iot.appinventor.mit.edu/iot/reference/bluetoothle | 高；并核对平台AIX元数据，避免仅靠网上新版本 |
| BluetoothClient为SPP、权限与方法 | https://ai2.appinventor.mit.edu/reference/components/connectivity.html#BluetoothClient | 高；Android手机权限仍需课堂验证 |

数据手册读取遵循本机`datasheets`技能的证据/信心区分；本任务无原理图和具体芯片封装引脚核查，因此不生成假装完整的MPN抽取缓存。参考DevKit板卡接线不等于裸芯片管脚号。
