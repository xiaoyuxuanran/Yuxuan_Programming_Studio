"""Author the six distinct beginner projects and their three teaching variants."""
from pathlib import Path
import argparse
import copy
import io
import json
import math
import struct
import wave

from aia_core import AiaProject, ROOT

OUT = ROOT / 'work/course56/aia'
LOGO = Path('C:/Users/Yuxuan/Desktop/logo等/logo.png')


def base(number, name, title):
    p = AiaProject(number, name, title)
    p.assets['logo.png'] = LOGO
    return p


def intro(p, title, subtitle):
    return [p.label('TitleLabel', title, FontSize=26, FontBold='True', Height=58, TextAlignment=1),
            p.label('SubtitleLabel', subtitle, FontSize=15, TextColor='&HFF56758B', Height=-1, TextAlignment=1),
            p.label('TopSpace', '', Height=14)]


def build01():
    p = base(1, 'Course01Hello', '我的第一个手机 APP')
    p.screen([p.page(intro(p, '你好，手机 APP', '第 1 课｜一次点击，一次回应') + [
        p.label('GreetingLabel', '我准备好和你打招呼了！', FontSize=22, Height=130, TextAlignment=1, BackgroundColor='&HFFFFFFFF'),
        p.button('HelloButton', '和我打招呼'),
        p.button('ResetButton', '回到最初', BackgroundColor='&HFFDCEFFF', TextColor='&HFF123E62'),
        p.label('HintLabel', '先点问候按钮，再试试重置。你想让 APP 说什么？', FontSize=14, TextColor='&HFF56758B')])])
    p.tops = [p.event('HelloButton', 'Click', p.set('GreetingLabel', 'Text', p.text('你好！这是我做的第一个手机 APP。')),
                      '事件：问候按钮被点击。动作：把问候标签的文字改成自己的句子。'),
              p.event('ResetButton', 'Click', p.set('GreetingLabel', 'Text', p.text('我准备好和你打招呼了！')),
                      '重置按钮把文字恢复为设计界面的初始内容，可以重复体验。')]
    p.class_tops = [copy.deepcopy(p.tops[1])]
    return p, dict(work='点击问候应用', classroomKept=['ResetButton.Click'], classroomTasks=['添加 HelloButton.Click，将 GreetingLabel.Text 设为自己的问候语'],
        screenshotGroups=['HelloButton.Click', 'ResetButton.Click'], tests=[
            dict(event='HelloButton.Click', expect={'GreetingLabel.Text': '你好！这是我做的第一个手机 APP。'}),
            dict(event='ResetButton.Click', expect={'GreetingLabel.Text': '我准备好和你打招呼了！'})])


def build02():
    p = base(2, 'Course02Card', '会互动的数字名片')
    p.screen([p.page(intro(p, '林小羽的数字名片', '第 2 课｜同一个界面，可以展示不同的我') + [
        p.comp('AvatarImage', 'Image', Picture='logo.png', Width=130, Height=130, AlternateText='羽轩编程工作台标志示例头像', ScalePictureToFit='True'),
        p.label('NameLabel', '林小羽｜创意小队', FontSize=21, FontBold='True', Height=48),
        p.label('InfoLabel', '欢迎认识我！点击下面的按钮。', Height=125, FontSize=18, BackgroundColor='&HFFFFFFFF'),
        p.comp('TabsRow', 'HorizontalArrangement', [p.button('IntroButton', '我的介绍', Width=-1050), p.button('HobbyButton', '我的爱好', Width=-1050)], Width=-2, Height=58),
        p.button('ResetButton', '回到名片首页', BackgroundColor='&HFFDCEFFF', TextColor='&HFF123E62'),
        p.label('HintLabel', '示例姓名为虚构。改编时不必公开电话、住址或真实照片。', FontSize=13, TextColor='&HFF56758B')])])
    p.tops = [p.event('IntroButton', 'Click', p.chain(
        p.set('InfoLabel', 'Text', p.text('大家好，我是林小羽。我喜欢提出问题，也喜欢把想法做成作品。')),
        p.set('NameLabel', 'Text', p.text('林小羽｜关于我'))), '一次点击可以依次修改多个属性；组件名与屏幕文字不是同一回事。'),
        p.event('HobbyButton', 'Click', p.chain(
            p.set('InfoLabel', 'Text', p.text('我的爱好：画画、阅读和编程。我想做一个帮助同学的小工具。')),
            p.set('NameLabel', 'Text', p.text('林小羽｜我的爱好')))),
        p.event('ResetButton', 'Click', p.chain(
            p.set('InfoLabel', 'Text', p.text('欢迎认识我！点击下面的按钮。')),
            p.set('NameLabel', 'Text', p.text('林小羽｜创意小队'))))]
    p.class_tops = [copy.deepcopy(p.tops[0])]
    return p, dict(work='互动数字名片', classroomKept=['IntroButton.Click'], classroomTasks=['补齐 HobbyButton.Click，展示爱好并更新姓名标签', '补齐 ResetButton.Click，恢复两个标签的初始内容'],
        screenshotGroups=['IntroButton.Click', 'HobbyButton.Click', 'ResetButton.Click'], tests=[
            dict(event='IntroButton.Click', expect={'NameLabel.Text': '林小羽｜关于我'}),
            dict(event='HobbyButton.Click', expect={'NameLabel.Text': '林小羽｜我的爱好', 'InfoLabel.Text': '我的爱好：画画、阅读和编程。我想做一个帮助同学的小工具。'}),
            dict(event='ResetButton.Click', expect={'InfoLabel.Text': '欢迎认识我！点击下面的按钮。', 'NameLabel.Text': '林小羽｜创意小队'})])


