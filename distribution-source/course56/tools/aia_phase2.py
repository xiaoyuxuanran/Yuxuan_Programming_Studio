"""Author the eight programming-thinking projects, lessons 7–14.

Every classroom variant has connected, type-correct blocks.  Lesson 14 alone
deliberately contains the three documented logic defects for a debugging task.
"""
from pathlib import Path
import argparse
import copy
import json

from aia_core import ROOT, AiaProject
from aia_phase1 import base, intro

OUT = ROOT / 'work/course56/aia'
BLUEPRINTS = ROOT / 'work/course56/blueprints'


def box(p, name, hint, **props):
    options = dict(Text='', Hint=hint, Width=-2, Height=55, FontSize=19,
                   NumbersOnly='True', BackgroundColor='&HFFFFFFFF', TextColor='&HFF123E62')
    options.update(props)
    return p.comp(name, 'TextBox', **options)


def neq(p, a, b):
    return p.b('logic_compare', {'OP': 'NEQ'}, {'A': a, 'B': b})


def integer(p, value):
    duplicate = copy.deepcopy(value)
    for node in duplicate.iter('block'):
        node.set('id', f'c{p.lesson:02d}-{next(p._block_ids):05d}')
    return p.cmp('EQ', duplicate, p.floor(value))


def numeric_text(p, component):
    return p.trim(p.get(component, 'Text'))


def build07():
    p = base(7, 'YXCourse07', '会记数的 APP')
    p.screen([p.page(intro(p, '合作积分器', '第 7 课｜一次操作改变一份数据') + [
        p.label('ScoreLabel', '得分：0', FontSize=36, FontBold='True', Height=145, TextAlignment=1, BackgroundColor='&HFFFFFFFF'),
        p.comp('ScoreButtons', 'HorizontalArrangement', [p.button('AddButton', '完成挑战 +1', Width=-1050), p.button('MinusButton', '撤销一次 −1', Width=-1050)], Width=-2, Height=58),
        p.button('ResetButton', '归零，开始新一轮', BackgroundColor='&HFFDCEFFF', TextColor='&HFF123E62'),
        p.label('HintLabel', '得分会累计，最低为 0。关闭应用后不保留本轮积分。', FontSize=14, TextColor='&HFF56758B')])])
    p.tops = [p.global_('得分', p.num(0)),
        p.define('刷新得分', p.set('ScoreLabel', 'Text', p.join(p.text('得分：'), p.var('得分')))),
        p.event('AddButton', 'Click', p.chain(p.setvar('得分', p.add(p.var('得分'), p.num(1))), p.call('刷新得分')), '先读取旧得分，计算加 1，再写回同一个变量。'),
        p.event('MinusButton', 'Click', p.chain(p.setvar('得分', p.mm('MAX', p.num(0), p.sub(p.var('得分'), p.num(1)))), p.call('刷新得分'))),
        p.event('ResetButton', 'Click', p.chain(p.setvar('得分', p.num(0)), p.call('刷新得分')))]
    p.class_tops = copy.deepcopy(p.tops[:2]) + [p.event('AddButton', 'Click', p.call('刷新得分'), '课堂任务：在刷新之前加入得分←得分+1。')]
    return p, dict(work='合作积分器', classroomKept=['global 得分', '刷新得分', 'AddButton.Click 的刷新调用'], classroomTasks=['在 AddButton.Click 的刷新前加入累计赋值', '添加 MinusButton.Click，限制最低 0 分', '添加 ResetButton.Click，同时清变量和显示'],
        screenshotGroups=['AddButton.Click', '刷新得分', 'MinusButton.Click'], tests=[
            dict(events=['AddButton.Click']*3, expect={'global 得分':3,'ScoreLabel.Text':'得分：3'}),
            dict(events=['MinusButton.Click']*2, expect={'global 得分':0,'ScoreLabel.Text':'得分：0'}),
            dict(events=['AddButton.Click']*5+['ResetButton.Click','AddButton.Click'], expect={'global 得分':1})])


