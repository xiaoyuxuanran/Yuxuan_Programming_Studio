"""Phone-side ESP32 lessons with exact extension contracts and supplied firmware."""
import json
from write_media_data_network import ROOT, DATA, entry, emit, task, question

COMMON='配套固件及接线表见firmware。参考板为原始ESP32-WROOM DevKit；LED GPIO23串330Ω，ADC1 GPIO34只接0～3.3V电位器滑端，GPIO27按钮接地，0为按下。工程导入、APK编译和桌面协议测试不能代替Android与ESP32实物联调；本次未做真机测试。'
STREAM=[['已连接','假；必须核对当前实际连接'],['接收缓存','空；保留半行，最多512字符'],['有效应答','校验完整格式后才真'],['日志','最多保留最近20条']]
V2=STREAM+[['等待序号','0表示没有待确认命令'],['重试次数','0或1；每次等待最多重试一次']]

def hardware(n,scope,states,flow,tasks,exits,blocks,**extra):
 s=json.loads((ROOT.parent/'aia'/f'lesson{n:02}/artifact-spec.json').read_text(encoding='utf8'))
 captures={i:dict(target=target,title=blocks[i][0],body=blocks[i][1]) for i,target in enumerate(s['screenshotGroups'])}
 entry(n,COMMON+' '+scope,states,flow,tasks,exits,[x[2] for x in blocks],capture_overrides=captures,**extra)

hardware(43,'本课APP生成命令并解析粘贴的应答；实际USB连接由电脑串口调试器完成，不是手机USB串口应用。LF表示一个换行字节，不能发送反斜线加n代替。',
 [['最近命令','生成的LED,0/1与末尾LF'],['有效应答','格式和范围全部正确才真']],
 ['按钮只生成请求，不宣称LED已改变','电脑115200串口发送含LF的指令','把真实应答粘贴到ReplyBox，解析后显示确认'],
 [task('补生成指令',['找到生成指令过程，参数只用0或1。','最近命令连接LED,、数值与真正LF。','更新CommandLabel中的可见说明。','观察字面\\n与换行字节的区别。'],'点开灯按钮就能说设备已经亮了吗？','不能，本课只生成请求，设备是否执行要看应答及现场观察。'),
  task('补合法应答解析',['按逗号拆分，先校验字段数量。','OK,LED要求数值0或1；STATE要求五列且全数值范围有效。','LED为0/1、PWM为0～255、ADC为0～4095、按钮为0/1。','坏数据不修改已确认状态。'],'为什么不能读完第一个字段就更新界面？','后续字段可能非法，必须全部校验通过才提交整条状态。'),
  task('用已给按钮做协议互测',['ParseButton.Click已给，追踪它怎样调用处理应答。','粘贴OK,LED,1与OK,LED,9，比较结果。','教师串口发送LED,1并记录回包；无设备时写待测。'],'ADC=2048能写成20.48摄氏度吗？','不能，它是原始ADC读数，没有温度传感器或换算标定。')],
 [question('命令末尾为什么要LF？','设备以LF识别一条命令的结束。'),question('请求与确认有什么区别？','请求表达想做的动作，应答确认设备处理结果。'),question('本课APP连接USB了吗？','没有，USB串口由电脑调试器操作，APP做协议生成与解析。')],
 [('生成一行命令',['LED,1后附真正LF。','只生成请求，等设备确认。'],'生成指令待补；字面转义标记仅用于显示说明。'),('校验完整应答',['字段数量与范围均通过才更新。','OK,LED,9不能当成功。'],'处理应答待补；无效帧不得部分覆盖旧状态。'),('粘贴解析入口',['ParseButton读取ReplyBox。','有效与无效应答成对测试。'],'入口已给，用它追踪完整处理流程。')])