def tone_wav():
    """Original 0.16-second two-note UI chime; explicitly not an animal recording."""
    sample_rate = 22050
    samples = []
    for i in range(int(sample_rate * .16)):
        t = i / sample_rate
        freq = 660 if t < .08 else 880
        local = t % .08
        envelope = min(local / .005, 1) * max(0, 1 - local / .08)
        samples.append(struct.pack('<h', int(7000 * envelope * math.sin(2 * math.pi * freq * t))))
    output = io.BytesIO()
    with wave.open(output, 'wb') as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sample_rate)
        w.writeframes(b''.join(samples))
    return output.getvalue()


def build03():
    p = base(3, 'Course03Voice', '会发声的伙伴')
    p.assets['feedback.wav'] = tone_wav()
    p.screen([p.page(intro(p, '会发声的伙伴', '第 3 课｜让按钮带来听得见的回应') + [
        p.label('PetLabel', '小猫和小狗来做客', FontSize=22, FontBold='True', Height=65, TextAlignment=1),
        p.label('StatusLabel', '点击一种伙伴，听听它的自我介绍。', Height=130, FontSize=19, BackgroundColor='&HFFFFFFFF'),
        p.comp('PetButtons', 'HorizontalArrangement', [p.button('CatButton', '小猫', Width=-1050), p.button('DogButton', '小狗', Width=-1050)], Width=-2, Height=58),
        p.button('StopButton', '停止声音', BackgroundColor='&HFFDCEFFF', TextColor='&HFF123E62'),
        p.label('HintLabel', '短音是原创操作提示音；伙伴介绍由手机的文字转语音引擎朗读，需要已安装中文语音。', FontSize=14, TextColor='&HFF56758B')]),
        p.comp('PetSpeech', 'TextToSpeech', Language='zh', Country='CHN', Pitch=1, SpeechRate=.9),
        p.comp('FeedbackSound', 'Sound', Source='feedback.wav', MinimumInterval=200)])
    p.tops = [p.event('CatButton', 'Click', p.chain(
        p.method('PetSpeech', 'Stop'), p.set('StatusLabel', 'Text', p.text('小猫：我是小猫，喵喵喵。')),
        p.method('FeedbackSound', 'Play'), p.method('PetSpeech', 'Speak', p.text('我是小猫，喵喵喵'))),
        'Play 播放打包在工程里的短提示音；Speak 交给手机本地语音引擎。两种声音来源不同。'),
        p.event('DogButton', 'Click', p.chain(
            p.method('PetSpeech', 'Stop'), p.set('StatusLabel', 'Text', p.text('小狗：我是小狗，汪汪汪。')),
            p.method('FeedbackSound', 'Play'), p.method('PetSpeech', 'Speak', p.text('我是小狗，汪汪汪')))),
        p.event('StopButton', 'Click', p.chain(
            p.method('PetSpeech', 'Stop'), p.method('FeedbackSound', 'Stop'),
            p.set('StatusLabel', 'Text', p.text('声音已停止，再选一个伙伴吧。'))))]
    p.class_tops = [copy.deepcopy(p.tops[0])]
    return p, dict(work='动物语音伙伴', classroomKept=['CatButton.Click'], classroomTasks=['参照小猫事件完成 DogButton.Click', '完成 StopButton.Click，同时停止语音和短音并更新状态文字'],
        screenshotGroups=['CatButton.Click', 'DogButton.Click', 'StopButton.Click'], limitations=['TTS 输出取决于手机已安装的中文语音引擎，不把合成提示音称为真实动物叫声', '桌面静态与编译验证不等于安卓音频播放实测'], tests=[
            dict(event='CatButton.Click', expect={'StatusLabel.Text': '小猫：我是小猫，喵喵喵。'}, methods=['PetSpeech.Stop', 'FeedbackSound.Play', 'PetSpeech.Speak:我是小猫，喵喵喵']),
            dict(event='DogButton.Click', expect={'StatusLabel.Text': '小狗：我是小狗，汪汪汪。'}, methods=['PetSpeech.Stop', 'FeedbackSound.Play', 'PetSpeech.Speak:我是小狗，汪汪汪']),
            dict(event='StopButton.Click', expect={'StatusLabel.Text': '声音已停止，再选一个伙伴吧。'}, methods=['PetSpeech.Stop', 'FeedbackSound.Stop'])])