def build08():
    p = base(8, 'YXCourse08', '随身计算小工具')
    p.screen([p.page(intro(p, '厘米与米换算器', '第 8 课｜先检查输入，再按单位换算') + [
        p.label('InputLabel', '输入长度数值（非负数）', Height=42), box(p, 'InputBox', '例如：125 或 1.25'),
        p.comp('ConvertRow', 'HorizontalArrangement', [p.button('ToMeterButton', '厘米 → 米', Width=-1050), p.button('ToCmButton', '米 → 厘米', Width=-1050)], Width=-2, Height=58),
        p.label('ResultLabel', '等待输入', FontSize=24, FontBold='True', Height=130, BackgroundColor='&HFFFFFFFF'),
        p.button('ClearButton', '清空', BackgroundColor='&HFFDCEFFF', TextColor='&HFF123E62'),
        p.label('HintLabel', '1 米 = 100 厘米。输入框只写数字，单位由按钮决定。', FontSize=14, TextColor='&HFF56758B')])])
    result = p.set('ResultLabel', 'Text', p.join(p.mul(p.var('输入值'), p.param('倍率')), p.param('单位')))
    convert = p.iff(p.isnum(numeric_text(p,'InputBox')), p.chain(
        p.setvar('输入值', p.add(numeric_text(p,'InputBox'),p.num(0))),
        p.iff(p.cmp('GTE',p.var('输入值'),p.num(0)), result, p.set('ResultLabel','Text',p.text('请输入非负数')))),
        p.set('ResultLabel','Text',p.text('请输入数字')))
    p.tops = [p.global_('输入值',p.num(0)), p.define('换算',convert,args=('倍率','单位')),
        p.event('ToMeterButton','Click',p.call('换算',p.num(.01),p.text('米'),names=('倍率','单位'))),
        p.event('ToCmButton','Click',p.call('换算',p.num(100),p.text('厘米'),names=('倍率','单位'))),
        p.event('ClearButton','Click',p.chain(p.set('InputBox','Text',p.text('')),p.setvar('输入值',p.num(0)),p.set('ResultLabel','Text',p.text('等待输入'))))]
    p.class_tops = copy.deepcopy(p.tops[:3])
    return p, dict(work='厘米与米换算器', classroomKept=['global 输入值','换算(倍率,单位)：完整输入检查与计算过程','ToMeterButton.Click'],classroomTasks=['参照厘米转米补齐 ToCmButton.Click，倍率为100、单位为厘米','添加 ClearButton.Click，同时清输入、变量与结果'],
        screenshotGroups=['ToMeterButton.Click','换算','ToCmButton.Click'],tests=[
            dict(set={'InputBox.Text':'125'},event='ToMeterButton.Click',expect={'ResultLabel.Text':'1.25米'}),
            dict(set={'InputBox.Text':'1.25'},event='ToCmButton.Click',expect={'ResultLabel.Text':'125厘米'}),
            dict(set={'InputBox.Text':'  '},event='ToMeterButton.Click',expect={'ResultLabel.Text':'请输入数字'}),
            dict(set={'InputBox.Text':'abc'},event='ToMeterButton.Click',expect={'ResultLabel.Text':'请输入数字'}),
            dict(set={'InputBox.Text':'-1'},event='ToMeterButton.Click',expect={'ResultLabel.Text':'请输入非负数'}),
            dict(event='ClearButton.Click',expect={'InputBox.Text':'','ResultLabel.Text':'等待输入'})])


