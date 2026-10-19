"""Lesson 23--42 content, aligned to completed AIA specs. No runtime or deck work."""
from pathlib import Path
from copy import deepcopy
import json
import zipfile
import xml.etree.ElementTree as ET
from write_phase1 import write_lesson, agenda
from write_continue import base, component, source, task, question

ROOT = Path(__file__).resolve().parent
DATA = {}

def entry(n, scope, states, flow, tasks, exits, block_notes, **extra):
    DATA[n] = dict(scope=scope, states=states, flow=flow, tasks=tasks,
                   exits=exits, block_notes=block_notes, **extra)

entry(23,
 '语音由Android系统TTS引擎提供；中文离线朗读取决于已安装的语音数据。本课不生成音频文件。',
 [['播报中','假；限制重复朗读'],['手动停止','假；区分停止与引擎失败'],['RateSlider','0.5～1.5；开始时读取语速']],
 ['空白输入：只提示，不发起Speak','有效文字：锁定开始键，再请求朗读','完成或停止：恢复按钮并显示原因'],
 [task('补校验与朗读',['找到Class已给的恢复按钮、Stop与滑块事件。','添加SpeakButton.Click：trim后为空只提示。','有效时先手动停止←假、播报中←真，禁用SpeakButton。','设置Voice.SpeechRate为滑块值，再Speak去空格后的文字。'], '为什么不能在Speak后立刻写“朗读完成”？','Speak是开始请求，整段结束由Voice.AfterSpeaking通知；调用返回不代表播放完成。'),
  task('用已有语速事件做对照实验',['保留RateSlider.PositionChanged，并核对RateLabel。','同一句分别用0.5、1、1.5倍朗读，记录听到的变化。','检查SpeechRate在开始朗读时读取滑块，而非把显示文字当数值。'], '语速标签更新，为什么还要在朗读时设置SpeechRate？','标签只显示反馈；SpeechRate属性才控制引擎，本工程开始时读取当前滑块值。'),
  task('补完成反馈并检查停止',['添加Voice.AfterSpeaking，先恢复按钮。','手动停止为真时显示已停止；否则按result显示完成或语音不可用。','长句中停止，再朗读，检查按钮可恢复。','无语音设备只做事件追踪，听测栏写待测。'], '停止后result=false，应直接判定引擎坏了吗？','不应。先检查手动停止标志；停止引发的回调应保留已停止提示。')],
 [question('三个空格会请求朗读吗？','不会，trim为空时只提示请先输入文字。'),question('AfterSpeaking的result有什么用？','表示引擎报告的成功与否；需结合手动停止标志解释。'),question('没有中文语音包时编译成功能证明会说话吗？','不能，需在具备相应语言数据的设备听测。')],
 ['Class中SpeakButton.Click待补。空白分支不能禁用后不恢复；有效分支先更新状态再Speak。', '这一事件在Class中已经给出，用来阅读、实验并核对RateLabel；不要求重复搭建。SpeechRate在开始朗读时赋值。', '截图对应完成事件；StopButton.Click及恢复过程已给出。手动停止标志防止把正常停止误报为引擎故障。'],
 extra_components=[('RateLabel','Label','显示当前语速倍率')],
 event_overrides={'Voice.AfterSpeaking':'先恢复按钮；若手动停止则显示已停止，否则result真显示朗读完成，假显示语音不可用', 'StopButton.Click':'手动停止←真；Voice.Stop；恢复按钮；状态已停止'},
 procedure_overrides={'恢复按钮':'播报中←假；SpeakButton.Enabled←真；停止按钮恢复相应状态；提示由调用入口决定'})