def scene_switch(p, target):
    return p.chain(*[p.set(scene, 'Visible', p.boolean(scene == target)) for scene in ['BeachScene', 'CleanupScene', 'RescueScene']])


def build04():
    p = base(4, 'Course04Story', '我的故事小舞台')
    for asset in ['scene_beach.png', 'scene_cleanup.png', 'scene_turtle.png']:
        p.assets[asset] = ROOT / 'work/course56/assets' / asset
    beach = p.comp('BeachScene', 'VerticalArrangement', [
        p.label('BeachTitle', '第一幕：海滩上的发现', FontSize=22, FontBold='True', Height=65),
        p.comp('BeachImage', 'Image', Picture='scene_beach.png', Width=-2, Height=180, AlternateText='海滩上发现塑料垃圾与需要帮助的小海龟', ScalePictureToFit='True'),
        p.label('BeachText', '你来到海边。沙滩上有塑料瓶，不远处还有一只被线缠住的小海龟。你想先做什么？', FontSize=19, Height=170),
        p.button('CleanButton', '先清理沙滩'), p.button('RescueButton', '先联系救助人员')
    ], Width=-2, Height=-1, Visible='True', BackgroundColor='&HFFEAF7FF')
    cleanup = p.comp('CleanupScene', 'VerticalArrangement', [
        p.label('CleanupTitle', '第二幕：一片干净的海滩', FontSize=22, FontBold='True', Height=65),
        p.comp('CleanupImage', 'Image', Picture='scene_cleanup.png', Width=-2, Height=180, AlternateText='同伴合作清理海滩垃圾', ScalePictureToFit='True'),
        p.label('CleanupText', '你戴好手套，把塑料瓶放入合适的回收箱。越来越多的伙伴加入了清理行动。海滩变干净了！', FontSize=19, Height=180),
        p.button('CleanupRestartButton', '回到发现的那一刻')
    ], Width=-2, Height=-1, Visible='False', BackgroundColor='&HFFF3FAF0')
    rescue = p.comp('RescueScene', 'VerticalArrangement', [
        p.label('RescueTitle', '第三幕：海龟得到帮助', FontSize=22, FontBold='True', Height=65),
        p.comp('RescueImage', 'Image', Picture='scene_turtle.png', Width=-2, Height=180, AlternateText='小海龟在专业帮助下安全回到海边', ScalePictureToFit='True'),
        p.label('RescueText', '你请大人联系专业救助人员，在安全距离外等待。海龟得到帮助，你也学会了遇到野生动物时先寻求专业支持。', FontSize=19, Height=180),
        p.button('RescueRestartButton', '再体验另一条故事路线')
    ], Width=-2, Height=-1, Visible='False', BackgroundColor='&HFFF1F1FF')
    p.screen([p.page(intro(p, '海岛环保小故事', '第 4 课｜按钮决定接下来展示哪一幕') + [beach, cleanup, rescue,
        p.label('HintLabel', '三个场景在同一屏幕中。每次只显示其中一个。', FontSize=14, TextColor='&HFF56758B')])])
    p.tops = [p.event('CleanButton', 'Click', scene_switch(p, 'CleanupScene'), '三个 Visible 要一起设置，避免多个场景叠在同一个页面。'),
              p.event('RescueButton', 'Click', scene_switch(p, 'RescueScene')),
              p.event('CleanupRestartButton', 'Click', scene_switch(p, 'BeachScene')),
              p.event('RescueRestartButton', 'Click', scene_switch(p, 'BeachScene'))]
    p.class_tops = [copy.deepcopy(p.tops[0])]
    return p, dict(work='海岛环保三场景故事', classroomKept=['CleanButton.Click'], classroomTasks=['完成 RescueButton.Click，显示 RescueScene 并隐藏其余场景', '完成两个 Restart 按钮事件，回到 BeachScene'],
        screenshotGroups=['CleanButton.Click', 'RescueButton.Click', 'CleanupRestartButton.Click', 'RescueRestartButton.Click'], tests=[
            dict(event='CleanButton.Click', expect={'BeachScene.Visible': False, 'CleanupScene.Visible': True, 'RescueScene.Visible': False}),
            dict(event='CleanupRestartButton.Click', expect={'BeachScene.Visible': True, 'CleanupScene.Visible': False, 'RescueScene.Visible': False}),
            dict(event='RescueButton.Click', expect={'BeachScene.Visible': False, 'CleanupScene.Visible': False, 'RescueScene.Visible': True}),
            dict(event='RescueRestartButton.Click', expect={'BeachScene.Visible': True, 'CleanupScene.Visible': False, 'RescueScene.Visible': False})])