def build09():
    p = base(9, 'YXCourse09', '让 APP 学会判断')
    p.screen([p.page(intro(p,'阅读目标小助手','第 9 课｜20 分钟，恰好达标算不算？')+[
        p.label('GoalLabel','今天的目标：阅读 20 分钟',FontSize=23,FontBold='True',Height=70),
        box(p,'MinutesBox','你今天读了多少分钟？'),p.button('CheckButton','检查阅读进度'),
        p.label('ResultLabel','输入非负分钟数，再点击检查。',FontSize=22,Height=145,BackgroundColor='&HFFFFFFFF'),
        p.button('ResetButton','重新填写',BackgroundColor='&HFFDCEFFF',TextColor='&HFF123E62'),
        p.label('HintLabel','输入变化时不会自动提交；20 分钟属于达标分支。',FontSize=14,TextColor='&HFF56758B')])])
    def check(op='GTE', include_shortfall=True):
        normal = p.iff(p.cmp(op,numeric_text(p,'MinutesBox'),p.var('目标')),
                       p.set('ResultLabel','Text',p.text('达标！今天的阅读目标完成了。')),
                       p.set('ResultLabel','Text',p.join(p.text('还差'),p.sub(p.var('目标'),numeric_text(p,'MinutesBox')),p.text('分钟。'))) if include_shortfall else p.set('ResultLabel','Text',p.text('未达标，请补齐剩余分钟数提示。')))
        return p.iff(p.isnum(numeric_text(p,'MinutesBox')),
            p.iff(p.cmp('GTE',numeric_text(p,'MinutesBox'),p.num(0)),normal,p.set('ResultLabel','Text',p.text('请输入非负分钟数'))),
            p.set('ResultLabel','Text',p.text('请输入非负分钟数')))
    p.tops=[p.global_('目标',p.num(20)),p.define('检查时长',check()),
        p.event('CheckButton','Click',p.call('检查时长')),
        p.event('ResetButton','Click',p.chain(p.set('MinutesBox','Text',p.text('')),p.set('ResultLabel','Text',p.text('输入非负分钟数，再点击检查。'))))]
    p.class_tops=[copy.deepcopy(p.tops[0]),p.note(p.define('检查时长',check('GT',False)),'课堂任务：比较改为≥；未达标分支应显示目标减输入得到的差值。'),copy.deepcopy(p.tops[2])]
    return p,dict(work='阅读目标判断器',classroomKept=['global 目标','检查时长：合法性检查和待修的>比较','CheckButton.Click'],classroomTasks=['将>改为≥，使20分钟达标','补齐未达标分支的差值显示','添加 ResetButton.Click'],
        screenshotGroups=['CheckButton.Click','检查时长','ResetButton.Click'],tests=[
            dict(set={'MinutesBox.Text':'19'},event='CheckButton.Click',expect={'ResultLabel.Text':'还差1分钟。'}),
            dict(set={'MinutesBox.Text':'20'},event='CheckButton.Click',expect={'ResultLabel.Text':'达标！今天的阅读目标完成了。'}),
            dict(set={'MinutesBox.Text':'21'},event='CheckButton.Click',expect={'ResultLabel.Text':'达标！今天的阅读目标完成了。'}),
            dict(set={'MinutesBox.Text':'8'},event='CheckButton.Click',expect={'ResultLabel.Text':'还差12分钟。'}),
            dict(set={'MinutesBox.Text':'-1'},event='CheckButton.Click',expect={'ResultLabel.Text':'请输入非负分钟数'}),
            dict(set={'MinutesBox.Text':''},event='CheckButton.Click',expect={'ResultLabel.Text':'请输入非负分钟数'})])


