"""Media and phone sensors, lessons 23–28; physical-device checks remain pending."""
from pathlib import Path
import argparse
import copy
import json
import struct
import zlib

from aia_core import ROOT
from aia_phase1 import base, intro
from aia_phase2 import numeric_text
from aia_phase3 import ref

OUT=ROOT/'work/course56/aia'
BLUEPRINTS=ROOT/'work/course56/blueprints'


def empty(p,value):return p.b('text_isEmpty',values={'VALUE':value})
def negate(p,value):return p.b('logic_negate',values={'BOOL':value})
def choose(p,test,yes,no):return p.b('controls_choose',values={'TEST':test,'THENRETURN':yes,'ELSERETURN':no})


def build23():
    p=base(23,'YXCourse23','会说话的 APP')
    p.screen([p.page(intro(p,'语音提示小助手','第 23 课｜文字、语速与异步回调')+[
        p.comp('MessageBox','TextBox',Text='你好，欢迎来到羽轩编程课堂。',Hint='输入要朗读的文字',MultiLine='True',Width=-2,Height=150,FontSize=20,BackgroundColor='&HFFFFFFFF'),
        p.label('RateLabel','语速：1.0 倍',FontSize=19,Height=42),p.comp('RateSlider','Slider',MinValue=.5,MaxValue=1.5,ThumbPosition=1,NumberOfSteps=10,Width=-2,ColorLeft='&HFF1388CC'),
        p.comp('VoiceButtons','HorizontalArrangement',[p.button('SpeakButton','朗读',Width=-1050),p.button('StopButton','停止',Width=-1050,BackgroundColor='&HFFDCEFFF',TextColor='&HFF123E62')],Width=-2,Height=58),
        p.label('StatusLabel','待播报',FontSize=22,Height=125,BackgroundColor='&HFFFFFFFF'),
        p.label('HintLabel','需要手机安装中文语音。是否能离线发声取决于系统语音包。',FontSize=14,TextColor='&HFF56758B')]),
        p.comp('Voice','TextToSpeech',Language='zh',Country='CHN',SpeechRate=1)])
    restore=p.chain(p.setvar('播报中',p.boolean(False)),p.set('SpeakButton','Enabled',p.boolean(True)),p.set('StatusLabel','Text',p.text('待播报')))
    speak=p.iff(empty(p,p.trim(p.get('MessageBox','Text'))),p.set('StatusLabel','Text',p.text('请先输入文字')),p.chain(
        p.setvar('手动停止',p.boolean(False)),p.setvar('播报中',p.boolean(True)),p.set('SpeakButton','Enabled',p.boolean(False)),p.set('Voice','SpeechRate',p.get('RateSlider','ThumbPosition')),p.set('StatusLabel','Text',p.text('正在朗读…')),p.method('Voice','Speak',p.trim(p.get('MessageBox','Text')))))
    after=p.chain(p.call('恢复按钮'),p.iff(p.var('手动停止'),p.set('StatusLabel','Text',p.text('已停止')),
        p.iff(p.param('result',True),p.set('StatusLabel','Text',p.text('朗读完成')),p.set('StatusLabel','Text',p.text('语音不可用，请检查中文语音引擎')))))
    p.tops=[p.global_('播报中',p.boolean(False)),p.global_('手动停止',p.boolean(False)),p.define('恢复按钮',restore),
        p.event('SpeakButton','Click',speak),p.event('Voice','AfterSpeaking',after),
        p.event('StopButton','Click',p.chain(p.setvar('手动停止',p.boolean(True)),p.method('Voice','Stop'),p.call('恢复按钮'),p.set('StatusLabel','Text',p.text('已停止')))),
        p.event('RateSlider','PositionChanged',p.chain(p.set('Voice','SpeechRate',p.param('thumbPosition',True)),p.set('RateLabel','Text',p.join(p.text('语速：'),p.div(p.b('math_round',{'OP':'ROUND'},{'NUM':p.mul(p.param('thumbPosition',True),p.num(10))}),p.num(10)),p.text(' 倍')))))]
    p.class_tops=[copy.deepcopy(p.tops[i]) for i in [0,1,2,5,6]]
    return p,dict(work='带语速和完成反馈的语音助手',classroomKept=['全部变量','恢复按钮','StopButton.Click','RateSlider.PositionChanged'],classroomTasks=['添加SpeakButton.Click，检查空白并调用Speak','添加Voice.AfterSpeaking，按result恢复并反馈','保留手动停止标志，避免停止后误报引擎故障'],screenshotGroups=['SpeakButton.Click','RateSlider.PositionChanged','Voice.AfterSpeaking'],
        tests=[dict(set={'MessageBox.Text':'   '},event='SpeakButton.Click',expect={'StatusLabel.Text':'请先输入文字','global 播报中':False}),dict(event='SpeakButton.Click',expect={'global 播报中':True,'SpeakButton.Enabled':False},methods=['Voice.Speak']),dict(set={'global 手动停止':False},event='Voice.AfterSpeaking',args={'result':True},expect={'SpeakButton.Enabled':True,'StatusLabel.Text':'朗读完成'}),dict(event='StopButton.Click',expect={'SpeakButton.Enabled':True,'StatusLabel.Text':'已停止'}),dict(set={'global 手动停止':True},event='Voice.AfterSpeaking',args={'result':False},expect={'StatusLabel.Text':'已停止'})],limitations=['中文朗读依赖Android系统语音引擎及已安装语音包','仅验证异步事件逻辑和编译，不声称完成安卓声音实测'])