def build05():
    p = base(5, 'Course05Festival', '给 APP 设计漂亮的界面')
    p.screen([p.page(intro(p, '校园创意节', '第 5 课｜清楚的布局，让信息更好找') + [
        p.comp('HeroRow', 'HorizontalArrangement', [
            p.comp('FestivalImage', 'Image', Picture='logo.png', Width=84, Height=84, ScalePictureToFit='True', AlternateText='羽轩创意编程标志'),
            p.label('FestivalTagline', '把一个想法\n做成看得见的作品', Width=-2, FontSize=20, FontBold='True')
        ], Width=-2, Height=98, AlignVertical=2),
        p.comp('MenuRow', 'HorizontalArrangement', [
            p.button('TimeButton', '时间', Width=-1033), p.button('PlaceButton', '地点', Width=-1033), p.button('SignupButton', '报名', Width=-1034)
        ], Width=-2, Height=58),
        p.comp('InfoCard', 'VerticalArrangement', [
            p.label('InfoTitle', '欢迎参加创意节', FontSize=22, FontBold='True', Height=52),
            p.label('InfoLabel', '展示游戏、故事和生活小工具。点击上方的分类，查看活动信息。', FontSize=18, Height=150)
        ], Width=-2, Height=-1, BackgroundColor='&HFFFFFFFF'),
        p.button('ResetButton', '活动首页', BackgroundColor='&HFFDCEFFF', TextColor='&HFF123E62'),
        p.label('HintLabel', '课堂虚构活动。报名按钮只展示说明，不联网、不收集个人信息。', FontSize=13, TextColor='&HFF56758B')])])
    info = [
        ('TimeButton', '活动时间', '示例时间：周五 15:00—16:30。\n先到展示区集合，再参加同伴体验。'),
        ('PlaceButton', '活动地点', '示例地点：学校创意教室。\n从教学楼一层入口进入，按现场指引到作品展示区。'),
        ('SignupButton', '报名方式', '课堂演示：向老师说明作品名称与展示方式。\n此按钮仅显示报名说明，不会提交任何资料。'),
        ('ResetButton', '欢迎参加创意节', '展示游戏、故事和生活小工具。点击上方的分类，查看活动信息。')]
    p.tops = [p.event(c, 'Click', p.chain(p.set('InfoTitle', 'Text', p.text(title)), p.set('InfoLabel', 'Text', p.text(body))),
                      '按钮等宽排在水平布局中；信息区域占满可用宽度。' if c == 'TimeButton' else None) for c, title, body in info]
    p.class_tops = [copy.deepcopy(p.tops[0])]
    return p, dict(work='校园创意节信息页', classroomKept=['TimeButton.Click'], classroomTasks=['补齐 PlaceButton.Click 与 SignupButton.Click', '补齐 ResetButton.Click 并检查标题、正文、提示的层级'],
        screenshotGroups=[c + '.Click' for c, _, _ in info], tests=[dict(event=c+'.Click', expect={'InfoTitle.Text': title, 'InfoLabel.Text': body}) for c,title,body in info],
        layoutNotes=['Screen1.Scrollable=True 防止小屏底部内容不可见', 'Page 与 InfoCard 宽度填充父组件', 'MenuRow 三按钮宽度分别为 33%、33%、34%'])