def build10():
    p=base(10,'YXCourse10','随机数与猜数字')
    p.screen([p.page(intro(p,'猜猜秘密数字','第 10 课｜答案在 1 到 20 之间')+[
        p.label('RangeLabel','我想好了一个 1～20 的整数。',FontSize=21,FontBold='True',Height=65),
        box(p,'GuessBox','输入你的猜测'),p.button('GuessButton','提交猜测'),
        p.label('HintLabel','点击“换一局”开始新游戏。',FontSize=22,Height=130,BackgroundColor='&HFFFFFFFF'),
        p.label('AttemptsLabel','尝试次数：0',FontSize=19,Height=50),
        p.button('NewButton','换一局',BackgroundColor='&HFFDCEFFF',TextColor='&HFF123E62')])])
    valid = p.both(integer(p,numeric_text(p,'GuessBox')),p.both(p.cmp('GTE',numeric_text(p,'GuessBox'),p.num(1)),p.cmp('LTE',numeric_text(p,'GuessBox'),p.num(20))))
    outcome=p.iff(p.cmp('LT',numeric_text(p,'GuessBox'),p.var('答案')),p.set('HintLabel','Text',p.text('偏小，再试一次！')),
        p.iff(p.cmp('GT',numeric_text(p,'GuessBox'),p.var('答案')),p.set('HintLabel','Text',p.text('偏大，再试一次！')),
              p.chain(p.set('HintLabel','Text',p.text('猜中了！点击“换一局”再挑战。')),p.setvar('已结束',p.boolean(True)))))
    validation=lambda body:p.iff(p.eq(p.var('已结束'),p.boolean(False)),p.iff(p.isnum(numeric_text(p,'GuessBox')),p.iff(copy.deepcopy(valid),body,p.set('HintLabel','Text',p.text('请输入1～20的整数'))),p.set('HintLabel','Text',p.text('请输入1～20的整数'))))
    p.tops=[p.global_('答案',p.num(1)),p.global_('次数',p.num(0)),p.global_('已结束',p.boolean(False)),
        p.define('新一局',p.chain(p.setvar('答案',p.random(p.num(1),p.num(20))),p.setvar('次数',p.num(0)),p.setvar('已结束',p.boolean(False)),p.set('GuessBox','Text',p.text('')),p.set('HintLabel','Text',p.text('我想好了，开始猜吧！')),p.set('AttemptsLabel','Text',p.text('尝试次数：0')))),
        p.define('检查猜测',validation(p.chain(p.setvar('次数',p.add(p.var('次数'),p.num(1))),p.set('AttemptsLabel','Text',p.join(p.text('尝试次数：'),p.var('次数'))),outcome))),
        p.event('Screen1','Initialize',p.call('新一局')),p.event('GuessButton','Click',p.call('检查猜测')),p.event('NewButton','Click',p.call('新一局'))]
    p.class_tops=copy.deepcopy(p.tops[:4])+[p.note(p.define('检查猜测',validation(p.set('HintLabel','Text',p.text('输入有效，请补齐计次与三路比较。')))),'有效输入分支：先累计次数，再比较猜测与答案。猜中后设已结束为true。')]+copy.deepcopy(p.tops[5:])
    return p,dict(work='1～20猜数字游戏',classroomKept=['全部变量','新一局','检查猜测：输入检查和结束状态保护','三个入口事件'],classroomTasks=['在有效分支累计次数并刷新显示','完成偏小、偏大、猜中三个分支','猜中时设置已结束=True，保留后续提交保护'],
        screenshotGroups=['新一局','检查猜测','NewButton.Click'],tests=[
            dict(set={'global 答案':12,'GuessBox.Text':'8'},event='GuessButton.Click',expect={'global 次数':1,'HintLabel.Text':'偏小，再试一次！'}),
            dict(set={'global 答案':12,'GuessBox.Text':'16'},event='GuessButton.Click',expect={'HintLabel.Text':'偏大，再试一次！'}),
            dict(set={'global 答案':12,'GuessBox.Text':'12'},event='GuessButton.Click',expect={'global 已结束':True,'HintLabel.Text':'猜中了！点击“换一局”再挑战。'}),
            dict(set={'GuessBox.Text':'2.5'},event='GuessButton.Click',expect={'global 次数':0,'HintLabel.Text':'请输入1～20的整数'}),
            dict(set={'global 已结束':True,'global 次数':3,'HintLabel.Text':'保持结果','GuessBox.Text':'1'},event='GuessButton.Click',expect={'global 次数':3,'HintLabel.Text':'保持结果'}),
            dict(event='NewButton.Click',expect={'global 次数':0,'global 已结束':False,'GuessBox.Text':''})],limitations=['自动逻辑测试可暂设答案为12；交付答案版始终使用1～20随机整数'])