entry(24,
 '保存的是录音组件返回的本次文件引用，不承诺卸载后、跨设备或长期管理。音频、麦克风权限和真实播放需课堂Android设备验证。',
 [['状态','空闲／准备录音／录音中／播放中'],['录音路径','初始为空；由sound回调提供']],
 ['开始请求：先停播放，显示准备录音','StartedRecording才确认录音开始','sound到达后保存路径，空闲时才可试听'],
 [task('读懂已给的录音入口',['Class已含RecordButton、StartedRecording、StopButton和异常恢复。','沿RecordButton.Click追踪准备录音与Recorder.Start。','分别记录点击时、StartedRecording后和停止后的界面状态。'], '点击开始时就写录音成功，会误导什么？','Start只发起请求，权限或设备可能失败；应等StartedRecording确认。'),
  task('补录音结果与播放来源',['添加Recorder.AfterSoundRecorded，使用事件参数sound。','录音路径←sound，AudioPlayer.Source←sound。','调用回到空闲并给出可试听提示。','录两段不同内容，检查第二次来源已更新。'], '为什么不能把一条电脑绝对路径写进Source？','录音位置由设备组件返回；硬编码电脑路径在手机上无效。'),
  task('补试听并核对恢复入口',['添加PlayButton.Click：有录音路径且状态空闲时才开始。','设置播放中、刷新按钮，再AudioPlayer.Start。','核对已给的Completed、Stop、PermissionDenied和ErrorOccurred。','试听中停止，检查可以重新录制；无设备结果标待测。'], 'AfterSoundRecorded的sound是识别出的文字吗？','不是，是音频文件路径；交给Player.Source后才能试听。')],
 [question('StartedRecording与AfterSoundRecorded分别提供什么？','前者确认开始录制，后者给出录音文件引用。'),question('第二次录音后如何保证试听最新留言？','每次回调同步更新录音路径与AudioPlayer.Source。'),question('为什么拒绝权限后要恢复按钮？','失败也需要结束等待，使用者才能调整权限或继续操作。')],
 ['截图是Class已给的启动事件；读状态顺序，不把它重新布置为缺失任务。', 'Class缺此事件，学生保存sound并设置Source，之后回到空闲；StoppedRecording恢复已给出，不能假定它就是音频文件结果。', 'Class缺试听事件；Completed、停止、权限及错误恢复已有。播放仅在有路径且空闲时发起。'],
 event_overrides={'PlayButton.Click':'若录音路径非空且状态为空闲：状态←播放中；刷新按钮；AudioPlayer.Start', 'Recorder.StoppedRecording':'若仍处于录音相关状态则恢复空闲；文件引用仍等待AfterSoundRecorded'})

entry(25,
 '本课在本机显示照片和文字，不上传。启动相机或选择器时保留旧作品；取消可能没有成功回调，不能靠等待回调锁定界面。实际URI和权限需设备验证。',
 [['图片路径','初始为空；来自相机或相册'],['image','AfterPicture的图片引用'],['PhotoPicker.Selection','相册返回的图片引用']],
 ['相机或相册：把非空结果交给显示图片','生成卡片：校验标题，再拼接说明','取消保留旧作；清空必须明确点击按钮'],
 [task('补相机结果事件',['Class已给相机启动、显示图片和清空卡片。','添加Camera1.AfterPicture。','把事件参数image传入显示图片，不提前猜测文件路径。'], '为什么TakePicture后不能立即显示本次结果？','拍摄在外部界面进行，新的image要等AfterPicture回调。'),
  task('相册复用显示过程',['添加PhotoPicker.AfterPicking。','将PhotoPicker.Selection传给显示图片。','已有照片时打开相册后取消，检查旧图不被擦除。','对照显示图片内非空路径保护。'], '取消为什么不等于清空？','取消没有新的有效选择；只有非空结果替换旧图，清空由单独按钮执行。'),
  task('补标题校验和介绍卡',['添加ApplyButton.Click，trim标题为空时只在StatusLabel提示。','有效时把标题、换行和说明连接到CardLabel。','生成后取消拍照，确认现有作品仍可使用。','重置后检查图、标题、说明和输出都已清空。'], '只清空CardLabel能叫清空作品吗？','不能，还要清图片路径、Picture、TitleBox和CaptionBox，避免旧素材残留。')],
 [question('相机和相册为什么能共用一个过程？','两者最终都提供图片引用，显示图片处理共同的非空检查和Picture赋值。'),question('空标题时改写CardLabel会有什么问题？','可能擦掉已有作品；本工程在StatusLabel提示并保留原卡片。'),question('取消相机没回调，界面如何继续用？','启动时不清旧图且不锁界面，原作品和其他操作仍可用。')],
 ['只在AfterPicture里使用image。Class已给TakePicture入口，不要求再添加重复事件。', '显示图片为共用过程；空Selection不更新。系统URI不应手工改成电脑路径。', '标题提示写StatusLabel；有效输出写CardLabel。权限与异常反馈保留旧作，取消不是成功拍摄。'],
 extra_components=[('StatusLabel','Label','操作、权限和输入校验反馈')],
 event_overrides={'ApplyButton.Click':'trim标题为空时StatusLabel提示请先输入照片标题；否则CardLabel←去空格标题+换行+去空格说明', 'Screen1.ErrorOccurred':'显示错误提示，保留已有照片与卡片，不把异常当作清空'},
 tests_extra=[('已有作品时取消相机','旧照片与文字保留，可以继续生成或清空')])

