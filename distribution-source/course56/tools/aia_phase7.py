"""Hardware lessons 43–50, using the distribution's exact AIX metadata/assets.

No socket/Bluetooth success is simulated by these projects. Each status update
comes from connection properties or a validated device reply.
"""
import argparse
import copy
import json
import zipfile

from aia_core import ROOT, METADATA
from aia_phase1 import base, intro
from aia_phase2 import integer
from aia_phase3 import lists
from aia_phase4 import choose, empty, negate, emit_project
from aia_phase5 import length, item, append, remove, foreach, lower, either, while_

# Designer and Blockly serialize the descriptor's short name. Its fully
# qualified Java type belongs in components.json and the extension jars.
BLE='BluetoothLE'
TCP='ClientSocketAI2Ext'
SERVICE='6e400001-b5a3-f393-e0a9-e50e24dcca9e'
WRITE='6e400002-b5a3-f393-e0a9-e50e24dcca9e'
NOTIFY='6e400003-b5a3-f393-e0a9-e50e24dcca9e'


def add_extension(p, name):
    archive=ROOT/'work/native/server/war/WEB-INF/classes/bundled-extensions'/f'{name}.aix'
    with zipfile.ZipFile(archive) as z:
        metadata=json.loads(z.read(next(n for n in z.namelist() if n.endswith('/components.json'))))
        for c in metadata:
            METADATA[c['type']]=c
            METADATA[c['name']]=c
        # Keep the entire original package, including jars/build information,
        # in the AIA external_comps layout expected by the native importer.
        for n in z.namelist():
            if not n.endswith('/'):p.assets['external_comps/'+n]=z.read(n)


def size(p,v):return p.b('text_length',values={'VALUE':v})
def split(p,text,at):return p.b('text_split',{'OP':'SPLIT'},{'TEXT':text,'AT':at},mutation={'mode':'SPLIT'})
def at(p,text,part):return p.b('text_starts_at',values={'TEXT':text,'PIECE':part})
def segment(p,text,start,count):return p.b('text_segment',values={'TEXT':text,'START':start,'LENGTH':count})
def round_(p,text):return p.b('math_round',{'OP':'ROUND'},{'NUM':text})


def all_(p,*terms):
    if len(terms)==1:return terms[0]
    return p.both(terms[0],all_(p,*terms[1:]))


def range_(p,value,lo,hi):return p.call('整数范围',value,p.num(lo),p.num(hi),names=('值','下限','上限'),returns=True)


def common_globals(p):
    p.tops += [p.global_('接收字段',lists(p)),p.global_('有效应答',p.boolean(False)),p.global_('日志',lists(p))]
    valid=choose(p,p.isnum(p.param('值')),all_(p,integer(p,p.param('值')),p.cmp('GTE',p.param('值'),p.param('下限')),p.cmp('LTE',p.param('值'),p.param('上限'))),p.boolean(False))
    log=p.chain(append(p,p.var('日志'),p.param('内容')),while_(p,p.cmp('GT',length(p,p.var('日志')),p.num(20)),remove(p,p.var('日志'),p.num(1))),p.set('LogLabel','Text',p.b('text_join',values={'ADD0':p.text('最近记录（最多20条）\n'),'ADD1':p.b('lists_to_csv_row',values={'LIST':p.var('日志')})},mutation={'items':2})))
    p.tops += [p.define('整数范围',valid,args=('值','下限','上限'),returns=True),p.define('记录日志',log,args=('内容',))]