def build24():
    p=base(24,'YXCourse24','我的声音工作室')
    p.screen([p.page(intro(p,'声音留言工作室','第 24 课｜录制后，用返回的路径试听')+[
        p.label('StateLabel','空闲：录一段自己的声音吧。',FontSize=22,Height=155,BackgroundColor='&HFFFFFFFF'),p.button('RecordButton','开始录音'),
        p.button('StopButton','停止录音／播放',Enabled='False',BackgroundColor='&HFFDCEFFF',TextColor='&HFF123E62'),p.button('PlayButton','试听最新留言',Enabled='False'),
        p.label('HintLabel','首次录音需要麦克风权限。录音留在本机，本课不上传、不做长期录音管理。',FontSize=15,TextColor='&HFF56758B')]),
        p.comp('Recorder','SoundRecorder'),p.comp('AudioPlayer','Player',Loop='False',PlayOnlyInForeground='True',Volume=80)])
    idle=lambda:p.eq(p.var('状态'),p.text('空闲'))
    refresh=p.chain(p.set('RecordButton','Enabled',idle()),p.set('StopButton','Enabled',negate(p,idle())),p.set('PlayButton','Enabled',p.both(idle(),negate(p,empty(p,p.var('录音路径'))))))
    back=lambda msg:p.call('回到空闲',msg,names=('提示',))
    stop=p.iff(p.eq(p.var('状态'),p.text('录音中')),p.chain(p.setvar('状态',p.text('停止录音中')),p.set('StateLabel','Text',p.text('正在停止录音，等待新音频路径…')),p.method('Recorder','Stop')),
        p.iff(p.eq(p.var('状态'),p.text('准备录音')),p.chain(p.method('Recorder','Stop'),back(p.text('已取消本次录音准备'))),p.chain(p.method('AudioPlayer','Stop'),back(p.text('播放已停止')))))
    p.tops=[p.global_('状态',p.text('空闲')),p.global_('录音路径',p.text('')),p.define('刷新按钮',refresh),p.define('回到空闲',p.chain(p.setvar('状态',p.text('空闲')),p.call('刷新按钮'),p.set('StateLabel','Text',p.param('提示'))),args=('提示',)),
        p.event('RecordButton','Click',p.chain(p.method('AudioPlayer','Stop'),p.setvar('状态',p.text('准备录音')),p.call('刷新按钮'),p.set('StateLabel','Text',p.text('等待麦克风权限与开始录音回调…')),p.method('Recorder','Start'))),
        p.event('Recorder','StartedRecording',p.chain(p.setvar('状态',p.text('录音中')),p.call('刷新按钮'),p.set('StateLabel','Text',p.text('录音中…点击停止结束这段留言。')))),
        p.event('StopButton','Click',stop),p.event('Recorder','AfterSoundRecorded',p.iff(negate(p,empty(p,p.param('sound',True))),p.chain(p.setvar('录音路径',p.param('sound',True)),p.set('AudioPlayer','Source',p.param('sound',True)),back(p.text('新留言已就绪，可以试听。'))),back(p.text('没有取得录音文件，请重新录制')))),
        p.event('PlayButton','Click',p.iff(p.both(idle(),negate(p,empty(p,p.var('录音路径')))),p.chain(p.setvar('状态',p.text('播放中')),p.call('刷新按钮'),p.set('StateLabel','Text',p.text('正在播放最新留言…')),p.method('AudioPlayer','Start')))),
        p.event('AudioPlayer','Completed',back(p.text('试听完成'))),p.event('Screen1','PermissionDenied',p.chain(p.method('AudioPlayer','Stop'),back(p.text('麦克风权限被拒绝，请在系统设置中允许后重试')))),
        p.event('Screen1','ErrorOccurred',back(p.join(p.text('本次操作未完成：'),p.param('message',True)))),
        p.event('Recorder','StoppedRecording',p.iff(p.b('logic_operation',{'OP':'OR'},{'A':p.eq(p.var('状态'),p.text('录音中')),'B':p.eq(p.var('状态'),p.text('停止录音中'))},mutation={'items':2}),back(p.text('录音已停止；若已生成文件，将由回调提供。'))))]
    p.class_tops=[copy.deepcopy(p.tops[i]) for i in [0,1,2,3,4,5,6,9,10,11,12]]
    return p,dict(work='录音留言与试听',classroomKept=['全部变量和按钮状态过程','RecordButton、StartedRecording、StopButton','Completed、PermissionDenied、ErrorOccurred、StoppedRecording异常恢复'],classroomTasks=['添加Recorder.AfterSoundRecorded，保存sound并设置AudioPlayer.Source','添加PlayButton.Click，有路径且空闲时启动试听','录第二段后检查播放源已更新'],screenshotGroups=['RecordButton.Click','Recorder.AfterSoundRecorded','PlayButton.Click'],tests=[dict(event='RecordButton.Click',expect={'global 状态':'准备录音','RecordButton.Enabled':False},methods=['AudioPlayer.Stop','Recorder.Start']),dict(event='Recorder.StartedRecording',expect={'global 状态':'录音中'}),dict(event='Recorder.AfterSoundRecorded',args={'sound':'file:///recording-2.m4a'},expect={'global 录音路径':'file:///recording-2.m4a','AudioPlayer.Source':'file:///recording-2.m4a','PlayButton.Enabled':True}),dict(set={'global 录音路径':'file:///r.m4a'},event='PlayButton.Click',expect={'global 状态':'播放中'},methods=['AudioPlayer.Start']),dict(event='Screen1.PermissionDenied',args={'permissionName':'android.permission.RECORD_AUDIO'},expect={'global 状态':'空闲','RecordButton.Enabled':True})],limitations=['Android录音权限、麦克风和真实音频路径需课堂真机核验；本次未实测','保存的是本次录音组件返回的引用，不承诺卸载后或跨设备保留'])