entry(26,
 '按钮替代入口始终保留；加速度传感器是否可用与灵敏度取决于设备。一秒冷却由Clock安排，不作为精密计时；20次样本不能证明随机公平。',
 [['可掷','真；过程入口的冷却开关'],['点数','初始1；有效范围1～6'],['次数','初始0；每次有效投掷加1']],
 ['按钮和摇动都调用掷骰','可掷为真才随机、累计并关闭入口','Cooldown到时恢复入口，并关闭自己'],
 [task('修正支架中的固定结果',['在掷骰过程中找到固定点数1。','替换为1～6随机整数，并把次数加1。','更新DiceLabel与CountLabel。','连续观察多次，允许连续出现相同点数。'], '为什么随机6次不必恰好每面一次？','每次独立取范围内随机值，不要求短样本平均或不重复。'),
  task('补完整冷却规则',['在掷骰入口检查可掷。','有效时先可掷←假，禁用按钮，再生成一次结果。','启动Cooldown，读取已给的恢复掷骰与Timer。','冷却内连续触发三次，次数应只增加1。'], '为什么必须先关入口再随机？','先关入口能让后续重复事件被保护；等到最后才关会留下重复处理机会。'),
  task('连接传感器并核对替代入口',['添加Motion.Shaking并调用掷骰。','保留RollButton.Click和Screen1.Initialize的能力检查。','无传感器时用按钮完成冷却后再投掷的测试。','记录20次结果及是否越界，不宣称证明公平。'], '没有传感器是否必须放弃作品？','不必，按钮调用相同过程，可体验同样的随机和冷却规则。')],
 [question('一次摇动触发三次事件，为什么只计一次？','可掷在第一轮先设为假，其余在冷却内被忽略。'),question('Cooldown恢复后为什么关闭自身？','本次冷却已完成，关闭可避免无意义的连续Timer。'),question('连续两个6是否说明程序错误？','不一定，合法随机允许重复；应先查范围和事件计数。')],
 ['Class的掷骰过程含固定1占位，随机、累计和入口保护需学生补齐。', 'Timer与恢复过程已给出，用于阅读验证；一秒为教学冷却设置，不宣称精密周期。', '能力检查已给出；学生补Motion.Shaking后验证按钮与传感器走同一过程。'])