def response_parser(p,number):
    """Guard list length and each integer before any state mutation."""
    field=lambda n:item(p,p.var('接收字段'),p.num(n))
    valid=lambda:p.setvar('有效应答',p.boolean(True))
    mark=lambda *a:p.chain(valid(),*a)
    led=mark(p.set('StateLabel','Text',p.join(p.text('设备确认：LED='),field(3))))
    pwm=mark(p.set('StateLabel','Text',p.join(p.text('设备确认：PWM='),field(3))))
    ok=p.iff(p.eq(length(p,p.var('接收字段')),p.num(3)),p.iff(p.eq(field(1),p.text('OK')),p.iff(p.eq(field(2),p.text('LED')),p.iff(range_(p,field(3),0,1),led),p.iff(p.eq(field(2),p.text('PWM')),p.iff(range_(p,field(3),0,255),pwm)))))
    state=mark(p.set('StateLabel','Text',p.join(p.text('设备报告：LED='),field(2),p.text('；PWM='),field(3),p.text('\nADC原始值='),field(4),p.text('；按钮='),choose(p,p.eq(field(5),p.text('0')),p.text('按下'),p.text('松开')))))
    if number==50:
        state=p.chain(state,p.set('SensorLabel','Text',p.join(p.text('电位器相对读数：'),round_(p,p.mul(p.div(field(4),p.num(4095)),p.num(100))),p.text('%（不是温湿度）'))),p.setvar('最近确认',p.method('TimeClock','SystemTime')),p.set('FreshLabel','Text',p.text('刚收到设备状态（10秒后标记为旧数据）')))
    statecheck=all_(p,range_(p,field(2),0,1),range_(p,field(3),0,255),range_(p,field(4),0,4095),range_(p,field(5),0,1))
    stateif=p.iff(p.eq(length(p,p.var('接收字段')),p.num(5)),p.iff(p.eq(field(1),p.text('STATE')),p.iff(statecheck,state)))
    err=p.iff(p.cmp('GTE',length(p,p.var('接收字段')),p.num(2)),p.iff(p.eq(field(1),p.text('ERR')),mark(p.set('StateLabel','Text',p.join(p.text('设备拒绝：'),p.param('一行'))))))
    pong=p.iff(p.eq(p.param('一行'),p.text('PONG')),valid())
    return p.chain(p.setvar('有效应答',p.boolean(False)),p.setvar('接收字段',split(p,p.trim(p.param('一行')),p.text(','))),ok,stateif,err,pong,p.iff(negate(p,p.var('有效应答')),p.call('记录日志',p.join(p.text('忽略格式错误：'),p.param('一行')),names=('内容',))))


def finish_class(p,names):
    p.class_tops=[]
    for top in p.tops:
        fields={f.get('name'):f.text for f in top.findall('field')}
        if top.get('type')=='procedures_defnoreturn' and fields.get('NAME') in names:
            m=top.find('mutation');args=[a.get('name') for a in m.findall('arg')] if m is not None else []
            p.class_tops.append(p.note(p.define(fields['NAME'],p.set('StatusLabel','Text',p.text('课堂任务：补齐'+fields['NAME'])),args=args),'参数与调用保留，请依据协议完成本课过程。'))
        else:p.class_tops.append(copy.deepcopy(top))


def detail(number,p,captures,tasks,tests):
    modes={43:'串口指令实验台',44:'经典蓝牙SPP开关灯',45:'SPP调光与状态回传',46:'MIT BluetoothLE低功耗蓝牙',47:'ESP32 AP局域网TCP',48:'同路由器STA TCP',49:'带序号确认与一次重试',50:'软硬件综合状态面板'}
    limitations=['未进行Android手机、ESP32或真实无线链路测试；AIA导入/编译和协议夹具不能替代真机联调','默认接线参考经典ESP32-WROOM DevKit；C3/S3仅用于BLE或Wi-Fi并需重新核对GPIO，不能运行经典SPP固件','GPIO仅3.3V；LED串330Ω电阻，GPIO34为ADC1输入，GPIO27按钮使用INPUT_PULLUP']
    if number==43:limitations.append('本课APP仅生成/粘贴解析指令；通过电脑串口调试器连接ESP32，不宣称手机已建立USB串口连接')
    if number>=47:limitations.append('ClientSocketAI2Ext无Connected/Error事件；通过ConnectionState轮询、RemoteConnectionClosed及Screen.ErrorOccurred判断连接')
    return dict(work=modes[number],classroomKept=['所有组件与协议参数','连接状态清理、数值边界、非本课重点过程和完整事件入口','扩展完整原始包与真实事件签名'],classroomTasks=['补齐'+x+'过程' for x in tasks],screenshotGroups=captures,tests=tests,implementationNotes=['固件与接线见firmware目录和esp32-course-firmware-spec.md','发送请求不立即假定设备状态成功，合法应答才更新确认状态','接收使用LF分帧，缓存上限512字符；日志最多20条'] if number!=46 else ['BLE使用UART UUID，WriteStringsWithResponse写单字节ASCII 0/1','RegisterForStrings使用UTF-8，NullTerminateStrings=False；按stringValues列表逐条解析','BLE不能与经典蓝牙SPP互换'],limitations=limitations,hardwareTest='not performed',firmwareFolder={43:'43-serial-protocol',44:'44-45-classic-spp',45:'44-45-classic-spp',46:'46-ble-led',47:'47-tcp-ap',48:'48-tcp-sta',49:'49-50-tcp-reliable',50:'49-50-tcp-reliable'}[number])