def build25():
    p=base(25,'YXCourse25','拍照与图片创作')
    p.screen([p.page(intro(p,'我的照片介绍卡','第 25 课｜选照片，写一段说明')+[
        p.comp('PhotoImage','Image',Picture='',Width=-2,Height=240,ScalePictureToFit='True',AlternateText='当前选择的照片'),
        p.comp('PhotoButtons','HorizontalArrangement',[p.button('CameraButton','拍一张',Width=-1050),p.comp('PhotoPicker','ImagePicker',Text='从相册选图',Width=-1050,Height=52,FontSize=17,BackgroundColor='&HFF1388CC',TextColor='&HFFFFFFFF')],Width=-2,Height=58),
        p.comp('TitleBox','TextBox',Text='',Hint='照片标题',Width=-2,Height=52,FontSize=20,BackgroundColor='&HFFFFFFFF'),
        p.comp('CaptionBox','TextBox',Text='',Hint='写一段介绍',MultiLine='True',Width=-2,Height=100,FontSize=18,BackgroundColor='&HFFFFFFFF'),
        p.button('ApplyButton','生成介绍卡'),p.label('CardLabel','标题和说明会显示在这里。',FontSize=21,Height=135,BackgroundColor='&HFFFFFFFF'),
        p.label('StatusLabel','尚未选择照片。',FontSize=14,Height=65),p.button('ResetButton','清空作品',BackgroundColor='&HFFDCEFFF',TextColor='&HFF123E62')]),p.comp('Camera1','Camera')])
    show=p.iff(negate(p,empty(p,p.param('路径'))),p.chain(p.setvar('图片路径',p.param('路径')),p.set('PhotoImage','Picture',p.param('路径')),p.set('StatusLabel','Text',p.text('已选择照片；填写标题和说明。'))))
    p.tops=[p.global_('图片路径',p.text('')),p.define('显示图片',show,args=('路径',)),p.define('清空卡片',p.chain(p.setvar('图片路径',p.text('')),p.set('PhotoImage','Picture',p.text('')),p.set('TitleBox','Text',p.text('')),p.set('CaptionBox','Text',p.text('')),p.set('CardLabel','Text',p.text('')),p.set('StatusLabel','Text',p.text('作品已清空。')))),
        p.event('CameraButton','Click',p.chain(p.set('StatusLabel','Text',p.text('等待相机返回；取消时保留原照片，可继续操作。')),p.method('Camera1','TakePicture'))),
        p.event('Camera1','AfterPicture',p.call('显示图片',p.param('image',True),names=('路径',))),p.event('PhotoPicker','AfterPicking',p.call('显示图片',p.get('PhotoPicker','Selection'),names=('路径',))),
        p.event('ApplyButton','Click',p.iff(empty(p,p.trim(p.get('TitleBox','Text'))),p.set('StatusLabel','Text',p.text('请先输入照片标题')),p.chain(p.set('CardLabel','Text',p.join(p.trim(p.get('TitleBox','Text')),p.text('\n'),p.trim(p.get('CaptionBox','Text')))),p.set('StatusLabel','Text',p.text('介绍卡已生成，仅在本机展示。'))))),
        p.event('ResetButton','Click',p.call('清空卡片')),p.event('Screen1','PermissionDenied',p.set('StatusLabel','Text',p.text('相机或照片权限被拒绝；可调整权限后重试，或保留已有作品。'))),
        p.event('Screen1','ErrorOccurred',p.set('StatusLabel','Text',p.join(p.text('本次未取得新图片，原作品保留：'),p.param('message',True))))]
    p.class_tops=[copy.deepcopy(p.tops[i]) for i in [0,1,2,3,7,8,9]]
    return p,dict(work='本机照片与文字介绍卡',classroomKept=['global 图片路径','显示图片、清空卡片','相机启动、重置及权限/异常反馈'],classroomTasks=['添加Camera1.AfterPicture，使用image回调路径','添加PhotoPicker.AfterPicking，复用显示图片','添加ApplyButton.Click，校验非空标题并拼接说明'],screenshotGroups=['Camera1.AfterPicture','PhotoPicker.AfterPicking','ApplyButton.Click'],tests=[dict(event='Camera1.AfterPicture',args={'image':'content://photo/7'},expect={'global 图片路径':'content://photo/7','PhotoImage.Picture':'content://photo/7'}),dict(set={'global 图片路径':'old','PhotoImage.Picture':'old','PhotoPicker.Selection':''},event='PhotoPicker.AfterPicking',expect={'global 图片路径':'old','PhotoImage.Picture':'old'}),dict(set={'TitleBox.Text':'  '},event='ApplyButton.Click',expect={'StatusLabel.Text':'请先输入照片标题'}),dict(set={'TitleBox.Text':'我的植物','CaptionBox.Text':'今天长出了新叶。'},event='ApplyButton.Click',expect={'CardLabel.Text':'我的植物\n今天长出了新叶。'}),dict(event='ResetButton.Click',expect={'PhotoImage.Picture':'','TitleBox.Text':'','CaptionBox.Text':'','CardLabel.Text':''})],limitations=['取消相机或照片选择器通常不产生成功回调；启动时不清旧图且不锁定界面，因此可继续使用原作品','Android相机/照片URI和权限未进行真机实测'])