def build06():
    p = base(6, 'Course06Clubs', '第一次创意改编')
    p.screen([p.page(intro(p, '我的校园兴趣指南', '第 6 课｜保留交互方法，换成自己的创意主题') + [
        p.label('QuestionLabel', '今天，你想尝试什么？', FontSize=22, FontBold='True', Height=65),
        p.comp('ChoicesRow', 'HorizontalArrangement', [
            p.button('SportsButton', '运动', Width=-1033), p.button('ArtButton', '艺术', Width=-1033), p.button('CodeButton', '编程', Width=-1034)
        ], Width=-2, Height=58),
        p.label('RecommendationLabel', '选择一个方向，看看参考建议。', FontSize=22, FontBold='True', Height=95, BackgroundColor='&HFFFFFFFF'),
        p.label('ReasonLabel', '这是根据你点击的选项显示的固定建议。你可以修改文案，加入自己的校园活动。', FontSize=18, Height=155, BackgroundColor='&HFFFFFFFF'),
        p.button('ResetButton', '重新选择', BackgroundColor='&HFFDCEFFF', TextColor='&HFF123E62'),
        p.label('HintLabel', '参考作品不做兴趣测评，也不自动推断个人能力。改编时说明你保留了什么、改变了什么。', FontSize=13, TextColor='&HFF56758B')])])
    info = [
        ('SportsButton', '试试运动挑战站', '和同伴练习跳绳或投球。先确认场地安全，按老师的安排热身。'),
        ('ArtButton', '试试创意美术角', '用纸笔设计一张作品海报。选择两种主色，把最重要的信息放大。'),
        ('CodeButton', '试试创意编程社', '把一句问候变成互动名片，再给作品添加声音或新的故事场景。'),
        ('ResetButton', '选择一个方向，看看参考建议。', '这是根据你点击的选项显示的固定建议。你可以修改文案，加入自己的校园活动。')]
    p.tops = [p.event(c, 'Click', p.chain(p.set('RecommendationLabel', 'Text', p.text(title)), p.set('ReasonLabel', 'Text', p.text(body))),
                      '从第 2 课的名片切换方法改编而来：改变主题和内容，保留“事件修改标签”的方法。' if c == 'SportsButton' else None) for c,title,body in info]
    p.class_tops = [copy.deepcopy(p.tops[0])]
    return p, dict(work='校园兴趣指南', classroomKept=['SportsButton.Click'], classroomTasks=['完成 ArtButton.Click 与 CodeButton.Click', '完成 ResetButton.Click；自选一种兴趣改写推荐内容'],
        screenshotGroups=[c + '.Click' for c,_,_ in info], tests=[dict(event=c+'.Click', expect={'RecommendationLabel.Text': title, 'ReasonLabel.Text': body}) for c,title,body in info])


def emit(number):
    project, detail = globals()[f'build{number:02d}']()
    folder = OUT / f'lesson{number:02d}'
    versions = project.write(folder)
    (folder/'blocks.xml').write_bytes(project.xml('answer'))
    assetdir=folder/'assets'
    assetdir.mkdir(exist_ok=True)
    for name, data in project.assets.items():
        (assetdir/name).write_bytes(data.read_bytes() if isinstance(data,Path) else data)
    components = []
    for name, c in project.components.items():
        components.append(dict(name=name, type=c['$Type'], version=c['$Version'], properties={k:v for k,v in c.items() if not k.startswith('$') and k!='Uuid'}))
    spec = dict(lesson=number, title=project.title, projectName=project.name, versions=versions, components=components,
                variants=dict(answer='完整参考答案；所有交互事件均已实现', classroom='课堂支架；保留一个完整示范事件，其他目标事件由学生补齐',
                              starter='纯界面起始版；组件、属性和素材与答案一致，积木为空'),
                assets=[dict(file=name,source='用户提供的羽轩品牌 logo，课堂本地示例复用' if name=='logo.png' else 'Python 标准库生成的原创 660/880 Hz 短提示音；不是动物录音' if name.endswith('.wav') else '本课程生成的原创故事插画，提示词见 work/course56/assets-source.json') for name in project.assets],
                staticValidation=dict(componentReferences='pass', designerProperties='pass: distribution metadata', eventMethods='pass: distribution metadata',
                                      valueSockets='pass', assetReferences='pass'),
                nativeImportValidation='pending', apkCompilation='pending', androidDeviceTest='not requested', **detail)
    (folder/'artifact-spec.json').write_text(json.dumps(spec,ensure_ascii=False,indent=2),encoding='utf8')
    print(json.dumps(dict(lesson=number,project=project.name,versions=[dict(kind=v['kind'],blocks=v['blockCount']) for v in versions],spec=str(folder/'artifact-spec.json')),ensure_ascii=False))


if __name__ == '__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('lessons', nargs='*', type=int, default=list(range(1,7)))
    args=parser.parse_args()
    for n in args.lessons:
        if not 1<=n<=6: parser.error('This authoring batch covers lessons 1–6')
        emit(n)