def build43():
    p=base(43,'YXCourse43','认识设备与通信指令')
    p.screen([p.page(intro(p,'指令实验台','第43课｜APP生成指令，电脑串口调试器连接ESP32')+[
        p.button('OnButton','生成 LED 开灯指令'),p.button('OffButton','生成 LED 关灯指令'),p.label('CommandLabel','尚未生成指令。',FontSize=21,Height=90),
        p.comp('ReplyBox','TextBox',Text='',Hint='粘贴串口真实应答，例如 OK,LED,1',Width=-2,Height=90,MultiLine='True',FontSize=18),p.button('ParseButton','解析这一行应答'),p.label('StateLabel','尚无设备确认。',FontSize=21,Height=130),p.label('StatusLabel','电脑串口设115200；发送时选择换行LF。APP没有连接USB。',Height=100),p.label('LogLabel','最近记录',FontSize=13,Height=170)])])
    p.tops=[p.global_('最近命令',p.text(''))];common_globals(p)
    p.tops += [p.define('生成指令',p.chain(p.setvar('最近命令',p.join(p.text('LED,'),p.param('值'),p.text('\n'))),p.set('CommandLabel','Text',p.join(p.text('命令：LED,'),p.param('值'),p.text(' ⏎ LF\n共6个ASCII字符；最后一个为换行。')))),args=('值',)),p.define('处理应答',response_parser(p,43),args=('一行',)),p.event('OnButton','Click',p.call('生成指令',p.num(1),names=('值',))),p.event('OffButton','Click',p.call('生成指令',p.num(0),names=('值',))),p.event('ParseButton','Click',p.call('处理应答',p.trim(p.get('ReplyBox','Text')),names=('一行',)))]
    tasks=['生成指令','处理应答'];finish_class(p,tasks)
    tests=[dict(event='OnButton.Click',expect={'global 最近命令':'LED,1\n'}),dict(procedure='处理应答',args=['OK,LED,1'],expect={'StateLabel.Text':'设备确认：LED=1','global 有效应答':True}),dict(procedure='处理应答',args=['OK,LED,9'],expect={'global 有效应答':False}),dict(procedure='处理应答',args=['STATE,1,128,2048,0'],expect={'global 有效应答':True},contains={'StateLabel.Text':['ADC原始值=2048','按钮=按下']})]
    return p,detail(43,p,['生成指令','处理应答','ParseButton.Click'],tasks,tests)