def build26():
    p=base(26,'YXCourse26','摇一摇，触发新玩法')
    p.screen([p.page(intro(p,'摇一摇骰子','第 26 课｜一次触发，一次随机结果')+[
        p.label('DiceLabel','1',FontSize=80,FontBold='True',Height=170,TextAlignment=1,BackgroundColor='&HFFFFFFFF'),
        p.label('CountLabel','投掷次数：0',FontSize=22,Height=55,TextAlignment=1),p.button('RollButton','点击也能掷骰'),
        p.label('HintLabel','可摇动或点击，每次间隔至少1秒。',FontSize=18,Height=120),p.label('NoticeLabel','轻轻摇动，握紧手机。重复点数允许出现，20次观察不能证明随机公平。',FontSize=14,TextColor='&HFF56758B')]),
        p.comp('Motion','AccelerometerSensor',Enabled='True'),p.comp('Cooldown','Clock',TimerInterval=1000,TimerEnabled='False',TimerAlwaysFires='False')])
    ready=p.chain(p.setvar('可掷',p.boolean(True)),p.set('Cooldown','TimerEnabled',p.boolean(False)),p.set('RollButton','Enabled',p.boolean(True)),p.iff(p.get('Motion','Available'),p.set('HintLabel','Text',p.text('可摇动或点击，每次间隔至少1秒。')),p.set('HintLabel','Text',p.text('本设备无加速度传感器，请使用按钮投掷。'))))
    roll=p.iff(p.var('可掷'),p.chain(p.setvar('可掷',p.boolean(False)),p.set('RollButton','Enabled',p.boolean(False)),p.setvar('点数',p.random(p.num(1),p.num(6))),p.setvar('次数',p.add(p.var('次数'),p.num(1))),p.set('DiceLabel','Text',p.var('点数')),p.set('CountLabel','Text',p.join(p.text('投掷次数：'),p.var('次数'))),p.set('HintLabel','Text',p.text('冷却1秒，请稍候…')),p.set('Cooldown','TimerEnabled',p.boolean(True))))
    p.tops=[p.global_('可掷',p.boolean(True)),p.global_('点数',p.num(1)),p.global_('次数',p.num(0)),p.define('恢复掷骰',ready),p.define('掷骰',roll),
        p.event('Motion','Shaking',p.call('掷骰')),p.event('RollButton','Click',p.call('掷骰')),p.event('Cooldown','Timer',p.call('恢复掷骰')),p.event('Screen1','Initialize',p.call('恢复掷骰'))]
    p.class_tops=copy.deepcopy(p.tops[:4])+[p.note(p.define('掷骰',p.chain(p.setvar('点数',p.num(1)),p.set('DiceLabel','Text',p.var('点数')))),'课堂任务：随机1..6、累计次数，并用可掷和Clock加入一秒冷却。')]+copy.deepcopy(p.tops[6:])
    return p,dict(work='带一秒冷却的摇动骰子',classroomKept=['全部变量','恢复掷骰','按钮、Clock、初始化入口','掷骰过程的固定1占位'],classroomTasks=['将固定点数改成1..6随机整数并累计次数','可掷false阻止重复触发，启动Cooldown后由恢复过程重开','添加Motion.Shaking调用掷骰'],screenshotGroups=['掷骰','Cooldown.Timer','Screen1.Initialize'],tests=[dict(events=['Motion.Shaking']*3,expect={'global 次数':1,'global 可掷':False,'Cooldown.TimerEnabled':True}),dict(events=['RollButton.Click','Cooldown.Timer','RollButton.Click'],expect={'global 次数':2}),dict(set={'Motion.Available':False},event='Screen1.Initialize',expect={'RollButton.Enabled':True,'HintLabel.Text':'本设备无加速度传感器，请使用按钮投掷。'})],limitations=['加速度传感器实际灵敏度和摇动事件需课堂真机核验'])