def build11():
    p=base(11,'YXCourse11','重复任务交给程序')
    p.screen([p.page(intro(p,'我的乘法表','第 11 课｜一个循环生成九行算式')+[
        box(p,'RowBox','输入1～9的整数，例如3'),p.button('GenerateButton','生成这一行乘法表'),
        p.label('OutputLabel','输入一个数，再点击生成。',FontSize=21,Height=285,BackgroundColor='&HFFFFFFFF'),
        p.label('SumLabel','九个乘积的总和：0',FontSize=20,FontBold='True',Height=70),
        p.label('HintLabel','重复生成会替换上一次结果，不会继续追加。',FontSize=14,TextColor='&HFF56758B')])])
    product=lambda:p.mul(p.param('行'),p.param('i'))
    loopbody=p.chain(p.setvar('输出',p.join(p.var('输出'),p.param('行'),p.text(' × '),p.param('i'),p.text(' = '),product(),p.text('\n'))),p.setvar('总和',p.add(p.var('总和'),product())))
    def generate(body):
        return p.chain(p.setvar('输出',p.text('')),p.setvar('总和',p.num(0)),p.forrange('i',p.num(1),p.num(9),p.num(1),body),p.set('OutputLabel','Text',p.var('输出')),p.set('SumLabel','Text',p.join(p.text('九个乘积的总和：'),p.var('总和'))))
    valid=p.both(integer(p,numeric_text(p,'RowBox')),p.both(p.cmp('GTE',numeric_text(p,'RowBox'),p.num(1)),p.cmp('LTE',numeric_text(p,'RowBox'),p.num(9))))
    error=lambda:p.set('OutputLabel','Text',p.text('请输入1～9的整数'))
    p.tops=[p.global_('输出',p.text('')),p.global_('总和',p.num(0)),p.define('生成乘法行',generate(loopbody),args=('行',)),
        p.event('GenerateButton','Click',p.iff(p.isnum(numeric_text(p,'RowBox')),p.iff(valid,p.call('生成乘法行',p.add(numeric_text(p,'RowBox'),p.num(0)),names=('行',)),error()),error()))]
    p.class_tops=copy.deepcopy(p.tops[:2])+[p.note(p.define('生成乘法行',generate(p.setvar('输出',p.var('输出'))),args=('行',)),'循环体占位：加入算式与换行追加，以及总和累计。保留循环前的两项清零。')]+copy.deepcopy(p.tops[3:])
    return p,dict(work='乘法表与乘积总和',classroomKept=['global 输出、总和','生成乘法行：清零、1～9循环框架和结果显示','GenerateButton.Click：合法性检查'],classroomTasks=['把循环体的自赋值占位改成追加行×i=乘积与换行','在循环体累计总和','保留循环前清零，验证重复生成不叠加'],
        screenshotGroups=['GenerateButton.Click','生成乘法行','生成乘法行'],tests=[
            dict(set={'RowBox.Text':'3'},event='GenerateButton.Click',expect={'global 总和':135,'SumLabel.Text':'九个乘积的总和：135'},contains={'OutputLabel.Text':['3 × 1 = 3','3 × 9 = 27']}),
            dict(set={'RowBox.Text':'3'},events=['GenerateButton.Click']*2,expect={'global 总和':135},lineCount={'OutputLabel.Text':9}),
            dict(set={'RowBox.Text':'0'},event='GenerateButton.Click',expect={'OutputLabel.Text':'请输入1～9的整数'}),
            dict(set={'RowBox.Text':'2.5'},event='GenerateButton.Click',expect={'OutputLabel.Text':'请输入1～9的整数'})])