def build_stream(number):
    spp=number in (44,45);reliable=number>=49;sensors=number in (45,48,50)
    p=base(number,f'YXCourse{number}',{44:'蓝牙连接与开关控制',45:'蓝牙双向数据通信',47:'Wi-Fi TCP直连设备',48:'通过局域网控制设备',49:'可靠通信与异常处理',50:'软硬件综合项目'}[number])
    if not spp:add_extension(p,'ClientSocketAI2Ext')
    controls=[]
    if spp:
        controls += [p.comp('DevicePicker','ListPicker',Text='选择已配对ESP32',Title='先在系统蓝牙设置配对YX-ESP32-SPP',Width=-2,Height=52,FontSize=18,BackgroundColor='&HFF1388CC',TextColor='&HFFFFFFFF')]
    else:
        controls += [p.comp('HostBox','TextBox',Text='192.168.4.1' if number==47 else '',Hint='ESP32串口输出的IPv4地址',Width=-2,Height=52,FontSize=19),p.comp('PortBox','TextBox',Text='9000',NumbersOnly='True',Hint='端口1～65535',Width=-2,Height=52,FontSize=19),p.button('ConnectButton','连接ESP32 TCP服务器')]
    controls += [p.button('DisconnectButton','断开连接',BackgroundColor='&HFFDCEFFF',TextColor='&HFF123E62'),p.comp('LedRow','HorizontalArrangement',[p.button('OnButton','开灯',Width=-1050,Enabled='False'),p.button('OffButton','关灯',Width=-1050,Enabled='False')],Width=-2,Height=58)]
    if sensors:
        controls += [p.label('PreviewLabel','待发送PWM：0（0～255）',FontSize=18,Height=45),p.comp('BrightnessSlider','Slider',Width=-2,MinValue=0,MaxValue=255,ThumbPosition=0,NumberOfSteps=255,ThumbEnabled='True'),p.button('ApplyButton','发送待选PWM',Enabled='False')]
    if number!=44:controls.append(p.button('ReadButton','读取设备状态 GET',Enabled='False'))
    if number==50:controls += [p.label('SensorLabel','电位器相对读数：—',FontSize=20,Height=65),p.label('FreshLabel','尚无确认状态；连接状态不会自动从本地恢复。',FontSize=16,Height=70)]
    instructions='经典ESP32-WROOM支持SPP；C3/S3不支持。先系统配对，再选择设备。' if spp else ('先连接YX-ESP32-AP，密码YXclass88，保留“无互联网”连接。' if number==47 else '手机和ESP32接同一Wi-Fi；填写串口输出的局域网IP，手机localhost不是ESP32。')
    controls += [p.label('StatusLabel','尚未连接。'+instructions,FontSize=17,Height=125),p.label('StateLabel','尚无设备确认。',FontSize=20,Height=135),p.label('LogLabel','最近记录',FontSize=13,Height=220)]
    nonvisual=[p.comp('TimeClock','Clock',TimerEnabled='False',TimerAlwaysFires='False'),p.comp('PollClock','Clock',TimerInterval=100,TimerEnabled='False',TimerAlwaysFires='False')]
    if spp:nonvisual.append(p.comp('Bt','BluetoothClient',CharacterEncoding='UTF-8',DelimiterByte=10,DisconnectOnError='True',NoLocationNeeded='False'))
    else:nonvisual.append(p.comp('Socket',TCP,ServerAddress='192.168.4.1' if number==47 else '',ServerPort='9000',TimeoutMs=2500,HexaStringMode='False',DebugMessages='False'))
    if reliable:nonvisual.append(p.comp('AckClock','Clock',TimerInterval=100,TimerEnabled='False',TimerAlwaysFires='False'))
    if number==50:nonvisual.append(p.comp('LocalDB','TinyDB',Namespace='YXHardwarePanel'))
    p.screen([p.page(intro(p,'ESP32通信实验室',f'第{number}课｜'+('有序号、确认与超时' if reliable else '请求与应答分开显示'))+controls)]+nonvisual,AndroidMinSdk=21)
    p.tops=[p.global_('已连接',p.boolean(False)),p.global_('连接中',p.boolean(False)),p.global_('连接开始',p.num(0)),p.global_('接收缓存',p.text('')),p.global_('当前行',p.text('')),p.global_('换行位置',p.num(0)),p.global_('最近命令',p.text('')),p.global_('待选PWM',p.num(0))]
    if number==50:p.tops.append(p.global_('最近确认',p.num(0)))
    common_globals(p)
    buttons=['OnButton','OffButton']+(['ApplyButton'] if sensors else [])+(['ReadButton'] if number!=44 else [])
    enabled=lambda value:p.chain(*[p.set(n,'Enabled',value()) for n in buttons])
    isconn=lambda:p.get('Bt','IsConnected') if spp else p.get('Socket','ConnectionState')
    send=lambda text:p.method('Bt','SendText',text) if spp else p.method('Socket','SendData',text)
    disconnect=lambda:p.method('Bt','Disconnect') if spp else p.method('Socket','Disconnect')
    cleanup=p.chain(p.setvar('已连接',p.boolean(False)),p.setvar('连接中',p.boolean(False)),p.setvar('接收缓存',p.text('')),p.set('PollClock','TimerEnabled',p.boolean(False)),enabled(lambda:p.boolean(False)),p.set('StatusLabel','Text',p.text('已断开；设备输出可能仍保留上次状态，须重连后读取。')))
    if reliable:cleanup=p.chain(cleanup,p.setvar('等待序号',p.num(0)),p.setvar('等待原文',p.text('')),p.set('AckClock','TimerEnabled',p.boolean(False)))
    connected=p.chain(p.setvar('已连接',p.boolean(True)),p.setvar('连接中',p.boolean(False)),p.setvar('接收缓存',p.text('')),enabled(lambda:p.boolean(True)),p.set('StatusLabel','Text',p.text('连接已建立；按钮发送请求，设备应答后才确认状态。')))
    if number==50:connected=p.chain(connected,p.method('LocalDB','StoreValue',p.text('lastHost'),p.trim(p.get('HostBox','Text'))),p.set('FreshLabel','Text',p.text('已连接但尚未读取新状态；点击GET。')))
    p.tops += [p.define('清理连接',cleanup),p.define('处理载荷' if reliable else '处理应答',response_parser(p,number),args=('一行',))]
    if reliable:
        p.tops += [p.global_('下个序号',p.num(1)),p.global_('等待序号',p.num(0)),p.global_('等待原文',p.text('')),p.global_('发送时刻',p.num(0)),p.global_('重试次数',p.num(0)),p.global_('序号字段',lists(p))]
        # Only a valid matching reply completes the one outstanding request.
        parts=lambda n:item(p,p.var('序号字段'),p.num(n))
        matching=p.chain(p.call('处理载荷',parts(2),names=('一行',)),p.iff(p.var('有效应答'),p.chain(p.setvar('等待序号',p.num(0)),p.setvar('等待原文',p.text('')),p.set('AckClock','TimerEnabled',p.boolean(False)),enabled(lambda:p.boolean(True)),p.set('StatusLabel','Text',p.text('已收到匹配序号的设备回复。')))))
        seqparse=p.chain(p.setvar('序号字段',split(p,p.param('一行'),p.text('|'))),p.iff(p.eq(length(p,p.var('序号字段')),p.num(2)),p.iff(range_(p,parts(1),1,2147483647),p.iff(all_(p,p.cmp('GT',p.var('等待序号'),p.num(0)),p.eq(p.add(parts(1),p.num(0)),p.var('等待序号'))),matching,p.call('记录日志',p.join(p.text('忽略旧序号：'),p.param('一行')),names=('内容',)))),p.call('记录日志',p.text('忽略非法序号帧'),names=('内容',))))
        p.tops.append(p.define('处理应答',seqparse,args=('一行',)))
        raw=p.chain(p.setvar('等待序号',p.var('下个序号')),p.setvar('下个序号',choose(p,p.cmp('GTE',p.var('下个序号'),p.num(2147483647)),p.num(1),p.add(p.var('下个序号'),p.num(1)))),p.setvar('等待原文',p.join(p.var('等待序号'),p.text('|'),p.param('命令'),p.text('\n'))),p.setvar('发送时刻',p.method('TimeClock','SystemTime')),p.setvar('重试次数',p.num(0)),enabled(lambda:p.boolean(False)),send(p.var('等待原文')),p.set('AckClock','TimerEnabled',p.boolean(True)),p.set('StatusLabel','Text',p.join(p.text('已发送，等待确认。序号：'),p.var('等待序号'))))
        retry=p.iff(p.get('Socket','ConnectionState'),p.iff(p.cmp('GT',p.var('等待序号'),p.num(0)),p.iff(p.cmp('GTE',p.sub(p.method('TimeClock','SystemTime'),p.var('发送时刻')),p.num(1500)),p.iff(p.eq(p.var('重试次数'),p.num(0)),p.chain(send(p.var('等待原文')),p.setvar('重试次数',p.num(1)),p.setvar('发送时刻',p.method('TimeClock','SystemTime')),p.call('记录日志',p.text('同序号同指令重试一次'),names=('内容',))),p.chain(p.setvar('等待序号',p.num(0)),p.set('AckClock','TimerEnabled',p.boolean(False)),enabled(lambda:p.boolean(True)),p.set('StatusLabel','Text',p.text('结果未确认：一次重试后仍超时。请读取GET核对真实状态。')))))),p.call('清理连接'))
        p.tops += [p.define('检查超时',retry),p.event('AckClock','Timer',p.call('检查超时'))]
        sending=p.iff(p.both(p.var('已连接'),isconn()),p.iff(p.eq(p.var('等待序号'),p.num(0)),raw,p.set('StatusLabel','Text',p.text('上一条指令尚未确认，请等待。'))),p.set('StatusLabel','Text',p.text('未连接，未发送。')))
    else:
        sending=p.iff(p.both(p.var('已连接'),isconn()),p.chain(p.setvar('最近命令',p.join(p.param('命令'),p.text('\n'))),send(p.var('最近命令')),p.set('StatusLabel','Text',p.join(p.text('请求已发送，等待设备应答：'),p.param('命令')))),p.set('StatusLabel','Text',p.text('未连接，未发送。')))
    # Network chunks can contain zero, one, or many LF-delimited frames.
    take=p.chain(p.setvar('换行位置',at(p,p.var('接收缓存'),p.text('\n'))),p.setvar('当前行',p.trim(segment(p,p.var('接收缓存'),p.num(1),p.sub(p.var('换行位置'),p.num(1))))),p.setvar('接收缓存',segment(p,p.var('接收缓存'),p.add(p.var('换行位置'),p.num(1)),p.sub(size(p,p.var('接收缓存')),p.var('换行位置')))),p.iff(negate(p,empty(p,p.var('当前行'))),p.chain(p.call('记录日志',p.join(p.text('RX '),p.var('当前行')),names=('内容',)),p.call('处理应答',p.var('当前行'),names=('一行',)))))
    ingest=p.chain(p.setvar('接收缓存',p.join(p.var('接收缓存'),p.param('片段'))),p.iff(p.cmp('GT',size(p,p.var('接收缓存')),p.num(512)),p.chain(p.setvar('接收缓存',p.text('')),p.call('记录日志',p.text('接收缓存超512字符，已清空，请重新读取状态。'),names=('内容',))),while_(p,p.cmp('GT',at(p,p.var('接收缓存'),p.text('\n')),p.num(0)),take)))
    p.tops += [p.define('发送命令',sending,args=('命令',)),p.define('接收分帧',ingest,args=('片段',)),p.event('OnButton','Click',p.call('发送命令',p.text('LED,1'),names=('命令',))),p.event('OffButton','Click',p.call('发送命令',p.text('LED,0'),names=('命令',))),p.event('DisconnectButton','Click',p.chain(disconnect(),p.call('清理连接')))]
    if sensors:
        p.tops += [p.event('BrightnessSlider','PositionChanged',p.chain(p.setvar('待选PWM',round_(p,p.get('BrightnessSlider','ThumbPosition'))),p.set('PreviewLabel','Text',p.join(p.text('待发送PWM：'),p.var('待选PWM'),p.text('（设备确认值见下方）'))))),p.event('ApplyButton','Click',p.call('发送命令',p.join(p.text('PWM,'),p.var('待选PWM')),names=('命令',)))]
    if number!=44:p.tops.append(p.event('ReadButton','Click',p.call('发送命令',p.text('GET'),names=('命令',))))
    if spp:
        polling=p.iff(p.var('已连接'),p.iff(isconn(),p.iff(p.cmp('GT',p.method('Bt','BytesAvailableToReceive'),p.num(0)),p.call('接收分帧',p.method('Bt','ReceiveText',p.method('Bt','BytesAvailableToReceive')),names=('片段',))),p.call('清理连接')))
        connect=p.chain(p.call('清理连接'),p.iff(p.method('Bt','Connect',p.get('DevicePicker','Selection')),p.chain(connected,p.set('PollClock','TimerEnabled',p.boolean(True))),p.set('StatusLabel','Text',p.text('SPP连接失败：检查系统配对和固件，C3/S3不支持经典SPP。'))))
        p.tops += [p.define('连接设备',connect),p.event('DevicePicker','BeforePicking',p.iff(p.get('Bt','Available'),p.set('DevicePicker','Elements',p.get('Bt','AddressesAndNames')),p.set('StatusLabel','Text',p.text('此设备没有可用蓝牙适配器。')))),p.event('DevicePicker','AfterPicking',p.call('连接设备')),p.event('PollClock','Timer',polling)]
    else:
        port=p.trim(p.get('PortBox','Text'));host=lambda:p.trim(p.get('HostBox','Text'))
        connect=p.chain(disconnect(),p.call('清理连接'),p.iff(empty(p,host()),p.set('StatusLabel','Text',p.text('请填写ESP32的IPv4地址。')),p.iff(range_(p,port,1,65535),p.chain(p.set('Socket','ServerAddress',host()),p.set('Socket','ServerPort',p.trim(p.get('PortBox','Text'))),p.setvar('连接中',p.boolean(True)),p.setvar('连接开始',p.method('TimeClock','SystemTime')),p.set('StatusLabel','Text',p.text('正在连接；ConnectionState为真后才启用控制。')),p.set('PollClock','TimerEnabled',p.boolean(True)),p.method('Socket','Connect')),p.set('StatusLabel','Text',p.text('端口必须为1～65535的整数。')))))
        notconn=p.iff(p.var('已连接'),p.call('清理连接'),p.iff(p.both(p.var('连接中'),p.cmp('GTE',p.sub(p.method('TimeClock','SystemTime'),p.var('连接开始')),p.num(4000))),p.chain(disconnect(),p.call('清理连接'),p.set('StatusLabel','Text',p.text('连接超时，请核对IP、Wi-Fi和端口。')))))
        polling=p.iff(isconn(),p.iff(negate(p,p.var('已连接')),connected),notconn)
        if number==50:polling=p.chain(polling,p.iff(p.both(p.cmp('GT',p.var('最近确认'),p.num(0)),p.cmp('GT',p.sub(p.method('TimeClock','SystemTime'),p.var('最近确认')),p.num(10000))),p.set('FreshLabel','Text',p.text('旧数据：超过10秒未确认新状态，请读取GET。'))))
        p.tops += [p.define('连接设备',connect),p.event('ConnectButton','Click',p.call('连接设备')),p.event('PollClock','Timer',polling),p.event('Socket','DataReceived',p.iff(isconn(),p.call('接收分帧',p.param('data',True),names=('片段',)))),p.event('Socket','RemoteConnectionClosed',p.call('清理连接'))]
    p.tops += [p.event('Screen1','PermissionDenied',p.chain(disconnect(),p.call('清理连接'),p.set('StatusLabel','Text',p.join(p.text('权限被拒绝：'),p.param('permissionName',True),p.text('。请在系统设置允许附近设备/蓝牙权限。'))))),p.event('Screen1','ErrorOccurred',p.chain(p.call('记录日志',p.join(p.text('组件错误：'),p.param('message',True)),names=('内容',)),p.call('清理连接')))]
    if number==50:p.tops.append(p.event('Screen1','Initialize',p.chain(p.set('HostBox','Text',p.method('LocalDB','GetValue',p.text('lastHost'),p.text(''))),p.setvar('已连接',p.boolean(False)),p.set('StatusLabel','Text',p.text('仅恢复上次IP；请主动连接并GET读取状态。')))))
    tasks={44:['连接设备','发送命令'],45:['处理应答'],47:['连接设备','接收分帧'],48:['处理应答','发送命令'],49:['处理应答','检查超时'],50:['处理载荷']}[number];finish_class(p,tasks)
    captures={44:['DevicePicker.BeforePicking','连接设备','发送命令'],45:['BrightnessSlider.PositionChanged','处理应答','接收分帧'],47:['连接设备','Socket.DataReceived','接收分帧'],48:['连接设备','ApplyButton.Click','处理应答'],49:['发送命令','处理应答','检查超时'],50:['处理载荷','PollClock.Timer','Screen1.Initialize']}[number]
    parser='处理载荷' if reliable else '处理应答'
    tests=[dict(procedure=parser,args=['OK,LED,1'],expect={'StateLabel.Text':'设备确认：LED=1','global 有效应答':True}),dict(procedure=parser,args=['STATE,1,128,2048,0'],expect={'global 有效应答':True},contains={'StateLabel.Text':['PWM=128','ADC原始值=2048','按钮=按下']}),dict(procedure=parser,args=['STATE,1,128,9999,0'],expect={'global 有效应答':False}),dict(procedure='清理连接',expect={'global 已连接':False,'global 接收缓存':'','OnButton.Enabled':False})]
    return p,detail(number,p,captures,tasks,tests)