def wall_png():
    """A solid software-game primitive, scaled by ImageSprite, not an illustration."""
    def chunk(name,data):return struct.pack('>I',len(data))+name+data+struct.pack('>I',zlib.crc32(name+data)&0xffffffff)
    return b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',1,1,8,6,0,0,0))+chunk(b'IDAT',zlib.compress(bytes([0,100,116,139,255])))+chunk(b'IEND',b'')


def build27():
    p=base(27,'YXCourse27','倾斜手机控制角色');p.assets['wall.png']=wall_png()
    p.screen([p.page(intro(p,'重力迷宫入门','第 27 课｜倾斜手机，绕开中间的墙')+[
        p.comp('MazeCanvas','Canvas',[p.comp('PlayerBall','Ball',Radius=12,OriginAtCenter='True',Speed=0,X=35,Y=325,PaintColor='&HFF1388CC'),
            p.comp('Wall','ImageSprite',Picture='wall.png',Width=50,Height=160,X=135,Y=100,Speed=0,Rotates='False',OriginX=0,OriginY=0),
            p.comp('Goal','Ball',Radius=22,OriginAtCenter='True',Speed=0,X=280,Y=40,PaintColor='&HFFF2BE4A')],Width=-2,Height=360,BackgroundColor='&HFFFFFFFF'),
        p.comp('MazeButtons','HorizontalArrangement',[p.button('StartButton','开始／重开',Width=-1050),p.button('ModeButton','切换操作模式',Width=-1050,BackgroundColor='&HFFDCEFFF',TextColor='&HFF123E62')],Width=-2,Height=58),
        p.label('StatusLabel','未开始。倾斜或切换触摸模式。',FontSize=19,Height=100),p.label('HintLabel','蓝球碰灰墙回起点，到金色终点获胜。竖屏设备方向可能不同，应记录左右/前后校准。',FontSize=14,TextColor='&HFF56758B')]),
        p.comp('Sensor','OrientationSensor',Enabled='True'),p.comp('MoveClock','Clock',TimerInterval=40,TimerEnabled='False',TimerAlwaysFires='False')])
    move=p.method('PlayerBall','MoveTo',p.mm('MAX',p.get('PlayerBall','Radius'),p.mm('MIN',p.sub(p.get('MazeCanvas','Width'),p.get('PlayerBall','Radius')),p.param('x'))),p.mm('MAX',p.get('PlayerBall','Radius'),p.mm('MIN',p.sub(p.get('MazeCanvas','Height'),p.get('PlayerBall','Radius')),p.param('y'))))
    reset=p.chain(p.method('PlayerBall','MoveTo',p.num(35),p.sub(p.get('MazeCanvas','Height'),p.num(35))),p.setvar('vx',p.num(0)),p.setvar('vy',p.num(0)))
    start=p.chain(p.setvar('运行中',p.boolean(False)),p.call('触障复位'),p.method('Wall','MoveTo',p.sub(p.div(p.get('MazeCanvas','Width'),p.num(2)),p.num(25)),p.num(100)),p.method('Goal','MoveTo',p.sub(p.get('MazeCanvas','Width'),p.num(40)),p.num(40)),p.setvar('运行中',p.boolean(True)),p.set('MoveClock','TimerEnabled',p.boolean(True)),p.set('StatusLabel','Text',p.join(p.text('运行中｜模式：'),p.var('模式'))))
    mapped=choose(p,p.cmp('LT',p.b('math_abs',{'OP':'ABS'},{'NUM':p.param('角度')}),p.num(2)),p.num(0),p.mm('MAX',p.num(-6),p.mm('MIN',p.num(6),p.div(p.param('角度'),p.num(5)))))
    collision=p.iff(p.var('运行中'),p.iff(p.eq(p.param('other',True),ref(p,'Wall')),p.chain(p.call('触障复位'),p.set('StatusLabel','Text',p.text('触障复位，继续尝试绕行。'))),
        p.iff(p.eq(p.param('other',True),ref(p,'Goal')),p.chain(p.setvar('运行中',p.boolean(False)),p.set('MoveClock','TimerEnabled',p.boolean(False)),p.setvar('vx',p.num(0)),p.setvar('vy',p.num(0)),p.set('StatusLabel','Text',p.text('胜利！到达终点，点击开始可再玩一局。'))))))
    p.tops=[p.global_('运行中',p.boolean(False)),p.global_('模式',p.text('倾斜')),p.global_('vx',p.num(0)),p.global_('vy',p.num(0)),
        p.define('映射',mapped,args=('角度',),returns=True),p.define('移动球',move,args=('x','y')),p.define('触障复位',reset),p.define('开始',start),
        p.event('Sensor','OrientationChanged',p.chain(p.setvar('vx',p.call('映射',p.param('roll',True),names=('角度',),returns=True)),p.setvar('vy',p.call('映射',p.sub(p.num(0),p.param('pitch',True)),names=('角度',),returns=True)))),
        p.event('MoveClock','Timer',p.iff(p.both(p.var('运行中'),p.eq(p.var('模式'),p.text('倾斜'))),p.call('移动球',p.add(p.get('PlayerBall','X'),p.var('vx')),p.add(p.get('PlayerBall','Y'),p.var('vy')),names=('x','y')))),
        p.event('MazeCanvas','Dragged',p.iff(p.both(p.var('运行中'),p.eq(p.var('模式'),p.text('触摸'))),p.call('移动球',p.param('currentX',True),p.param('currentY',True),names=('x','y')))),
        p.event('PlayerBall','CollidedWith',collision),p.event('ModeButton','Click',p.chain(p.iff(p.get('Sensor','Available'),p.iff(p.eq(p.var('模式'),p.text('倾斜')),p.setvar('模式',p.text('触摸')),p.setvar('模式',p.text('倾斜'))),p.setvar('模式',p.text('触摸'))),p.setvar('vx',p.num(0)),p.setvar('vy',p.num(0)),p.set('StatusLabel','Text',p.join(p.text('当前模式：'),p.var('模式'))))),
        p.event('StartButton','Click',p.call('开始')),p.event('Screen1','Initialize',p.iff(negate(p,p.get('Sensor','Available')),p.chain(p.setvar('模式',p.text('触摸')),p.set('StatusLabel','Text',p.text('本设备无方向传感器，已改用触摸模式。')))))]
    p.class_tops=copy.deepcopy(p.tops[:4])+[p.note(p.define('映射',p.num(0),args=('角度',),returns=True),'课堂任务：绝对值小于2返回0，否则角度/5并限制-6..6。')]+copy.deepcopy(p.tops[5:9])+[copy.deepcopy(p.tops[10])]+copy.deepcopy(p.tops[12:])
    return p,dict(work='倾斜与触摸双模式迷宫',classroomKept=['全部变量','移动球边界限制、触障复位、开始','方向回调与触摸模式入口','模式切换和设备能力检查','映射过程返回0占位'],classroomTasks=['映射实现2°死区、除5缩放、±6上限','添加MoveClock.Timer的X+vx、Y+vy移动','添加PlayerBall.CollidedWith：碰墙复位，碰目标停止并胜利'],screenshotGroups=['映射','MoveClock.Timer','PlayerBall.CollidedWith'],tests=[dict(procedure='映射',args=[0],returns=0),dict(procedure='映射',args=[1],returns=0),dict(procedure='映射',args=[30],returns=6),dict(procedure='映射',args=[-100],returns=-6),dict(set={'global 运行中':True,'MazeCanvas.Height':360},event='PlayerBall.CollidedWith',args={'other':{'component':'Wall'}},expect={'PlayerBall.X':35,'PlayerBall.Y':325,'global 运行中':True}),dict(set={'global 运行中':True},event='PlayerBall.CollidedWith',args={'other':{'component':'Goal'}},expect={'global 运行中':False,'MoveClock.TimerEnabled':False})],limitations=['倾斜轴符号和竖屏方向必须在目标手机校准；本次没有真机校准','wall.png为原创纯色游戏障碍资源，非外部插画'])