entry(27,
 '倾斜roll/pitch轴向和符号需在目标竖屏手机校准。wall.png为原创纯色障碍资源。触摸替代用于验证游戏规则，不用传感器也能先做逻辑检查。',
 [['运行中','假；限制胜利后的移动'],['模式','倾斜／触摸'],['vx、vy','初始0；每次移动的像素量'],['映射(角度)','死区2°，除5缩放，限于±6']],
 ['方向回调保存vx、vy，Clock按节奏应用','触摸模式使用另一入口，同样限制边界','碰墙复位；碰Goal停止并显示胜利'],
 [task('补映射过程的返回值',['找到Class中返回0的映射过程。','绝对角度小于2时返回0。','其余返回max(-6,min(6,角度/5))。','手算0、1、30、-100的结果，再检查积木。'], '死区与上限分别解决什么？','死区减少近水平时微小漂移；上限限制单次位移过大。'),
  task('补Clock移动',['添加MoveClock.Timer。','仅运行中且为倾斜模式时调用移动球。','x为PlayerBall.X+vx，y为PlayerBall.Y+vy。','保持Ball.Speed为0，由过程限制中心坐标。'], '为何不同时设置Ball.Speed为非零？','会叠加另一套自动运动，难以解释每次位移及碰撞规则。'),
  task('补碰撞并比较两种输入',['添加PlayerBall.CollidedWith。','other为Wall时调用触障复位；other为Goal时运行中←假并停Clock。','切到触摸模式验证碰墙和胜利，再测试重开。','传感器方向若相反，先记录设备方向再校准符号。'], '到达目标后只显示胜利文字够吗？','不够，还应停止运行和Clock，防止胜利后继续移动。')],
 [question('映射(-100)为什么是-6？','先除5得到-20，再受下限-6限制。'),question('OrientationChanged和Timer各做什么？','前者采样并保存速度，后者按节奏把速度加到位置。'),question('触摸模式能证明倾斜轴方向正确吗？','不能，只能先验游戏规则；轴向需要真机校准。')],
 ['映射是带返回值过程，Class返0占位。角度恰为2不在小于2的死区内。', '速度由方向回调保存。移动球过程已给边界限制，不要在两个入口重复写不同边界规则。', 'Wall为实际1×1纯色PNG拉伸的障碍；不是品牌图标。触摸模式已给入口，胜利和重开仍须按规则检查。'])

entry(28,
 '本课只在本机观察位置，不反向地理编码或上传。室内等待和精度取决于设备服务。0,0可以是合法经纬度；是否有效由回调与有位置标志判断。',
 [['观察中','假；控制是否接收更新'],['有位置','假；收到LocationChanged才变真'],['最近纬度、最近经度','初始0；数值0不代表无效'],['HasAccuracy','决定显示数值精度或精度未知']],
 ['用户开始：清旧提示，启用位置与方位','LocationChanged到达才显示有效位置','停止后保留最后结果，标明不是实时'],
 [task('补开始观察过程',['找到Class中开始观察占位过程。','观察中←真，有位置←假，清旧提示。','启用Location1和Compass，显示等待位置。','首次打开前不自动启用定位。'], '为什么开始时重设有位置为假？','防止旧数值被当作本次已经获得的新位置。'),
  task('补实际位置回调',['添加Location1.LocationChanged。','仅观察中时保存latitude、longitude。','调用显示位置(latitude,longitude,speed)。','阅读已给过程：speed单位m/s；HasAccuracy假显示精度未知。'], '收到latitude=0、longitude=0能判定定位失败吗？','不能；0,0可能是合法位置，成功回调才是有位置的证据。'),
  task('补权限恢复并核对停止',['添加Screen1.PermissionDenied，停止观察并提示权限设置。','阅读已给StatusChanged：它报告服务状态，不冒充新位置。','有效结果后停止，核对两组件Enabled都为假。','再来的位置回调应被忽略，页面标记最后结果。'], 'Location1.StatusChanged能替代LocationChanged吗？','不能，服务状态变化没有提供本次经纬度，不应切成已定位。')],
 [question('Accuracy未知时为什么不能显示0米？','0米会误导为极高精度；需检查HasAccuracy并写精度未知。'),question('速度与方位分别来自哪里？','速度来自位置回调speed，单位m/s；方位角来自Compass。'),question('停止后保留旧数值为什么必须标记？','避免使用者把最后一次位置误认为仍在实时更新。')],
 ['Class保留按钮入口但开始观察过程待补。位置与方位传感器都须按用户操作启停。', '显示位置已给出；包含SpeedLabel与精度未知保护。接收时刻表示本机收到回调，不宣称测量绝对准确。', '权限拒绝后先停观察再提示，所有操作入口仍可继续。具体权限行为由Android课堂设备另验。'],
 extra_components=[('SpeedLabel','Label','显示位置回调速度，单位m/s')],
 event_overrides={'Location1.StatusChanged':'仅显示provider与status，不设置有位置、不替换经纬度'},
 tests_extra=[('以0,0回调且HasAccuracy为假','标为有位置，显示0经纬度与精度未知')])