def build46():
    p=base(46,'YXCourse46','认识低功耗蓝牙BLE');add_extension(p,'BluetoothLE')
    p.screen([p.page(intro(p,'BLE服务与特征值','第46课｜低功耗蓝牙，不使用经典SPP')+[
        p.button('ScanButton','扫描BLE设备（5秒）'),p.comp('DevicePicker','ListPicker',Text='选择YX-ESP32-BLE',Title='按扫描列表序号连接',Width=-2,Height=52,FontSize=18,BackgroundColor='&HFF1388CC',TextColor='&HFFFFFFFF'),p.button('DisconnectButton','断开连接',BackgroundColor='&HFFDCEFFF',TextColor='&HFF123E62'),p.button('OnButton','写入 ASCII 1 开灯',Enabled='False'),p.button('OffButton','写入 ASCII 0 关灯',Enabled='False'),p.label('StatusLabel','尚未连接。先扫描，再选择设备；需允许附近设备/蓝牙权限。',FontSize=18,Height=130),p.label('StateLabel','尚无BLE通知确认。',FontSize=21,Height=110),p.label('ProtocolLabel','服务6e400001…\n写入特征6e400002…；通知特征6e400003…\n写入UTF-8单字节0/1，不附带换行或NUL。',FontSize=14,Height=135),p.label('LogLabel','最近记录',FontSize=13,Height=180)]),p.comp('Ble',BLE,AutoReconnect='False',ConnectionTimeout=10,NoLocationNeeded='False',NullTerminateStrings='False'),p.comp('ScanClock','Clock',TimerInterval=5000,TimerEnabled='False',TimerAlwaysFires='False')],AndroidMinSdk=21)
    p.tops=[p.global_('已连接',p.boolean(False)),p.global_('通知字段',lists(p))];common_globals(p)
    cleanup=p.chain(p.setvar('已连接',p.boolean(False)),p.set('OnButton','Enabled',p.boolean(False)),p.set('OffButton','Enabled',p.boolean(False)),p.set('StatusLabel','Text',p.text('未连接；经典SPP设备不会提供本课BLE服务。')))
    scan=p.chain(p.method('Ble','StopScanning'),p.method('Ble','Disconnect'),p.call('清理连接'),p.set('DevicePicker','Elements',lists(p)),p.method('Ble','StartScanning'),p.set('ScanClock','TimerEnabled',p.boolean(True)),p.set('StatusLabel','Text',p.text('扫描中…等待YX-ESP32-BLE，5秒后停止。')))
    stop=p.chain(p.method('Ble','StopScanning'),p.set('ScanClock','TimerEnabled',p.boolean(False)),p.set('DevicePicker','ElementsFromString',p.get('Ble','DeviceList')),p.set('StatusLabel','Text',p.text('扫描停止。点击设备选择器，选YX-ESP32-BLE。')))
    send=p.iff(p.both(p.var('已连接'),p.get('Ble','IsDeviceConnected')),p.chain(p.method('Ble','WriteStringsWithResponse',p.text(SERVICE),p.text(WRITE),p.boolean(False),lists(p,p.param('值'))),p.set('StatusLabel','Text',p.text('写入请求已发出，等待LED通知确认。'))),p.set('StatusLabel','Text',p.text('未连接，未写入。')))
    f=lambda n:item(p,p.var('通知字段'),p.num(n))
    parse=p.chain(p.setvar('通知字段',split(p,p.param('消息'),p.text(','))),p.iff(p.eq(length(p,p.var('通知字段')),p.num(2)),p.iff(p.both(p.eq(f(1),p.text('LED')),range_(p,f(2),0,1)),p.set('StateLabel','Text',p.join(p.text('BLE设备确认：LED='),f(2))))))
    receive=p.iff(all_(p,p.eq(lower(p,p.param('serviceUuid',True)),p.text(SERVICE)),p.eq(lower(p,p.param('characteristicUuid',True)),p.text(NOTIFY))),foreach(p,'通知',p.param('stringValues',True),p.chain(p.call('记录日志',p.param('通知'),names=('内容',)),p.call('解析通知',p.param('通知'),names=('消息',)))))
    p.tops += [p.define('清理连接',cleanup),p.define('开始扫描',scan),p.define('停止扫描',stop),p.define('写入开关',send,args=('值',)),p.define('解析通知',parse,args=('消息',)),p.event('ScanButton','Click',p.call('开始扫描')),p.event('ScanClock','Timer',p.call('停止扫描')),p.event('DevicePicker','BeforePicking',p.chain(p.method('Ble','StopScanning'),p.set('ScanClock','TimerEnabled',p.boolean(False)),p.set('DevicePicker','ElementsFromString',p.get('Ble','DeviceList')))),p.event('Ble','DeviceFound',p.set('DevicePicker','ElementsFromString',p.get('Ble','DeviceList'))),p.event('DevicePicker','AfterPicking',p.iff(p.cmp('GT',p.get('DevicePicker','SelectionIndex'),p.num(0)),p.chain(p.method('Ble','Connect',p.get('DevicePicker','SelectionIndex')),p.set('StatusLabel','Text',p.text('BLE连接中；等待Connected回调。'))))),p.event('Ble','Connected',p.chain(p.setvar('已连接',p.boolean(True)),p.method('Ble','RegisterForStrings',p.text(SERVICE),p.text(NOTIFY),p.boolean(False)),p.set('OnButton','Enabled',p.boolean(True)),p.set('OffButton','Enabled',p.boolean(True)),p.set('StatusLabel','Text',p.text('BLE已连接并请求订阅通知，请点击开关验证。')))),p.event('Ble','StringsReceived',receive),p.event('Ble','ConnectionFailed',p.chain(p.call('清理连接'),p.set('StatusLabel','Text',p.join(p.text('BLE连接失败：'),p.param('reason',True))))),p.event('Ble','Disconnected',p.call('清理连接')),p.event('DisconnectButton','Click',p.chain(p.method('Ble','Disconnect'),p.call('清理连接'))),p.event('OnButton','Click',p.call('写入开关',p.text('1'),names=('值',))),p.event('OffButton','Click',p.call('写入开关',p.text('0'),names=('值',))),p.event('Screen1','PermissionDenied',p.chain(p.call('清理连接'),p.set('ScanClock','TimerEnabled',p.boolean(False)),p.set('StatusLabel','Text',p.text('BLE权限被拒绝，请在Android系统设置允许附近设备/蓝牙权限；旧版系统还需位置权限。')))),p.event('Screen1','ErrorOccurred',p.chain(p.call('清理连接'),p.set('StatusLabel','Text',p.join(p.text('BLE组件报告：'),p.param('message',True)))))]
    tasks=['开始扫描','写入开关','解析通知'];finish_class(p,tasks)
    tests=[dict(procedure='解析通知',args=['LED,1'],expect={'StateLabel.Text':'BLE设备确认：LED=1'}),dict(procedure='解析通知',args=['LED,0'],expect={'StateLabel.Text':'BLE设备确认：LED=0'}),dict(set={'StateLabel.Text':'原状态'},procedure='解析通知',args=['LED,9'],expect={'StateLabel.Text':'原状态'}),dict(procedure='清理连接',expect={'global 已连接':False,'OnButton.Enabled':False})]
    return p,detail(46,p,['Ble.Connected','写入开关','Ble.StringsReceived'],tasks,tests)


def emit(number):
    p,d=build43() if number==43 else build46() if number==46 else build_stream(number)
    # emit_project supports ordinary assets; pre-create nested extension folders.
    assetroot=ROOT/f'work/course56/aia/lesson{number:02d}/assets'
    for name in p.assets:(assetroot/name).parent.mkdir(parents=True,exist_ok=True)
    emit_project(number,p,d)


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('lessons',nargs='*',type=int,default=list(range(43,51)));args=ap.parse_args()
    for n in args.lessons:
        if not 43<=n<=50:ap.error('43–50 only')
        emit(n)