def build28():
    p=base(28,'YXCourse28','手机知道我在哪里')
    p.screen([p.page(intro(p,'位置观察站','第 28 课｜主动开始，收到回调才显示位置')+[
        p.comp('LocationButtons','HorizontalArrangement',[p.button('StartButton','开始观察',Width=-1050),p.button('StopButton','停止观察',Width=-1050,BackgroundColor='&HFFDCEFFF',TextColor='&HFF123E62')],Width=-2,Height=58),
        p.label('LatitudeLabel','纬度：—',FontSize=23,Height=55),p.label('LongitudeLabel','经度：—',FontSize=23,Height=55),
        p.label('AccuracyLabel','精度：—｜尚无接收时刻',FontSize=17,Height=95),p.label('SpeedLabel','移动速度：— m/s',FontSize=18,Height=50),p.label('HeadingLabel','方位角：—',FontSize=18,Height=50),
        p.label('StatusLabel','未开始。位置信息只在本机显示。',FontSize=19,Height=145,BackgroundColor='&HFFFFFFFF'),p.label('HintLabel','定位需要系统位置权限和定位服务。经纬度0不是错误标志；停止后保留的只是最后一次观测。',FontSize=14,TextColor='&HFF56758B')]),
        p.comp('Location1','LocationSensor',Enabled='False',TimeInterval=3000,DistanceInterval=1),p.comp('Compass','OrientationSensor',Enabled='False'),p.comp('TimeClock','Clock',TimerEnabled='False',TimerAlwaysFires='False')])
    start=p.chain(p.setvar('观察中',p.boolean(True)),p.setvar('有位置',p.boolean(False)),p.set('LatitudeLabel','Text',p.text('纬度：等待定位…')),p.set('LongitudeLabel','Text',p.text('经度：等待定位…')),p.set('AccuracyLabel','Text',p.text('精度：等待首次位置回调')),p.set('SpeedLabel','Text',p.text('移动速度：— m/s')),p.set('HeadingLabel','Text',p.text('方位角：等待传感器…')),p.set('StatusLabel','Text',p.text('正在等待位置权限与有效位置；室内可能较慢。')),p.set('Location1','Enabled',p.boolean(True)),p.set('Compass','Enabled',p.boolean(True)))
    stop=p.chain(p.setvar('观察中',p.boolean(False)),p.set('Location1','Enabled',p.boolean(False)),p.set('Compass','Enabled',p.boolean(False)),p.iff(p.var('有位置'),p.set('StatusLabel','Text',p.text('已停止：以下为最后一次位置，不是实时位置。')),p.set('StatusLabel','Text',p.text('已停止：本轮尚未取得位置。'))))
    show=p.chain(p.setvar('有位置',p.boolean(True)),p.set('LatitudeLabel','Text',p.join(p.text('纬度：'),p.param('纬度'))),p.set('LongitudeLabel','Text',p.join(p.text('经度：'),p.param('经度'))),
        p.set('AccuracyLabel','Text',p.join(choose(p,p.get('Location1','HasAccuracy'),p.join(p.text('估计精度：'),p.get('Location1','Accuracy'),p.text(' 米')),p.text('精度未知')),p.text('\n本机接收：'),p.method('TimeClock','FormatTime',p.method('TimeClock','Now')))),
        p.set('SpeedLabel','Text',p.join(p.text('移动速度：'),p.param('速度'),p.text(' m/s'))),p.set('StatusLabel','Text',p.text('已收到有效位置。精度是估计范围，不是绝对误差保证。')))
    p.tops=[p.global_('观察中',p.boolean(False)),p.global_('有位置',p.boolean(False)),p.global_('最近纬度',p.num(0)),p.global_('最近经度',p.num(0)),p.define('开始观察',start),p.define('停止观察',stop),p.define('显示位置',show,args=('纬度','经度','速度')),
        p.event('StartButton','Click',p.call('开始观察')),p.event('StopButton','Click',p.call('停止观察')),
        p.event('Location1','LocationChanged',p.iff(p.var('观察中'),p.chain(p.setvar('最近纬度',p.param('latitude',True)),p.setvar('最近经度',p.param('longitude',True)),p.call('显示位置',p.param('latitude',True),p.param('longitude',True),p.param('speed',True),names=('纬度','经度','速度'))))),
        p.event('Location1','StatusChanged',p.iff(p.var('观察中'),p.set('StatusLabel','Text',p.join(p.text('位置服务状态：'),p.param('provider',True),p.text(' / '),p.param('status',True),p.text('；等待位置回调，状态变化不代表取得新位置。'))))),
        p.event('Compass','OrientationChanged',p.iff(p.var('观察中'),p.set('HeadingLabel','Text',p.join(p.text('方位角：'),p.param('azimuth',True),p.text('°（来自方向传感器）'))))),
        p.event('Screen1','PermissionDenied',p.chain(p.call('停止观察'),p.set('StatusLabel','Text',p.text('位置权限被拒绝，请在系统设置允许后重新开始。'))))]
    p.class_tops=copy.deepcopy(p.tops[:4])+[p.note(p.define('开始观察',p.set('StatusLabel','Text',p.text('课堂任务：设置观察中并启用Location1与Compass。'))),'保留默认关闭的传感器，学生主动开始后才启用。')]+copy.deepcopy(p.tops[5:9])+copy.deepcopy(p.tops[10:12])
    return p,dict(work='经纬度、精度、速度与方位观察站',classroomKept=['全部变量','停止观察、显示位置完整过程','开始与停止按钮入口','位置服务状态、方位角回调','开始观察过程占位'],classroomTasks=['开始观察设置状态、清旧提示并启用两个传感器','添加Location1.LocationChanged，仅观察中时保存并显示数据','添加Screen1.PermissionDenied，停止观察并提示权限设置'],screenshotGroups=['开始观察','Location1.LocationChanged','Screen1.PermissionDenied'],tests=[dict(event='StartButton.Click',expect={'global 观察中':True,'Location1.Enabled':True,'Compass.Enabled':True,'global 有位置':False}),dict(set={'global 观察中':True,'Location1.HasAccuracy':False},event='Location1.LocationChanged',args={'latitude':0,'longitude':0,'speed':0},expect={'global 有位置':True,'global 最近纬度':0,'LatitudeLabel.Text':'纬度：0'},contains={'AccuracyLabel.Text':['精度未知']}),dict(set={'global 观察中':True,'global 有位置':True},event='StopButton.Click',expect={'global 观察中':False,'Location1.Enabled':False,'Compass.Enabled':False,'StatusLabel.Text':'已停止：以下为最后一次位置，不是实时位置。'}),dict(set={'global 观察中':False,'global 最近纬度':31},event='Location1.LocationChanged',args={'latitude':32,'longitude':120,'speed':1},expect={'global 最近纬度':31}),dict(event='Screen1.PermissionDenied',expect={'global 观察中':False,'Location1.Enabled':False})],limitations=['没有进行GPS、方向传感器、Android权限或精度真机实测','不调用反向地理编码、不上传位置；方位角来自Compass而非GPS速度'])