def build12():
    p=base(12,'YXCourse12','和时间做游戏')
    p.screen([p.page(intro(p,'反应速度挑战','第 12 课｜等按钮变蓝绿色，再点！')+[
        p.label('RuleLabel','先点开始。等待时别抢跑，变色后立即点击下方按钮。',FontSize=20,Height=110),
        p.button('StartButton','开始新一轮'),p.button('ReactButton','等待开始',Height=125,FontSize=28,BackgroundColor='&HFF64748B'),
        p.label('ResultLabel','准备好了就开始。',FontSize=23,Height=150,BackgroundColor='&HFFFFFFFF'),
        p.label('HintLabel','结果是手机事件之间的毫秒差，受屏幕刷新与触摸延迟影响，不是专业测试仪。',FontSize=14,TextColor='&HFF56758B')]),
        p.comp('Clock1','Clock',TimerInterval=20,TimerEnabled='False',TimerAlwaysFires='False')])
    ready=p.chain(p.setvar('状态',p.text('准备')),p.set('Clock1','TimerEnabled',p.boolean(False)),p.set('ReactButton','BackgroundColor',p.num(-10185016)),p.set('ReactButton','Text',p.text('等待开始')))
    waiting=p.chain(p.setvar('状态',p.text('等待')),p.setvar('截止时刻',p.add(p.method('Clock1','SystemTime'),p.random(p.num(1000),p.num(3000)))),p.set('ReactButton','BackgroundColor',p.num(-10185016)),p.set('ReactButton','Text',p.text('等待变色…')),p.set('ResultLabel','Text',p.text('等待信号，提前点击算抢跑。')),p.set('Clock1','TimerEnabled',p.boolean(True)))
    timer=p.iff(p.both(p.eq(p.var('状态'),p.text('等待')),p.cmp('GTE',p.method('Clock1','SystemTime'),p.var('截止时刻'))),p.chain(
        p.setvar('状态',p.text('可点')),p.setvar('开始时刻',p.method('Clock1','SystemTime')),p.set('ReactButton','BackgroundColor',p.num(-16016174)),p.set('ReactButton','Text',p.text('现在点击！')),p.set('Clock1','TimerEnabled',p.boolean(False))))
    finish=lambda message:p.chain(p.set('Clock1','TimerEnabled',p.boolean(False)),p.setvar('状态',p.text('结束')),p.set('ResultLabel','Text',message),p.set('ReactButton','Text',p.text('本轮已结束')))
    react=p.iff(p.eq(p.var('状态'),p.text('等待')),finish(p.text('抢跑了！点击开始再试。')),
        p.iff(p.eq(p.var('状态'),p.text('可点')),finish(p.join(p.text('本次反应：'),p.sub(p.method('Clock1','SystemTime'),p.var('开始时刻')),p.text(' 毫秒'))),
            p.iff(p.eq(p.var('状态'),p.text('准备')),p.set('ResultLabel','Text',p.text('请先点击开始新一轮。')))))
    p.tops=[p.global_('状态',p.text('准备')),p.global_('开始时刻',p.num(0)),p.global_('截止时刻',p.num(0)),
        p.define('回到准备',ready),p.define('开始等待',waiting),p.event('Screen1','Initialize',p.call('回到准备')),
        p.event('StartButton','Click',p.call('开始等待')),p.event('Clock1','Timer',timer),p.event('ReactButton','Click',react)]
    p.class_tops=copy.deepcopy(p.tops[:7])
    return p,dict(work='毫秒反应挑战',classroomKept=['全部变量','回到准备','开始等待','Screen1.Initialize','StartButton.Click','Clock1 的20ms检查间隔'],classroomTasks=['添加 Clock1.Timer，截止后改变状态、记录开始时刻并停止计时器','添加 ReactButton.Click，区分等待抢跑和可点后的时间差','结束后再次点击保持结果，重新开始才进入等待'],
        screenshotGroups=['开始等待','Clock1.Timer','ReactButton.Click'],tests=[
            dict(set={'global 状态':'等待'},event='ReactButton.Click',expect={'global 状态':'结束','Clock1.TimerEnabled':False,'ResultLabel.Text':'抢跑了！点击开始再试。'}),
            dict(set={'global 状态':'可点','global 开始时刻':1000},systemTime=1500,event='ReactButton.Click',expect={'global 状态':'结束','ResultLabel.Text':'本次反应：500 毫秒'}),
            dict(set={'global 状态':'结束','ResultLabel.Text':'保持结果'},event='ReactButton.Click',expect={'ResultLabel.Text':'保持结果'}),
            dict(set={'global 状态':'等待','global 截止时刻':1200},systemTime=1200,event='Clock1.Timer',expect={'global 状态':'可点','global 开始时刻':1200,'Clock1.TimerEnabled':False})],limitations=['Clock 每20ms检查一次截止时刻，随机等待1～3秒；这不是20ms反应时分辨率保证','没有进行Android触摸或计时精度实测'])