hardware(44,'经典蓝牙SPP只用于具备该能力的原始ESP32；C3/S3不适用此固件。系统先配对YX-ESP32-SPP，APP再Connect建立通道，BluetoothClient不同于BLE。',STREAM,
 ['BeforePicking读取系统已配对设备列表','Connect返回真才启用控制和轮询','发送命令加LF，合法回包才更新确认'],
 [task('阅读配对设备入口',['BeforePicking已给，读取Bt.AddressesAndNames。','教师课前在系统配对YX-ESP32-SPP。','指出配对列表与当前通道连接的区别。'],'配对成功就等于APP已经连接吗？','不是，还要APP调用Connect并检查返回值。'),
  task('补连接设备过程',['先清理旧连接状态。','调用Bt.Connect(DevicePicker.Selection)。','返回真才设已连接、启用按钮和PollClock。','失败只提示，不把已连接强设为真。'],'BluetoothClient有Connected事件吗？','本地原生组件没有该事件；这里用Connect返回值及IsConnected。'),
  task('补发送命令',['同时检查已连接与Bt.IsConnected。','命令附LF，再Bt.SendText。','只显示等待应答；已给轮询按可用字节读取并分帧。','主动断开后按钮禁用，重新选择可再连接。'],'收到半行能用ReceiveText(-1)一直等吗？','本例避免阻塞，按当前可用字节数读取，再交给缓存分帧。')],
 [question('C3为何不能用这份SPP固件？','该芯片不支持此经典蓝牙SPP功能，不能用BLE代替同一通道。'),question('什么时候更新灯已开？','合法OK或STATE应答到达并校验之后。'),question('断开要清什么？','连接标志、轮询和半行缓存，并禁用控制。')],
 [('读取配对设备',['BeforePicking取得AddressesAndNames。','配对与APP连接分开。'],'本入口已给；查找目标经典SPP设备。'),('连接并核对结果',['Connect返回真才开放控制。','失败保持未连接。'],'连接设备过程待补，清理与界面恢复结构可复用。'),('发送请求并等待',['SendText发送命令加LF。','成功状态来自设备回包。'],'发送命令待补；不是按键后直接显示成功。')],
 event_overrides={'OnButton.Click':'调用发送命令(LED,1)','OffButton.Click':'调用发送命令(LED,0)'},
 procedure_overrides={'发送命令':'核对已连接及IsConnected后SendText(命令+LF)，只显示等待应答','接收分帧':'追加片段，while提取所有LF完整行，保留半行，上限512字符','清理连接':'清连接标志和缓存、关闭轮询、禁用控制'})

hardware(45,'沿用44课SPP固件。拖滑块仅预览，点应用才发PWM；ADC为12位原始读数，按钮INPUT_PULLUP时0表示按下。',STREAM+[['待选PWM','round滑块值，0～255']],
 ['滑块只更新待选值，应用键才发送','收到完整STATE后同时校验五列','读取和控制共用已给的接收分帧'],
 [task('阅读目标值与发送入口',['追踪PositionChanged更新待选PWM和预览文字。','追踪ApplyButton.Click调用发送命令。','滑到128但不点击应用，设备确认不应变化。'],'为什么不用每次滑动都发包？','本课用应用键确定提交时机，减少无意义的连续请求。'),
  task('补处理应答',['OK,PWM校验0到255整数，OK,LED校验0/1。','STATE恰好五列，全部字段有效才显示。','ADC最大4095，按钮0显示按下。','STATE含abc或9999时保留旧确认状态。'],'可以只更新其中看起来正常的三个字段吗？','不可以，这是一份设备状态，整条通过后再更新。'),
  task('阅读分帧并测试',['接收分帧已给；用纸条模拟OK,LE和D,1加LF。','再模拟同一片段内两条完整行。','GET与PWM交替，比较目标和设备确认。'],'一段蓝牙数据一定等于一条应答吗？','不一定，可能半条或多条，需要LF协议分帧。')],
 [question('目标128代表设备已128吗？','不代表，目标来自滑块，确认来自回包。'),question('ADC读数能直接叫电压吗？','不能，原始读数与精确电压不是一回事。'),question('按钮0为什么是按下？','使用上拉输入，按钮按下接地读0。')],
 [('滑块只做预览',['待选PWM取四舍五入值。','应用按钮才发出请求。'],'PositionChanged已经给出，用来比较目标与确认。'),('完整状态校验',['STATE五列全部有效才显示。','ADC 9999应被拒绝。'],'处理应答为本课唯一缺口；不要重复搭连接。'),('缓存提取完整行',['while处理所有LF行。','最后半行留给下次片段。'],'分帧已给，阅读并用拆段和连段做推演。')],
 procedure_overrides={'处理应答':'先验字段数与全部范围，再更新OK或STATE反馈','接收分帧':'缓存片段、按LF取完整行，保留尾部半行'})