def actual_index(spec):
    with zipfile.ZipFile(spec['versions'][0]['file']) as archive:
        document = ET.fromstring(archive.read(next(p for p in archive.namelist() if p.endswith('.bky'))))
    for item in document.iter(): item.tag = item.tag.split('}')[-1]
    result = dict(globals=[], procedures={}, events=[])
    for block in document:
        typ = block.get('type')
        fields = {f.get('name'): f.text for f in block.findall('field')}
        mutation = block.find('mutation')
        if typ == 'global_declaration': result['globals'].append(fields['NAME'])
        elif typ in ('procedures_defreturn', 'procedures_defnoreturn'):
            result['procedures'][fields['NAME']] = [arg.get('name') for arg in mutation.findall('arg')] if mutation is not None else []
        elif typ == 'component_event': result['events'].append(mutation.get('instance_name')+'.'+mutation.get('event_name'))
    return result

def make(n):
    b = json.loads((ROOT.parent/'blueprints'/f'lesson{n:02}.json').read_text(encoding='utf8'))
    spec = json.loads((ROOT.parent/'aia'/f'lesson{n:02}'/'artifact-spec.json').read_text(encoding='utf8'))
    a = DATA[n]
    for pos, replacement in a.get('capture_overrides', {}).items():
        b['blockCaptures'][pos].update(replacement)
        b['slides'][11+2*pos].update({k:v for k,v in replacement.items() if k in ('title','body','notes')})
    index = actual_index(spec)
    by_name = {x['name']: x for x in spec['components']}
    comps = [component(c['name'], by_name[c['name']]['type'], c['role']) for c in b['components'] if c['name'] in by_name]
    for name, kind, role in a.get('extra_components', []):
        assert by_name[name]['type'] == kind
        if name not in {c['name'] for c in comps}: comps.append(component(name, kind, role))
    assert len(b['slides']) == 24
    slides = deepcopy(b['slides'])
    slides[0]['title'] = b['title']
    slides[0]['body'] = [spec['work'], '90分钟 · App Inventor创意编程']
    slides[0]['notes'] = b['appDescription']+' '+a['scope']+' 完整答案用于体验；课堂先发Class版。实际导入、编译或设备验证以最终验证说明为准。'
    slides[5]['body'] = a.get('designer_body', [c['role'] for c in comps[:4]])
    slides[5]['notes'] += ' Designer截图表示组件设计，不能当作按钮逻辑或Android硬件运行证据。'
    # Keep blueprint's 24-page teaching order; limit tables to six data rows.
    slides[6]['table'] = [['组件名','类型','作品中的任务']]+[[c['name'],c['type'],c['role']] for c in comps[:6]]
    slides[6]['notes'] += ' 完整组件表见教师教案，英文名用于准确定位。'
    slides[7]['table'] = [['名称','初值或意义']]+a['states']
    slides[7]['notes'] = '以实际AIA变量和组件为准。先分清持久数据、运行状态、回调参数和可见标签；辅助变量详见教师核对。'
    slides[10]['body'] = a['flow']
    slides[10]['notes'] = a.get('flow_notes', '按事件→状态→反馈追踪一次操作。')+' Class保留：'+'；'.join(spec['classroomKept'])+'。学生任务：'+'；'.join(spec['classroomTasks'])+'。'
    for pos, capture in enumerate(b['blockCaptures']):
        target = spec['screenshotGroups'][pos]
        assert capture['target'] == target, (n, capture['target'],target)
        bp = slides[11+2*pos]
        bp['blockIndex'] = pos+1
        bp['captureTarget'] = target
        bp['notes'] = a['block_notes'][pos]+' 实际截图对应：'+target+'。'+a['scope']
        if pos in a.get('block_body', {}): bp['body'] = a['block_body'][pos]
        tp = slides[12+2*pos]
        t = a['tasks'][pos]
        tp['title'] = t['title']
        tp['body'] = a.get('task_body', {}).get(pos, t['steps'][:3])
        tp['notes'] = '实践15分钟。'+t['question']+' 教师参考：'+t['answer']+' 先让学生独立尝试，再对照积木；已经给出的结构用于阅读和测试。'
    tests = deepcopy(a.get('tests', b['tests']))
    for action, expected in a.get('tests_extra', []): tests.append(dict(action=action,expected=expected))
    slides[17]['table'] = [['操作或输入','预期结果']]+[[x['action'],x['expected']] for x in tests[:4]]
    slides[19]['table'] = [['操作或输入','应观察到']]+[[x['action'],x['expected']] for x in tests[:4]]
    for pos, replacement in a.get('slide_overrides', {}).items(): slides[pos-1].update(replacement)
    slides[23]['body'] = [q['q'] for q in a['exits']]
    slides[23]['layout'] = 'question'
    slides[23]['notes'] = '\n'.join(f"{i+1}. {q['a']}" for i,q in enumerate(a['exits']))+' 留下一项具体测试结果和仍需解决的问题。'
    slots = [(0,10,'1–5'), (10,25,'6–11'), (25,40,'12–13'), (40,55,'14–15'), (55,70,'16–18'), (70,80,'19–22'), (80,90,'23–24')]
    schedule = []
    for i,(start,end,pages) in enumerate(slots):
        teacher = (['展示作品、收集预测，区分演示与实测。','结合组件树与两条核心概念做短示范。']+[f"组织任务：{t['title']}，先问再示范。" for t in a['tasks']]+['用具体故障引导排查，组织微改编和同伴复测。','围绕规则、结果与修改证据组织展示和出口题。'])[i]
        student = (['观察现象，预测一个正常输入与一个边界。','定位状态与事件，手工追踪一个具体输入。']+[f"按任务单完成：{t['title']}。" for t in a['tasks']]+['交换操作者，记录修改前后的同一用例。','导出个人AIA、提交任务单并说明来源。'])[i]
        evidence = (['能用输入、状态与反馈描述作品。','能指出一个回调参数或状态的来源。']+[t['question'] for t in a['tasks']]+['基础规则保留，测试记录含预期和实际。','一项规则、一条证据和一个待解决问题。'])[i]
        schedule.append((start,end,pages,teacher,student,evidence))
    sources = [source('MIT '+u.split('/')[-1]+' 官方参考',u,'核对本课使用的组件、属性和事件；实际接口以随课AIA和元数据为准。') for u in b['sources']]
    payload = base(n,b['title'],spec['work'],a.get('goals',b['learningObjectives']),b['appDescription'],a['scope'],comps,a['tasks'],tests,a.get('pitfalls',b['pitfalls']),
                   ['完成课堂支架中的关键逻辑，记录一个正常和一个边界结果。']+b['remix'][:2],a['exits'],schedule,slides,sources)
    rename = {'选择有效?':'选择有效','提交中':'请求中'}
    def ren(text):
        for old,new in rename.items(): text=text.replace(old,new)
        return text
    events = {ren(k):ren(v) for k,v in b['events'].items()}
    events.update(a.get('event_overrides', {}))
    payload['exampleSpec']['logic'] = [dict(event=name,actions=[description]) for name,description in events.items() if name in index['events']]
    procedures = {ren(k):ren(v) for k,v in b['procedures'].items()}
    procedures.update(a.get('procedure_overrides', {}))
    payload['exampleSpec']['procedures'] = {k:v for k,v in procedures.items() if k.split('(')[0].split('（')[0] in index['procedures']}
    payload['actualClassroomKept'] = spec['classroomKept']
    payload['actualClassroomTasks'] = spec['classroomTasks']
    payload['actualScreenshotGroups'] = spec['screenshotGroups']
    payload['actualProgramIndex'] = index
    payload['actualExpectedOutputs'] = spec['tests']
    payload['artifactSpec'] = str(ROOT.parent/'aia'/f'lesson{n:02}'/'artifact-spec.json')
    payload['blueprintSlideOrder'] = True
    return payload, b, spec, a