def build13():
    p=base(13,'YXCourse13','把常用功能封装起来')
    p.screen([p.page(intro(p,'出行预算小助手','第 13 课｜参数送进过程，结果带回计算')+[
        p.label('PeopleLabel','参加人数（正整数）',Height=36),box(p,'PeopleBox','例如：3'),
        p.label('FeeLabel','每人交通费（元，非负数）',Height=36),box(p,'FeeBox','例如：12.5'),
        p.button('CalculateButton','计算总交通费'),p.label('ResultLabel','请输入人数与单价',FontSize=23,Height=125,BackgroundColor='&HFFFFFFFF'),
        p.button('ResetButton','重置',BackgroundColor='&HFFDCEFFF',TextColor='&HFF123E62')])])
    show=lambda message:p.call('提示',message,names=('内容',))
    calculate=p.iff(p.both(p.isnum(numeric_text(p,'PeopleBox')),p.isnum(numeric_text(p,'FeeBox'))),
        p.iff(p.both(integer(p,numeric_text(p,'PeopleBox')),p.cmp('GT',numeric_text(p,'PeopleBox'),p.num(0))),
            p.iff(p.cmp('GTE',numeric_text(p,'FeeBox'),p.num(0)),p.chain(
                p.setvar('总费用',p.call('总交通费',numeric_text(p,'PeopleBox'),numeric_text(p,'FeeBox'),names=('人数','单价'),returns=True)),
                show(p.join(p.text('总交通费'),p.var('总费用'),p.text('元')))),show(p.text('每人费用须为非负数'))),show(p.text('人数须为正整数'))),show(p.text('请输入有效的数字')))
    p.tops=[p.global_('总费用',p.num(0)),p.define('总交通费',p.mul(p.param('人数'),p.param('单价')),args=('人数','单价'),returns=True),
        p.define('提示',p.set('ResultLabel','Text',p.param('内容')),args=('内容',)),
        p.define('重置',p.chain(p.set('PeopleBox','Text',p.text('')),p.set('FeeBox','Text',p.text('')),p.setvar('总费用',p.num(0)),show(p.text('请输入人数与单价')))),
        p.event('CalculateButton','Click',calculate),p.event('ResetButton','Click',p.call('重置'))]
    p.class_tops=[copy.deepcopy(p.tops[0]),p.note(p.define('总交通费',p.num(0),args=('人数','单价'),returns=True),'课堂任务：把返回槽中的0替换成人数×单价。'),
        p.note(p.define('提示',p.set('ResultLabel','Text',p.text('课堂任务：使用内容参数')),args=('内容',)),'课堂任务：将固定文字替换为局部参数内容。')]+copy.deepcopy(p.tops[3:])
    return p,dict(work='带参数和返回值的出行预算器',classroomKept=['global 总费用','输入合法性检查','重置过程和两个按钮入口','总交通费与提示的过程框架及占位值'],classroomTasks=['提示过程使用参数内容代替固定文字','总交通费返回人数×单价，替换返回值0','观察CalculateButton如何接入返回值；ResetButton复用重置'],
        screenshotGroups=['提示','总交通费','ResetButton.Click'],tests=[
            dict(set={'PeopleBox.Text':'3','FeeBox.Text':'12.5'},event='CalculateButton.Click',expect={'global 总费用':37.5,'ResultLabel.Text':'总交通费37.5元'}),
            dict(set={'PeopleBox.Text':'1','FeeBox.Text':'0'},event='CalculateButton.Click',expect={'global 总费用':0,'ResultLabel.Text':'总交通费0元'}),
            dict(set={'PeopleBox.Text':'2.5','FeeBox.Text':'12'},event='CalculateButton.Click',expect={'ResultLabel.Text':'人数须为正整数'}),
            dict(set={'PeopleBox.Text':'0','FeeBox.Text':'12'},event='CalculateButton.Click',expect={'ResultLabel.Text':'人数须为正整数'}),
            dict(event='ResetButton.Click',expect={'PeopleBox.Text':'','FeeBox.Text':'','global 总费用':0,'ResultLabel.Text':'请输入人数与单价'})])


def build14():
    p=base(14,'YXCourse14','程序侦探挑战')
    p.screen([p.page(intro(p,'运动积分侦探','第 14 课｜用测试证据找到程序里的原因')+[
        p.label('GoalLabel','完成一次运动加 2 分，10 分达标。',FontSize=21,FontBold='True',Height=75),
        p.label('ScoreLabel','得分：0',FontSize=36,FontBold='True',Height=105,BackgroundColor='&HFFFFFFFF',TextAlignment=1),
        p.label('StatusLabel','继续努力',FontSize=23,Height=75,TextAlignment=1),p.button('AddButton','完成一次运动 +2'),
        p.button('ResetButton','重新开始',BackgroundColor='&HFFDCEFFF',TextColor='&HFF123E62'),
        p.label('HintLabel','课堂支架版故意保留 3 个逻辑错误；完整答案版已经修复。',FontSize=14,TextColor='&HFF56758B')])])
    def refresh(op):
        return p.chain(p.set('ScoreLabel','Text',p.join(p.text('得分：'),p.var('得分'))),p.iff(p.cmp(op,p.var('得分'),p.var('目标')),
            p.set('StatusLabel','Text',p.text('达标！')),p.set('StatusLabel','Text',p.text('继续努力'))))
    p.tops=[p.global_('得分',p.num(0)),p.global_('目标',p.num(10)),p.define('刷新',refresh('GTE')),
        p.define('重置',p.chain(p.setvar('得分',p.num(0)),p.call('刷新'))),
        p.event('AddButton','Click',p.chain(p.setvar('得分',p.add(p.var('得分'),p.num(2))),p.call('刷新'))),
        p.event('ResetButton','Click',p.call('重置'))]
    p.class_tops=copy.deepcopy(p.tops[:2])+[
        p.note(p.define('刷新',refresh('GT')),'侦探任务：10分应该达标，当前比较却不含等号。'),
        p.note(p.define('重置',p.chain(p.set('ScoreLabel','Text',p.text('得分：0')),p.set('StatusLabel','Text',p.text('继续努力')))),'侦探任务：这里只清了显示，源变量得分没有清零。'),
        p.note(p.event('AddButton','Click',p.chain(p.setvar('得分',p.num(2)),p.call('刷新'))),'侦探任务：固定赋值2不会累计。'),copy.deepcopy(p.tops[5])]
    return p,dict(work='运动积分器的三类故障修复',classroomKept=['完整组件界面','全部变量、过程与事件；故意保留三项逻辑缺陷'],classroomTasks=['AddButton.Click 固定2改为得分+2','刷新过程的GT改为GTE','重置过程改为得分=0后调用刷新'],
        intentionalClassroomBugs=[dict(target='AddButton.Click',fault='得分固定设为2',fix='得分←得分+2'),dict(target='刷新',fault='使用>目标，10分不达标',fix='比较改为≥目标'),dict(target='重置',fault='只清标签，没有清全局得分',fix='设置得分为0，再调用刷新')],
        screenshotGroups=['AddButton.Click','刷新','重置'],tests=[
            dict(events=['AddButton.Click']*2,expect={'global 得分':4,'ScoreLabel.Text':'得分：4'}),
            dict(events=['AddButton.Click']*5,expect={'global 得分':10,'StatusLabel.Text':'达标！'}),
            dict(events=['AddButton.Click']*5+['ResetButton.Click','AddButton.Click'],expect={'global 得分':2,'StatusLabel.Text':'继续努力'})])