hardware(46,'BLE工程已内置完整MIT BluetoothLE扩展。服务6e400001…，RX写6e400002…，TX通知6e400003…，完整UUID见接线协议文档。写UTF-8列表中的单字符0或1，不附LF或NUL。',
 [['已连接','假；Connected回调才真'],['DevicePicker','ElementsFromString接DeviceList'],['ScanClock','5秒后停止扫描'],['UTF-16／NUL','false／false']],
 ['开始扫描并保持设备索引一致','Connected订阅TX通知','写RX后等LED,0/1通知确认'],
 [task('补扫描并阅读订阅',['补开始扫描：先停止旧扫描与连接、清状态和列表。','StartScanning并开5秒ScanClock。','DeviceFound与停止事件已给，DeviceList进入ElementsFromString。','阅读Connected中RegisterForStrings，区分扫描和通知订阅。'],'BLE设备选择为什么用SelectionIndex连接？','本扩展Connect接受扫描列表序号，显示列表必须与该索引一致。'),
  task('补写入开关',['连接标志和IsDeviceConnected都真才写入。','WriteStringsWithResponse传服务UUID、RX UUID、false及单项文字列表。','参数只传0或1，不加LF，NullTerminateStrings为false。','等待设备通知，不把写完成当作灯已亮。'],'StringsWritten等于设备应用确认吗？','不等于，它只说明BLE写入操作完成，灯状态由TX通知协议确认。'),
  task('补通知解析',['StringsReceived入口已给，先核对服务及TX UUID。','遍历stringValues，逐项交解析通知。','消息必须是LED,0或LED,1才更新。','LED,9或未知字段不覆盖原状态。'],'为什么不是用BluetoothClient的配对列表？','BLE围绕扫描、服务和特征通信，不是经典SPP配对通道。')],
 [question('RX与TX特征分别做什么？','RX接收写入命令，TX提供设备状态通知。'),question('这里写1后附LF吗？','不附，只写UTF-8单字符1。'),question('收到通知先检查什么？','服务UUID与通知特征UUID，再校验消息内容。')],
 [('连接后订阅通知',['Connected中RegisterForStrings。','订阅TX，写入使用另一个RX。'],'截图为已给Connected；扫描过程是课堂任务一，不能把订阅当扫描。'),('写入UTF-8开关',['写入列表只含0或1。','不带换行或NUL。'],'写入开关待补；方法签名按包内真实扩展。'),('接收并校验通知',['核对UUID，遍历stringValues。','只接纳LED,0或LED,1。'],'入口已给，解析通知过程待补。')],
 extra_components=[('DevicePicker','ListPicker','按扫描序号选择设备')],
 event_overrides={'OnButton.Click':'调用写入开关(文字1)','OffButton.Click':'调用写入开关(文字0)'},
 procedure_overrides={'开始扫描':'停止旧扫描和连接、清状态，StartScanning并开启5秒计时','写入开关':'使用服务与RX UUID、utf16=false、单项文字列表写入','解析通知':'只接受LED,0/1两字段通知','清理连接':'禁用控制并设未连接'})

hardware(47,'ESP32创建YX-ESP32-AP，示例口令YXclass88，手机主动加入此局域网，TCP地址192.168.4.1:9000。ClientSocketAI2Ext没有Connected事件，以ConnectionState轮询判断；不是HTTP。',STREAM+[['连接中','连接请求后的等待状态']],
 ['校验IP与端口后Connect，先显示连接中','轮询ConnectionState决定是否开放控制','DataReceived片段交给LF分帧，再解析完整行'],
 [task('补连接设备',['非空HostBox，端口须为1到65535整数。','设置ServerAddress与文本ServerPort，再Connect。','开PollClock检查ConnectionState，不立即显示连接成功。','AP填192.168.4.1和9000。'],'Connect调用结束就代表通道建立了吗？','不代表，实际状态由ConnectionState轮询决定。'),
  task('阅读数据回调',['Socket.DataReceived已经给出。','连接有效时将data原样交接收分帧。','不在回调中假定片段就是完整应答。'],'扩展里有Socket.Connected事件可用吗？','本包没有；有DataReceived和RemoteConnectionClosed，并可读ConnectionState。'),
  task('补LF组帧',['把片段追加到接收缓存。','while存在LF：取前面一行、删除已处理部分、调用处理应答。','保留无LF尾部，缓存超过512字符清空并提示。','纸面推演OK,LE与D,1加LF，以及一次两条行。'],'为什么使用while而不是一个if？','一个片段可能包含多条完整行，需要全部提取。')],
 [question('192.168.4.1和9000分别是什么？','本固件AP的IP与TCP服务端口。'),question('加入热点一定有互联网吗？','不一定，此实验只需要手机与ESP32的局域网通信。'),question('原始TCP能直接用Web.Get吗？','不能，这份固件使用自定义TCP行协议，不是HTTP接口。')],
 [('发起TCP连接',['设置IP和端口再Connect。','等待ConnectionState为真。'],'连接设备待补，不能伪造扩展不存在的Connected事件。'),('收到的是片段',['DataReceived的data交接收分帧。','片段可能不是一整行。'],'入口已给，实际边界由LF定义。'),('提取全部完整行',['while取LF之前的行。','半行保留，缓存有上限。'],'接收分帧待补；清理连接也清半行缓存。')],
 event_overrides={'ConnectButton.Click':'调用连接设备','Socket.DataReceived':'当前ConnectionState为真时调用接收分帧(data)'},
 procedure_overrides={'连接设备':'校验地址和端口，设置Socket属性，Connect并轮询实际状态','接收分帧':'追加片段并循环提取LF行，保留尾部半行','清理连接':'清连接标志与缓存、禁用控制'})