def emit_project(number,p,detail):
    folder=OUT/f'lesson{number:02d}';versions=p.write(folder);(folder/'blocks.xml').write_bytes(p.xml('answer'));assets=folder/'assets';assets.mkdir(exist_ok=True)
    for name,value in p.assets.items():(assets/name).write_bytes(value.read_bytes() if isinstance(value,Path) else value)
    def target(top):
        fields={f.get('name'):f.text for f in top.findall('field')};m=top.find('mutation')
        return m.get('instance_name')+'.'+m.get('event_name') if top.get('type')=='component_event' else fields.get('NAME','')
    captures=[]
    for i,name in enumerate(detail['screenshotGroups'],1):
        matches=[(j,b) for j,b in enumerate(p.tops) if target(b)==name]
        if len(matches)!=1:raise ValueError(f'Nonunique capture target {name}')
        j,b=matches[0];captures.append(dict(blockIndex=i,target=name,topLevelIndex=j,blockId=b.get('id')))
    bp=json.loads((BLUEPRINTS/f'lesson{number:02d}.json').read_text(encoding='utf8'))
    spec=dict(lesson=number,title=p.title,projectName=p.name,versions=versions,
        components=[dict(name=n,type=c['$Type'],version=c['$Version'],properties={k:v for k,v in c.items() if not k.startswith('$') and k!='Uuid'}) for n,c in p.components.items()],
        variants=dict(answer='完整参考答案：全部本课规则均已实现',classroom='课堂支架：示范结构与占位任务见classroomKept/classroomTasks',starter='纯界面起始版：组件、属性与素材和答案相同，积木为空'),
        captureGroups=captures,assets=[dict(file=n,source='用户提供的羽轩品牌logo' if n=='logo.png' else '本课程原创纯色游戏图形' if n=='wall.png' else '本课程配套素材') for n in p.assets],sources=bp['sources'],
        staticValidation=dict(componentReferences='pass',designerProperties='pass: exact distribution metadata',eventMethods='pass: exact distribution metadata',valueSockets='pass',assetReferences='pass'),nativeImportValidation='pending',apkCompilation='pending',androidDeviceTest='not requested',**detail)
    (folder/'artifact-spec.json').write_text(json.dumps(spec,ensure_ascii=False,indent=2),encoding='utf8')
    print(json.dumps(dict(lesson=number,project=p.name,versions=[dict(kind=v['kind'],blocks=v['blockCount']) for v in versions]),ensure_ascii=False))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('lessons',nargs='*',type=int,default=list(range(23,29)));args=parser.parse_args()
    for n in args.lessons:
        if not 23<=n<=28:parser.error('This batch covers lessons 23–28')
        emit_project(n,*globals()[f'build{n:02d}']())