def emit(number):
    p, detail=globals()[f'build{number:02d}']()
    folder=OUT/f'lesson{number:02d}'
    versions=p.write(folder)
    (folder/'blocks.xml').write_bytes(p.xml('answer'))
    assets=folder/'assets';assets.mkdir(exist_ok=True)
    for name,value in p.assets.items():
        (assets/name).write_bytes(value.read_bytes() if isinstance(value,Path) else value)
    def target(top):
        fields={f.get('name'):f.text for f in top.findall('field')}
        mutation=top.find('mutation')
        return (mutation.get('instance_name')+'.'+mutation.get('event_name')) if top.get('type')=='component_event' else fields.get('NAME','')
    captures=[]
    for i,name in enumerate(detail['screenshotGroups'],1):
        candidates=[(j,b) for j,b in enumerate(p.tops) if target(b)==name]
        if len(candidates)!=1:raise ValueError(f'Capture target {name} is not unique')
        j,b=candidates[0];captures.append(dict(blockIndex=i,target=name,topLevelIndex=j,blockId=b.get('id')))
    bp=json.loads((BLUEPRINTS/f'lesson{number:02d}.json').read_text(encoding='utf8'))
    spec=dict(lesson=number,title=p.title,projectName=p.name,versions=versions,
        components=[dict(name=n,type=c['$Type'],version=c['$Version'],properties={k:v for k,v in c.items() if not k.startswith('$') and k!='Uuid'}) for n,c in p.components.items()],
        variants=dict(answer='完整参考答案；全部规则、交互事件与过程均已实现',classroom='课堂支架：详见 classroomKept 与 classroomTasks；第14课故意保留三项逻辑缺陷' if number==14 else '课堂支架：保留有效输入和示范结构，目标逻辑由学生补齐',starter='纯界面起始版：组件、静态属性和素材与答案相同，积木为空'),
        captureGroups=captures,assets=[dict(file='logo.png',source='用户提供的羽轩品牌 logo，课堂本地示例复用')],
        sources=bp['sources'],staticValidation=dict(componentReferences='pass',designerProperties='pass: exact distribution metadata',eventMethods='pass: exact distribution metadata',valueSockets='pass',assetReferences='pass'),
        nativeImportValidation='pending',apkCompilation='pending',androidDeviceTest='not requested',**detail)
    (folder/'artifact-spec.json').write_text(json.dumps(spec,ensure_ascii=False,indent=2),encoding='utf8')
    print(json.dumps(dict(lesson=number,project=p.name,versions=[dict(kind=v['kind'],blocks=v['blockCount']) for v in versions]),ensure_ascii=False))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('lessons',nargs='*',type=int,default=list(range(7,15)));args=parser.parse_args()
    for n in args.lessons:
        if not 7<=n<=14:parser.error('This batch covers lessons 7–14')
        emit(n)