hardware(48,'ESP32与手机加入同一个可互通路由器网络，教师在STA固件填写SSID和密码，从串口读实际IP；不固定使用192.168.4.1。沿用v1行协议与TCP9000。',STREAM+[['待选PWM','0到255的目标值']],
 ['读取设备实际IP，复用已给连接过程','应用按钮把PWM命令交发送命令','合法OK或STATE才更新设备确认'],
 [task('核对STA连接条件',['连接过程已给；从教师串口读取设备实际IP。','手机与板子使用可互通网络，检查访客隔离。','连接状态真后再使用控制；错误端口可修改重试。'],'连接同名Wi-Fi就一定互通吗？','不一定，访客网络或客户端隔离可能阻止设备相互访问。'),
  task('补发送命令',['应用入口已给，只把PWM和目标值交过程。','发送前核对当前连接。','Socket.SendData发送命令加LF，提示等待确认。','未连接时不调用SendData。'],'把路由器网关IP填成板子IP行吗？','不行，应使用串口打印的ESP32自身地址。'),
  task('补应答解析',['沿用45课五字段完整校验规则。','OK与STATE有效才更新确认，ADC与按钮单位明确。','设置128再GET，检查目标与确认。','坏字段不部分覆盖旧状态。'],'从AP改为STA后命令也必须重写吗？','不需要，地址配置变化，应用层LED/PWM/GET协议可继续复用。')],
 [question('STA地址从哪里得到？','从ESP32连接路由器后的串口输出读取实际分配地址。'),question('端口仍是什么？','本固件监听9000，APP必须一致。'),question('怎么区分连接错误和协议错误？','先查ConnectionState与IP/端口，再检查完整行及字段格式。')],
 [('读取实际IP再连接',['STA地址来自路由器分配。','9000端口与固件保持一致。'],'连接设备已给；不同于47课固定AP地址。'),('应用才发送PWM',['ApplyButton调用发送命令。','拖滑块仅改变预览。'],'发送命令为待补过程，入口已给。'),('验证设备应答',['所有STATE字段通过后再显示。','ADC原始值不是温度。'],'处理应答待补，保持与固件v1协议一致。')],
 event_overrides={'ApplyButton.Click':'调用发送命令(PWM,+待选PWM)'},
 procedure_overrides={'发送命令':'核对当前连接，SendData(命令+LF)','处理应答':'完整校验OK与STATE，成功才更新确认字段'})

hardware(49,'使用49-50可靠固件，格式seq|命令加LF，与v1固件不混用。等待1500ms只重发同一原文一次；再次超时报结果未确认，不等于设备未执行。',V2,
 ['只允许一条待确认命令，保存序号和原文','匹配序号且载荷有效才结束等待','一次重试仍超时就停止等待，提示用户核对'],
 [task('阅读发送过程并追踪序号',['发送命令已给，找到等待原文和发送时刻。','一次只留一个等待序号，其他按钮暂禁用。','用12|LED,1加LF手算请求和应答。'],'TCP可靠为什么还需要应用层确认？','字节有序传送不等于设备业务已经执行并被界面确认。'),
  task('补匹配应答',['按一个竖线拆成两段并校验正整数序号。','只处理等于等待序号的载荷。','载荷有效才清等待、关AckClock并恢复按钮。','旧序号仅记日志，不清除当前等待。'],'等待12时收到11|OK,LED,1怎么办？','记录旧应答，不影响12号等待。'),
  task('补最多一次重试',['当前连接且有等待，比较SystemTime差值。','达到1500ms且次数0才重发等待原文，次数设1。','再过1500ms仍无确认则停止等待并提示。','禁止重试时分配新序号或改变命令正文。'],'超时后能直接显示设备没执行吗？','不能，可能执行了但应答没确认，应显示结果未确认并用GET核对。')],
 [question('重发时哪些内容必须不变？','同一序号、同一正文与相同LF原文。'),question('固件收到重复请求怎样避免重复执行？','同序号同命令返回缓存应答。'),question('匹配序号但载荷非法可以结束等待吗？','不可以，载荷也须通过校验。')],
 [('保存一次请求',['保存序号、原文与发送时刻。','等待期间不发另一条命令。'],'发送命令已给，供阅读追踪与超时任务使用。'),('匹配序号与载荷',['旧序号不能清当前等待。','载荷完整合法才确认。'],'处理应答待补，内部调用已给处理载荷。'),('只重试一次',['1500ms后重发同一原文。','再次超时停止并报未确认。'],'检查超时待补，不能在每次Timer都无限发送。')],
 event_overrides={'OnButton.Click':'调用发送命令(LED,1)','OffButton.Click':'调用发送命令(LED,0)','ReadButton.Click':'调用发送命令(GET)','AckClock.Timer':'调用检查超时'},
 procedure_overrides={'发送命令':'仅空闲时分配序号，保存原文和时间后发送','处理应答':'校验序号分隔与当前等待匹配，再校验载荷，成功才结束等待','检查超时':'1500ms后同原文最多重试一次，第二次超时报未确认'})