def emit(n):
    content, blueprint, spec, a = make(n)
    folder = write_lesson(content)
    plan_path = folder/'教师教案.md'
    plan = plan_path.read_text(encoding='utf8')
    extras = '## 课堂支架与实际程序核对\n\n已给结构：\n\n'+'\n'.join('- '+x for x in spec['classroomKept'])+'\n\n学生要补或修正：\n\n'+'\n'.join('- '+x for x in spec['classroomTasks'])+'\n\n'
    extras += '实际全局变量：'+ '、'.join('`'+x+'`' for x in content['actualProgramIndex']['globals'])+'。\n\n'
    extras += '### 过程职责（教师参考）\n\n'+'\n'.join('- `'+k+'`：'+v+'。' for k,v in content['exampleSpec']['procedures'].items())+'\n\n'
    extras += '### 三组真实积木截图\n\n'+'\n'.join(f"{i+1}. `{target}`：{a['block_notes'][i]}" for i,target in enumerate(spec['screenshotGroups']))+'\n\n'
    extras += '### 设备与验证边界\n\n'+a['scope']+'\n\n'+'\n'.join('- '+x for x in blueprint.get('deviceRequirements', []))+'\n\n'
    if 37<=n<=42:
        extras += ('### 共用课堂服务\n\n教师使用随课 `teaching-api/teaching_server.py`；Python 3.8或3.13均可，无需第三方库。先在电脑浏览器核对欢迎接口。手机课堂运行 `python teaching_server.py --host 0.0.0.0`，使用电脑实际局域网IPv4。HostBox仅填IP，例如192.168.1.8；工程初值192.168.1.10是示例，不是固定地址。不要填协议、端口或路径；端口8765和接口路径由积木拼接。手机与电脑需在可互通的教学局域网，手机的127.0.0.1表示手机自身。\n\n'
                   '可重复故障：先停止当前服务，再加 `--scenario delay`（GET延迟6秒，对照APP超时5秒）、`error`（GET 500）、`empty`（空公告/活动）、`invalid-json`（坏JSON）。恢复用 `--scenario normal`。普通AIA按钮即可触发，不改HostBox为路径，也无需物理断网。POST超时不自动重发；先查结果再决定是否重试。示例仅教学数据，无账号权限系统，勿作为生产留言平台。\n\n')
    plan = plan.replace('## 核心任务与参考答案',extras+'## 核心任务与参考答案')
    plan_path.write_text(plan,encoding='utf8')
    assert len(content['slides'])==24
    assert sum(x['minutes'] for x in content['agenda'])==90
    assert all(s['notes'] for s in content['slides'])
    return folder

if __name__ == '__main__':
    import argparse
    parser=argparse.ArgumentParser()
    parser.add_argument('--start',type=int,default=23)
    parser.add_argument('--end',type=int,default=28)
    args=parser.parse_args()
    for n in range(args.start,args.end+1): print(emit(n))