hardware(50,'复用49课序号协议。只有有效STATE更新ADC相对百分比及最近确认时间；超过10秒标旧数据。IP仅在成功连接后保存，重开恢复地址但不自动认为已连接。',V2,
 ['有效STATE显示设备确认、相对ADC和按钮','PollClock同时核对连接与资料年龄','初始化只恢复上次IP，主动连接再GET'],
 [task('补完整状态面板',['处理载荷为本课缺口，其余可靠通信已给。','验证五字段后再更新LED、PWM、ADC和按钮。','ADC百分比round(adc/4095×100)，按钮0为按下。','只有有效STATE保存最近确认时刻。'],'ADC百分比能叫准确湿度吗？','不能，只是旋钮相对读数，没有湿度传感器和校准。'),
  task('阅读资料年龄检查',['PollClock.Timer已给，追踪SystemTime减最近确认。','超过10000ms时标记旧数据。','旧数值可以保留，但不称作正在实时更新。'],'收到一个开灯OK能代替新STATE刷新全部传感器吗？','不能，OK只确认对应命令，不含新的ADC或按钮测量。'),
  task('核对重开与交付说明',['Initialize已给，只GetValue lastHost。','确认已连接初值假，未自动恢复上次通道。','教师测试成功连接、PWM128、GET与重开；未实测项目写待测。','提交接线表、协议说明和正常/错误测试记录。'],'为什么不能把已连接真保存到TinyDB？','连接是当前运行中的实际通道，历史布尔值不能证明现在已连接。')],
 [question('资料年龄从何时开始计算？','最后一次收到并校验有效STATE的本机接收时刻。'),question('重开恢复了什么？','上次成功连接的IP，不恢复有效连接状态。'),question('10秒后旧值必须清空吗？','可以保留，但需明确标旧数据并提示重新GET。')],
 [('状态字段与含义',['完整校验后显示ADC相对百分比。','有效STATE才记最近确认时间。'],'处理载荷待补；不能把OK当成所有传感器刚更新。'),('连接与资料年龄',['轮询真实连接状态。','超过10秒标记旧状态。'],'Timer已给，用具体时间差做手工追踪。'),('启动只恢复地址',['读取lastHost，连接仍为假。','用户主动连接后GET。'],'初始化已给，IP在成功连接后保存。')],
 extra_components=[('PollClock','Clock','轮询连接状态并检查资料年龄')],
 event_overrides={'Screen1.Initialize':'读取lastHost，已连接设假，提示主动连接并GET','PollClock.Timer':'轮询ConnectionState；最近确认超过10秒则标旧数据'},
 procedure_overrides={'处理载荷':'校验五字段STATE后更新确认值、ADC相对百分比和最近确认时间'})

def emit_hardware(n):
 folder=emit(n)
 spec=json.loads((ROOT.parent/'aia'/f'lesson{n:02}/artifact-spec.json').read_text(encoding='utf8'))
 p=folder/'教师教案.md'
 with p.open('a',encoding='utf8') as f:
  f.write('\n## ESP32配套材料与课前核对\n\n使用 `firmware/'+spec['firmwareFolder']+'` 内同名草图。接线、协议与Arduino核心版本说明见 `firmware/接线与协议.md`。先断开USB电源接线，再核对3.3V、GND及330Ω限流电阻。\n\n')
  f.write('\n'.join('- '+x for x in spec['limitations'])+'\n\n')
  f.write('教师须记录：板型/核心版本、烧录结果、供电接线、Android权限、实际收发帧、设备输出及失败恢复。未进行的实物操作写“待测”，不得用APK编译结果替代。\n')
 return folder

if __name__=='__main__':
 for n in range(43,51): print(emit_hardware(n))
