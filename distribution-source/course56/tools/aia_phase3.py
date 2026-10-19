"""Native App Inventor projects for drawing, animation and games (15–22).

Lesson 19 is preserved verbatim in its original verified package and is never
rewritten here.  All assets are local, and every classroom variant is explicit.
"""
from pathlib import Path
import argparse
import copy
import json

from aia_core import ROOT, AiaProject
from aia_phase1 import base, intro

OUT=ROOT/'work/course56/aia'
BLUEPRINTS=ROOT/'work/course56/blueprints'
L19=ROOT/'outputs/课程案例/第19课-接物游戏/素材'
BLUE=-15497012
RED=-2396013


def ref(p,name):
    return p.b('component_component_block',{'COMPONENT_SELECTOR':name},mutation={'component_type':p.types[name],'instance_name':name})


def lists(p,*items):
    return p.b('lists_create_with',values={f'ADD{i}':v for i,v in enumerate(items)},mutation={'items':len(items)})


def build15():
    p=base(15,'YXCourse15','手机涂鸦板')
    p.screen([p.page(intro(p,'随手涂鸦板','第 15 课｜颜色和粗细，由你决定')+[
        p.comp('ColorRow','HorizontalArrangement',[p.button('BlueButton','天蓝笔',Width=-1050),p.button('RedButton','红色笔',Width=-1050,BackgroundColor='&HFFDB6F73')],Width=-2,Height=54),
        p.comp('WidthRow','HorizontalArrangement',[p.button('ThinButton','细线 2',Width=-1050,BackgroundColor='&HFFDCEFFF',TextColor='&HFF123E62'),p.button('ThickButton','粗线 10',Width=-1050,BackgroundColor='&HFFDCEFFF',TextColor='&HFF123E62')],Width=-2,Height=54),
        p.label('ToolLabel','当前画笔：5 像素（提示文字即画笔色）',FontSize=15,Height=42,TextColor='&HFF1388CC'),
        p.comp('PaintCanvas','Canvas',Width=-2,Height=-2,LineWidth=5,PaintColor='&HFF1388CC',BackgroundColor='&HFFFFFFFF'),
        p.button('ClearButton','清空画布',Height=48,BackgroundColor='&HFFDCEFFF',TextColor='&HFF123E62')],Height=-2)],Scrollable='False')
    choose=p.define('选择画笔',p.chain(p.set('PaintCanvas','PaintColor',p.param('颜色')),p.set('PaintCanvas','LineWidth',p.param('宽度')),
        p.set('ToolLabel','TextColor',p.param('颜色')),p.set('ToolLabel','Text',p.join(p.text('当前画笔：'),p.param('宽度'),p.text(' 像素（提示文字即画笔色）')))),args=('颜色','宽度'))
    p.tops=[choose,
        p.event('PaintCanvas','Dragged',p.method('PaintCanvas','DrawLine',p.param('prevX',True),p.param('prevY',True),p.param('currentX',True),p.param('currentY',True)), '上一点接当前点；startX/startY仅表示整次手势起点，不能代替prevX/prevY。'),
        p.event('PaintCanvas','Touched',p.method('PaintCanvas','DrawCircle',p.param('x',True),p.param('y',True),p.div(p.get('PaintCanvas','LineWidth'),p.num(2)),p.boolean(True))),
        p.event('BlueButton','Click',p.call('选择画笔',p.num(BLUE),p.get('PaintCanvas','LineWidth'),names=('颜色','宽度'))),
        p.event('RedButton','Click',p.call('选择画笔',p.num(RED),p.get('PaintCanvas','LineWidth'),names=('颜色','宽度'))),
        p.event('ThinButton','Click',p.call('选择画笔',p.get('PaintCanvas','PaintColor'),p.num(2),names=('颜色','宽度'))),
        p.event('ThickButton','Click',p.call('选择画笔',p.get('PaintCanvas','PaintColor'),p.num(10),names=('颜色','宽度'))),
        p.event('ClearButton','Click',p.method('PaintCanvas','Clear'))]
    p.class_tops=[copy.deepcopy(p.tops[i]) for i in [0,3,4,5,6]]
    return p,dict(work='可选颜色与粗细的涂鸦板',classroomKept=['选择画笔(颜色,宽度)','颜色与粗细四个按钮事件'],classroomTasks=['添加PaintCanvas.Dragged，用prevX/prevY连接currentX/currentY','添加PaintCanvas.Touched，画线宽一半半径的实心圆','添加ClearButton.Click，调用Clear'],
        screenshotGroups=['PaintCanvas.Dragged','BlueButton.Click','PaintCanvas.Touched'],tests=[
            dict(event='PaintCanvas.Dragged',args={'prevX':10,'prevY':20,'currentX':35,'currentY':55},methods=['PaintCanvas.DrawLine:10,20,35,55']),
            dict(events=['RedButton.Click','ThickButton.Click'],expect={'PaintCanvas.PaintColor':RED,'PaintCanvas.LineWidth':10}),
            dict(set={'PaintCanvas.LineWidth':10},event='PaintCanvas.Touched',args={'x':50,'y':60},methods=['PaintCanvas.DrawCircle:50,60,5,true']),
            dict(event='ClearButton.Click',methods=['PaintCanvas.Clear'])])


def build16():
    p=base(16,'YXCourse16','用程序画出图案')
    p.screen([p.page(intro(p,'程序绘出的几何花园','第 16 课｜循环确定数量，参数决定位置')+[
        p.comp('PatternCanvas','Canvas',Width=-2,Height=350,LineWidth=3,PaintColor='&HFF1388CC',BackgroundColor='&HFFFFFFFF'),
        p.comp('PatternButtons','HorizontalArrangement',[p.button('LinesButton','五条横线',Width=-1033),p.button('GridButton','两个方格',Width=-1033),p.button('RingsButton','同心圆',Width=-1034)],Width=-2,Height=58),
        p.button('ClearButton','清空',BackgroundColor='&HFFDCEFFF',TextColor='&HFF123E62'),
        p.label('HintLabel','每种图案先清空画布。修改参数可以改变位置、间距和大小。',FontSize=14,TextColor='&HFF56758B')])])
    def square(n=4):
        x=lambda:p.param('x');y=lambda:p.param('y');endx=lambda:p.add(x(),p.param('边长'));endy=lambda:p.add(y(),p.param('边长'))
        edges=[p.method('PatternCanvas','DrawLine',x(),y(),endx(),y()),p.method('PatternCanvas','DrawLine',endx(),y(),endx(),endy()),
               p.method('PatternCanvas','DrawLine',endx(),endy(),x(),endy()),p.method('PatternCanvas','DrawLine',x(),endy(),x(),y())]
        return p.chain(*edges[:n])
    drawring=lambda radius:p.method('PatternCanvas','DrawCircle',p.param('中心X'),p.param('中心Y'),radius,p.boolean(False))
    def lines(varied=True):
        y=lambda:p.add(p.num(30),p.mul(p.param('i'),p.num(30))) if varied else p.num(30)
        return p.chain(p.method('PatternCanvas','Clear'),p.forrange('i',p.num(0),p.num(4),p.num(1),p.method('PatternCanvas','DrawLine',p.num(20),y(),p.sub(p.get('PatternCanvas','Width'),p.num(20)),y())))
    p.tops=[p.define('画方格',square(),args=('x','y','边长')),
        p.define('画圆环',p.forrange('半径',p.num(20),p.num(60),p.num(20),drawring(p.param('半径'))),args=('中心X','中心Y')),
        p.event('LinesButton','Click',lines()),
        p.event('GridButton','Click',p.chain(p.method('PatternCanvas','Clear'),p.call('画方格',p.num(30),p.num(30),p.num(80),names=('x','y','边长')),p.call('画方格',p.num(130),p.num(130),p.num(80),names=('x','y','边长')))),
        p.event('RingsButton','Click',p.chain(p.method('PatternCanvas','Clear'),p.call('画圆环',p.div(p.get('PatternCanvas','Width'),p.num(2)),p.num(150),names=('中心X','中心Y')))),
        p.event('ClearButton','Click',p.method('PatternCanvas','Clear'))]
    p.class_tops=[p.note(p.define('画方格',square(2),args=('x','y','边长')),'课堂任务：目前只有两条边，用参数补齐另两条边。'),
        p.note(p.define('画圆环',drawring(p.num(60)),args=('中心X','中心Y')),'课堂任务：将单次画圆改成半径20到60、步长20的循环。'),
        p.note(p.event('LinesButton','Click',lines(False)),'课堂任务：两个Y坐标都由固定30改成30+i×30。')]+copy.deepcopy(p.tops[3:])
    return p,dict(work='循环几何图案生成器',classroomKept=['完整按钮入口','画方格的前两条边','横线循环框架，Y暂固定30','单个圆的画圆环过程'],classroomTasks=['横线两个Y改为30+i×30','补齐方格后两条边','用半径20、40、60循环画空心圆'],
        screenshotGroups=['LinesButton.Click','画方格','画圆环'],tests=[
            dict(event='LinesButton.Click',methodCounts={'PatternCanvas.DrawLine':5},methodArgValues={'PatternCanvas.DrawLine.1':[30,60,90,120,150]}),
            dict(event='GridButton.Click',methodCounts={'PatternCanvas.DrawLine':8}),
            dict(set={'PatternCanvas.Width':320},event='RingsButton.Click',methodCounts={'PatternCanvas.DrawCircle':3},methodArgValues={'PatternCanvas.DrawCircle.2':[20,40,60]}),
            dict(event='ClearButton.Click',methods=['PatternCanvas.Clear'])])


def build17():
    p=base(17,'YXCourse17','让角色动起来')
    p.assets['apple.png']=L19/'apple.png'
    p.screen([p.page(intro(p,'角色运动实验场','第 17 课｜方向、速度与坐标')+[
        p.comp('StageCanvas','Canvas',[
            p.comp('RunnerBall','Ball',Radius=14,Speed=0,Interval=50,Heading=0,X=30,Y=80,OriginAtCenter='True',PaintColor='&HFF1388CC'),
            p.comp('Marker','ImageSprite',Picture='apple.png',Width=40,Height=40,X=120,Y=150,Speed=0,Rotates='False',OriginX=0,OriginY=0)
        ],Width=-2,Height=340,BackgroundColor='&HFFFFFFFF'),
        p.comp('MotionButtons','HorizontalArrangement',[p.button('RunButton','开始运动',Width=-1050),
            p.comp('DirectionPicker','ListPicker',Text='选择方向：右',Title='小球运动方向',Width=-1050,Height=52,FontSize=17,BackgroundColor='&HFF1388CC',TextColor='&HFFFFFFFF',ElementsFromString='右,上,左,下')],Width=-2,Height=58),
        p.label('SpeedLabel','速度滑块：1～8 像素／50毫秒',FontSize=15,Height=38),
        p.comp('SpeedSlider','Slider',MinValue=1,MaxValue=8,ThumbPosition=4,NumberOfSteps=7,Width=-2,ColorLeft='&HFF1388CC'),
        p.label('StatusLabel','已暂停｜方向0°｜速度0',FontSize=17,Height=48),
        p.button('ResetButton','恢复起点',BackgroundColor='&HFFDCEFFF',TextColor='&HFF123E62'),
        p.label('HintLabel','点击画布定位苹果。小球到边缘后可改方向或重置，反弹在下一课学习。',FontSize=14,TextColor='&HFF56758B')])])
    def status():return p.set('StatusLabel','Text',p.join(p.text('方向'),p.get('RunnerBall','Heading'),p.text('°｜速度'),p.get('RunnerBall','Speed'),p.text(' 像素/50ms')))
    speed=p.iff(p.var('运行中'),p.chain(p.set('RunnerBall','Speed',p.b('math_round',{'OP':'ROUND'},{'NUM':p.get('SpeedSlider','ThumbPosition')})),p.set('RunButton','Text',p.text('暂停'))),p.chain(p.set('RunnerBall','Speed',p.num(0)),p.set('RunButton','Text',p.text('开始运动'))))
    def position():
        return p.method('Marker','MoveTo',p.mm('MAX',p.num(0),p.mm('MIN',p.sub(p.get('StageCanvas','Width'),p.get('Marker','Width')),p.sub(p.param('x'),p.div(p.get('Marker','Width'),p.num(2))))),
            p.mm('MAX',p.num(0),p.mm('MIN',p.sub(p.get('StageCanvas','Height'),p.get('Marker','Height')),p.sub(p.param('y'),p.div(p.get('Marker','Height'),p.num(2))))))
    p.tops=[p.global_('运行中',p.boolean(False)),p.define('刷新速度',p.chain(speed,status())),p.define('定位图片',position(),args=('x','y')),
        p.define('回到起点',p.chain(p.setvar('运行中',p.boolean(False)),p.set('RunnerBall','Heading',p.num(0)),p.set('SpeedSlider','ThumbPosition',p.num(4)),p.method('RunnerBall','MoveTo',p.num(30),p.num(80)),p.method('Marker','MoveTo',p.num(120),p.num(150)),p.set('DirectionPicker','Text',p.text('选择方向：右')),p.call('刷新速度'))),
        p.event('Screen1','Initialize',p.call('回到起点')),
        p.event('RunButton','Click',p.chain(p.iff(p.var('运行中'),p.setvar('运行中',p.boolean(False)),p.setvar('运行中',p.boolean(True))),p.call('刷新速度'))),
        p.event('DirectionPicker','BeforePicking',p.set('DirectionPicker','Elements',lists(p,p.text('右'),p.text('上'),p.text('左'),p.text('下')))),
        p.event('DirectionPicker','AfterPicking',p.chain(p.iff(p.cmp('GT',p.get('DirectionPicker','SelectionIndex'),p.num(0)),p.chain(p.set('RunnerBall','Heading',p.mul(p.sub(p.get('DirectionPicker','SelectionIndex'),p.num(1)),p.num(90))),p.set('DirectionPicker','Text',p.join(p.text('选择方向：'),p.get('DirectionPicker','Selection'))))),p.call('刷新速度'))),
        p.event('SpeedSlider','PositionChanged',p.call('刷新速度')),
        p.event('StageCanvas','Touched',p.call('定位图片',p.param('x',True),p.param('y',True),names=('x','y'))),p.event('ResetButton','Click',p.call('回到起点'))]
    p.class_tops=[copy.deepcopy(p.tops[0]),p.note(p.define('刷新速度',p.chain(p.set('RunnerBall','Speed',p.num(0)),status())),'课堂任务：根据运行中状态，将速度设为滑块四舍五入值或0，同时改按钮文字。'),
        p.note(p.define('定位图片',p.method('Marker','MoveTo',p.param('x'),p.param('y')),args=('x','y')),'课堂任务：坐标减去角色一半尺寸，并用max/min限制边界。')]+copy.deepcopy(p.tops[3:7])+[
        p.note(p.event('DirectionPicker','AfterPicking',p.chain(p.set('RunnerBall','Heading',p.num(0)),p.call('刷新速度'))),'课堂任务：把固定0度改为(SelectionIndex-1)×90。')]+copy.deepcopy(p.tops[8:])
    return p,dict(work='小球运动与图片触摸定位实验',classroomKept=['global 运行中','回到起点与各事件入口','方向列表','刷新速度、定位图片及选方向中的占位表达式'],classroomTasks=['根据运行中控制速度和开始/暂停文字','四个方向映射为0/90/180/270度','图片中心跟随触摸并限制边界'],
        screenshotGroups=['刷新速度','DirectionPicker.AfterPicking','定位图片'],tests=[
            dict(event='RunButton.Click',expect={'global 运行中':True,'RunnerBall.Speed':4}),
            dict(events=['RunButton.Click','RunButton.Click'],expect={'global 运行中':False,'RunnerBall.Speed':0}),
            dict(set={'DirectionPicker.SelectionIndex':2,'DirectionPicker.Selection':'上'},event='DirectionPicker.AfterPicking',expect={'RunnerBall.Heading':90}),
            dict(set={'StageCanvas.Width':320,'StageCanvas.Height':340},event='StageCanvas.Touched',args={'x':320,'y':340},expect={'Marker.X':280,'Marker.Y':300})],limitations=['小球的连续移动由原生Sprite调度器实现；自动逻辑测试不代替Android运动帧率实测'])


def build18():
    p=base(18,'YXCourse18','弹球与碰撞')
    p.screen([p.page(intro(p,'弹球练习场','第 18 课｜碰边反弹，命中橙色目标加分')+[
        p.label('ScoreLabel','命中次数：0',FontSize=24,FontBold='True',Height=55),
        p.comp('GameCanvas','Canvas',[p.comp('PlayBall','Ball',Radius=12,Speed=0,Interval=40,Heading=35,X=30,Y=60,OriginAtCenter='True',PaintColor='&HFF1388CC'),
            p.comp('TargetBall','Ball',Radius=18,Speed=0,X=220,Y=220,OriginAtCenter='True',PaintColor='&HFFF59E0B')],Width=-2,Height=340,BackgroundColor='&HFFFFFFFF'),
        p.comp('GameButtons','HorizontalArrangement',[p.button('StartButton','开始',Width=-1050),p.button('ResetButton','归零重开',Width=-1050,BackgroundColor='&HFFDCEFFF',TextColor='&HFF123E62')],Width=-2,Height=58),
        p.label('HintLabel','蓝球碰边不加分，碰到橙球才加1。暂停后球停在原位。',FontSize=15,TextColor='&HFF56758B')])])
    def reset(clear=True):
        return p.chain(p.set('PlayBall','Speed',p.num(0)),p.setvar('运行中',p.boolean(False)),p.setvar('得分',p.num(0)) if clear else None,
            p.set('PlayBall','Heading',p.num(35)),p.method('PlayBall','MoveTo',p.num(30),p.num(60)),p.call('移动目标'),p.call('刷新得分'),p.set('StartButton','Text',p.text('开始')))
    p.tops=[p.global_('得分',p.num(0)),p.global_('运行中',p.boolean(False)),
        p.define('移动目标',p.method('TargetBall','MoveTo',p.random(p.num(20),p.mm('MAX',p.num(20),p.sub(p.get('GameCanvas','Width'),p.num(50)))),p.random(p.num(20),p.mm('MAX',p.num(20),p.sub(p.get('GameCanvas','Height'),p.num(50)))))),
        p.define('刷新得分',p.set('ScoreLabel','Text',p.join(p.text('命中次数：'),p.var('得分')))),p.define('重置',reset()),
        p.event('Screen1','Initialize',p.call('重置')),
        p.event('PlayBall','EdgeReached',p.method('PlayBall','Bounce',p.param('edge',True))),
        p.event('PlayBall','CollidedWith',p.iff(p.both(p.var('运行中'),p.eq(p.param('other',True),ref(p,'TargetBall'))),p.chain(p.setvar('得分',p.add(p.var('得分'),p.num(1))),p.call('刷新得分'),p.call('移动目标')))),
        p.event('StartButton','Click',p.iff(p.var('运行中'),p.chain(p.setvar('运行中',p.boolean(False)),p.set('PlayBall','Speed',p.num(0)),p.set('StartButton','Text',p.text('继续'))),p.chain(p.setvar('运行中',p.boolean(True)),p.set('PlayBall','Speed',p.num(5)),p.set('StartButton','Text',p.text('暂停'))))),
        p.event('ResetButton','Click',p.call('重置'))]
    p.class_tops=copy.deepcopy(p.tops[:4])+[p.note(p.define('重置',reset(False)),'课堂任务：在刷新之前将全局得分清0。')]+[copy.deepcopy(p.tops[i]) for i in [5,8,9]]
    return p,dict(work='反弹与目标命中练习',classroomKept=['全部变量','移动目标、刷新得分','重置的位置与停止部分','初始化和两个按钮事件'],classroomTasks=['添加PlayBall.EdgeReached，把edge传给Bounce','添加PlayBall.CollidedWith，运行中且other为TargetBall时计分','重置过程补上得分=0'],
        screenshotGroups=['PlayBall.EdgeReached','PlayBall.CollidedWith','重置'],tests=[
            dict(event='PlayBall.EdgeReached',args={'edge':3},methods=['PlayBall.Bounce:3'],expect={'global 得分':0}),
            dict(set={'global 运行中':True},event='PlayBall.CollidedWith',args={'other':{'component':'TargetBall'}},expect={'global 得分':1,'ScoreLabel.Text':'命中次数：1'}),
            dict(set={'global 运行中':False,'global 得分':2},event='PlayBall.CollidedWith',args={'other':{'component':'TargetBall'}},expect={'global 得分':2}),
            dict(set={'global 得分':5},event='ResetButton.Click',expect={'global 得分':0,'PlayBall.Speed':0,'PlayBall.X':30,'PlayBall.Y':60})])


def build20():
    p=base(20,'YXCourse20','接物游戏：完善规则')
    p.assets.update({n:L19/n for n in ['apple.png','basket.png']})
    p.screen([p.page([p.label('TitleLabel','接住小苹果·规则升级',FontSize=24,FontBold='True',Height=48,TextAlignment=1),
        p.comp('ScoreRow','HorizontalArrangement',[p.label('ScoreLabel','得分：0',Width=-1050,FontSize=21,Height=42),p.label('LivesLabel','生命：3',Width=-1050,FontSize=21,Height=42)],Width=-2,Height=44),
        p.comp('GameCanvas','Canvas',[p.comp('Fruit','ImageSprite',Picture='apple.png',Width=38,Height=38,X=140,Y=20,Visible='False',Enabled='True',Speed=0,Rotates='False',OriginX=0,OriginY=0),
            p.comp('Basket','ImageSprite',Picture='basket.png',Width=90,Height=49,X=110,Y=70,Speed=0,Rotates='False',OriginX=0,OriginY=0)],Width=-2,Height=-2,BackgroundColor='&HFFEAF7FF'),
        p.comp('Controls','HorizontalArrangement',[p.button('StartButton','开始',Width=-1050,Height=48),p.button('ResetButton','重新开始',Width=-1050,Height=48,BackgroundColor='&HFFDCEFFF',TextColor='&HFF123E62')],Width=-2,Height=52),
        p.label('HintLabel','待开始｜3次生命，每5分加速。',Height=60,FontSize=15,TextAlignment=1)],Height=-2),
        p.comp('FallClock','Clock',TimerInterval=30,TimerEnabled='False',TimerAlwaysFires='False')],Scrollable='False')
    bottom=lambda:p.set('Basket','Y',p.mm('MAX',p.num(0),p.sub(p.sub(p.get('GameCanvas','Height'),p.get('Basket','Height')),p.num(8))))
    update=lambda:p.chain(p.set('ScoreLabel','Text',p.join(p.text('得分：'),p.var('得分'))),p.set('LivesLabel','Text',p.join(p.text('生命：'),p.var('生命'))),p.set('HintLabel','Text',p.join(p.text('状态：'),p.var('状态'),p.text('｜下落步长：'),p.var('下落步长'))))
    respawn=lambda:p.chain(p.set('Fruit','X',p.random(p.num(0),p.mm('MAX',p.num(0),p.sub(p.get('GameCanvas','Width'),p.get('Fruit','Width'))))),p.set('Fruit','Y',p.num(0)),p.set('Fruit','Visible',p.boolean(True)))
    movement=p.set('Basket','X',p.mm('MAX',p.num(0),p.mm('MIN',p.sub(p.get('GameCanvas','Width'),p.get('Basket','Width')),p.sub(p.param('目标X'),p.div(p.get('Basket','Width'),p.num(2))))))
    end=p.chain(p.setvar('状态',p.text('结束')),p.set('FallClock','TimerEnabled',p.boolean(False)),p.set('Fruit','Visible',p.boolean(False)),p.set('StartButton','Enabled',p.boolean(False)),p.call('更新面板'),p.set('HintLabel','Text',p.join(p.text('游戏结束！最终得分：'),p.var('得分'),p.text('。点击重新开始。'))))
    reset=p.chain(p.set('FallClock','TimerEnabled',p.boolean(False)),p.setvar('得分',p.num(0)),p.setvar('生命',p.num(3)),p.setvar('下落步长',p.num(5)),p.setvar('状态',p.text('待开始')),p.set('Fruit','Visible',p.boolean(False)),bottom(),p.call('移动篮子',p.div(p.get('GameCanvas','Width'),p.num(2)),names=('目标X',)),p.set('StartButton','Enabled',p.boolean(True)),p.set('StartButton','Text',p.text('开始')),p.call('更新面板'))
    start=p.iff(p.eq(p.var('状态'),p.text('运行')),p.chain(p.setvar('状态',p.text('暂停')),p.set('FallClock','TimerEnabled',p.boolean(False)),p.set('StartButton','Text',p.text('继续')),p.call('更新面板')),
        p.iff(p.eq(p.var('状态'),p.text('暂停')),p.chain(p.setvar('状态',p.text('运行')),p.set('FallClock','TimerEnabled',p.boolean(True)),p.set('StartButton','Text',p.text('暂停')),p.call('更新面板')),
            p.iff(p.eq(p.var('状态'),p.text('待开始')),p.chain(bottom(),p.call('移动篮子',p.div(p.get('GameCanvas','Width'),p.num(2)),names=('目标X',)),p.call('重置苹果'),p.setvar('状态',p.text('运行')),p.set('FallClock','TimerEnabled',p.boolean(True)),p.set('StartButton','Text',p.text('暂停')),p.call('更新面板')))))
    def timer(lives=True):
        miss=p.chain(p.setvar('生命',p.mm('MAX',p.num(0),p.sub(p.var('生命'),p.num(1)))),p.iff(p.cmp('LTE',p.var('生命'),p.num(0)),p.call('结束游戏'),p.chain(p.call('重置苹果'),p.call('更新面板')))) if lives else p.call('重置苹果')
        return p.iff(p.eq(p.var('状态'),p.text('运行')),p.chain(p.set('Fruit','Y',p.add(p.get('Fruit','Y'),p.var('下落步长'))),p.iff(p.cmp('GTE',p.get('Fruit','Y'),p.sub(p.get('GameCanvas','Height'),p.get('Fruit','Height'))),miss)))
    p.tops=[p.global_('得分',p.num(0)),p.global_('生命',p.num(3)),p.global_('状态',p.text('待开始')),p.global_('下落步长',p.num(5)),
        p.define('更新面板',update()),p.define('重置苹果',respawn()),p.define('移动篮子',movement,args=('目标X',)),
        p.define('结束游戏',end),p.define('重新开始',reset),p.define('调整难度',p.setvar('下落步长',p.mm('MIN',p.num(12),p.add(p.num(5),p.floor(p.div(p.var('得分'),p.num(5))))))),
        p.event('Screen1','Initialize',p.call('重新开始')),p.event('StartButton','Click',start),p.event('FallClock','Timer',timer()),
        p.event('Fruit','CollidedWith',p.iff(p.both(p.eq(p.var('状态'),p.text('运行')),p.eq(p.param('other',True),ref(p,'Basket'))),p.chain(p.setvar('得分',p.add(p.var('得分'),p.num(1))),p.call('调整难度'),p.call('更新面板'),p.call('重置苹果')))),
        p.event('ResetButton','Click',p.call('重新开始')),p.event('GameCanvas','Dragged',p.call('移动篮子',p.param('currentX',True),names=('目标X',))),p.event('GameCanvas','Touched',p.call('移动篮子',p.param('x',True),names=('目标X',)))]
    p.class_tops=copy.deepcopy(p.tops[:7])+[
        p.note(p.define('结束游戏',p.set('HintLabel','Text',p.text('课堂任务：补齐结束状态、停表、隐藏苹果与禁用开始键。'))),'此过程暂仅显示课堂提示，结束逻辑由学生完成。'),
        copy.deepcopy(p.tops[8]),p.note(p.define('调整难度',p.setvar('下落步长',p.num(5))),'课堂任务：改为min(12,5+floor(得分/5))。')]+copy.deepcopy(p.tops[10:12])+[
        p.note(p.event('FallClock','Timer',timer(False)),'本支架沿用第19课漏接后重生的规则。升级任务：扣生命，并在生命为0时调用结束游戏。')]+copy.deepcopy(p.tops[13:])
    return p,dict(work='三生命与递增难度接苹果',classroomKept=['第19课的移动、接取、开始/暂停/继续机制','全部新增变量和面板','重新开始、重置苹果、移动篮子','调整难度和结束游戏的占位过程'],classroomTasks=['FallClock.Timer漏接先扣生命再判断结束','调整难度改为min(12,5+floor(得分/5))','结束游戏停止Clock、隐藏苹果、禁用开始并显示最终分'],
        screenshotGroups=['FallClock.Timer','调整难度','结束游戏'],tests=[
            dict(set={'global 状态':'运行','global 生命':1,'GameCanvas.Height':340,'Fruit.Y':301},event='FallClock.Timer',expect={'global 生命':0,'global 状态':'结束','FallClock.TimerEnabled':False,'StartButton.Enabled':False}),
            dict(set={'global 状态':'运行','global 得分':4},event='Fruit.CollidedWith',args={'other':{'component':'Basket'}},expect={'global 得分':5,'global 下落步长':6}),
            dict(set={'global 得分':35},procedure='调整难度',expect={'global 下落步长':12}),
            dict(set={'global 状态':'暂停','Fruit.Y':120},event='StartButton.Click',expect={'global 状态':'运行','Fruit.Y':120}),
            dict(event='ResetButton.Click',expect={'global 得分':0,'global 生命':3,'global 下落步长':5,'global 状态':'待开始','StartButton.Enabled':True})])


def build21():
    p=base(21,'YXCourse21','可以选择结局的故事')
    school=ROOT/'work/course56/assets/scene_school.png'
    scene_asset='scene_school.png' if school.exists() else 'logo.png'
    if school.exists():p.assets[scene_asset]=school
    p.screen([p.page(intro(p,'失物招领小故事','第 21 课｜一次选择，走向不同的结局')+[
        p.label('SceneTitle','校门：一个遗落的文具袋',FontSize=23,FontBold='True',Height=65),
        p.comp('SceneImage','Image',Picture=scene_asset,Width=-2,Height=220,ScalePictureToFit='True',AlternateText='校园失物招领故事场景参考图' if school.exists() else '羽轩课程标识；故事以文字场景呈现'),
        p.label('SceneText','你在校门旁发现一个文具袋。放学时间快到了，你决定先去哪里寻找线索？',FontSize=19,Height=145,BackgroundColor='&HFFFFFFFF'),
        p.button('ChoiceA','去操场看看'),p.button('ChoiceB','去教师办公室'),
        p.comp('ReaderControls','HorizontalArrangement',[p.button('ReadButton','朗读这一幕',Width=-1050,BackgroundColor='&HFFDCEFFF',TextColor='&HFF123E62'),p.button('RestartButton','重新阅读',Width=-1050,BackgroundColor='&HFFDCEFFF',TextColor='&HFF123E62')],Width=-2,Height=58)]),
        p.comp('Voice','TextToSpeech',Language='zh',Country='CHN',SpeechRate=.9)])
    scenes={
        '校门':('校门：一个遗落的文具袋','你在校门旁发现一个文具袋。放学时间快到了，你决定先去哪里寻找线索？','去操场看看','去教师办公室',True),
        '操场':('操场：同伴提供了线索','一位同学说，刚才有人在找蓝色的文具袋。你们可以把失物交给老师，也可以明天继续寻找。','一起去教师办公室','明天再继续寻找',True),
        '办公室':('办公室：老师来帮忙','老师记录了失物特征。你描述发现的地点和时间，现在可以请老师联系失主，或者先保管并等待认领。','请老师联系失主','登记后等待明天认领',True),
        '找到主人':('结局一：找到主人','老师联系到了失主。对方说出了文具袋里的物品，你们核对后归还。谢谢你认真对待这次小小的发现！','','',False),
        '明天再找':('结局二：明天继续寻找','你把文具袋交给老师保管，记下发现的时间和地点。今天还没有找到主人，但线索已妥善保存，明天可以继续。','','',False)}
    def display(name,placeholder=False):
        title,body,a,b,visible=scenes[name]
        if placeholder:body='课堂任务：补写这一幕的叙述、选项文字与按钮显示规则。'
        return p.define('场景_'+name,p.chain(p.set('SceneTitle','Text',p.text(title)),p.set('SceneText','Text',p.text(body)),p.set('ChoiceA','Text',p.text(a)),p.set('ChoiceB','Text',p.text(b)),p.set('ChoiceA','Visible',p.boolean(visible)),p.set('ChoiceB','Visible',p.boolean(visible))))
    # Exactly one branch runs; independent if-statements would jump through more
    # than one node after the global scene has been changed by a previous call.
    dispatch=p.call('场景_明天再找')
    for name in reversed(['校门','操场','办公室','找到主人']):
        dispatch=p.iff(p.eq(p.param('名称'),p.text(name)),p.call('场景_'+name),dispatch)
    def choice(a):
        return p.iff(p.eq(p.var('场景'),p.text('校门')),p.call('显示场景',p.text('操场' if a else '办公室'),names=('名称',)),
            p.iff(p.eq(p.var('场景'),p.text('操场')),p.call('显示场景',p.text('办公室' if a else '明天再找'),names=('名称',)),
                p.iff(p.eq(p.var('场景'),p.text('办公室')),p.call('显示场景',p.text('找到主人' if a else '明天再找'),names=('名称',)))))
    p.tops=[p.global_('场景',p.text('校门')),p.define('显示场景',p.chain(p.method('Voice','Stop'),p.setvar('场景',p.param('名称')),dispatch),args=('名称',))]+[display(n) for n in scenes]+[
        p.define('返回开头',p.call('显示场景',p.text('校门'),names=('名称',))),p.event('Screen1','Initialize',p.call('返回开头')),
        p.event('ChoiceA','Click',choice(True)),p.event('ChoiceB','Click',choice(False)),p.event('RestartButton','Click',p.call('返回开头')),
        p.event('ReadButton','Click',p.chain(p.method('Voice','Stop'),p.method('Voice','Speak',p.get('SceneText','Text'))))]
    p.class_tops=copy.deepcopy(p.tops[:2])+[display(n,placeholder=n in ['操场','办公室']) for n in scenes]+[copy.deepcopy(p.tops[i]) for i in [7,8,11,12]]
    return p,dict(work='五场景双结局失物招领故事',classroomKept=['global 场景','显示场景分派和五个场景过程框架','校门与两种结局的完整显示','返回开头、初始化、重读、朗读'],classroomTasks=['补写场景_操场和场景_办公室','添加ChoiceA.Click与ChoiceB.Click的互斥分支跳转','验证结局隐藏选项、重读恢复选项'],
        screenshotGroups=['显示场景','ChoiceA.Click','RestartButton.Click'],tests=[
            dict(events=['Screen1.Initialize','ChoiceA.Click','ChoiceA.Click','ChoiceA.Click'],expect={'global 场景':'找到主人','ChoiceA.Visible':False,'ChoiceB.Visible':False}),
            dict(events=['Screen1.Initialize','ChoiceB.Click','ChoiceB.Click'],expect={'global 场景':'明天再找','ChoiceA.Visible':False}),
            dict(events=['Screen1.Initialize','ChoiceB.Click','ChoiceB.Click','RestartButton.Click'],expect={'global 场景':'校门','ChoiceA.Visible':True,'ChoiceB.Visible':True}),
            dict(event='ReadButton.Click',methods=['Voice.Stop','Voice.Speak'])],limitations=['朗读依赖手机已安装的中文TTS语音；没有进行安卓音频实测'],sceneIllustration='原创校园导览插画' if school.exists() else '当前使用课程标识作为文字舞台插图，尚未附专用校园插画')


def build22():
    p=base(22,'YXCourse22','我的原创小游戏或故事')
    p.screen([p.page(intro(p,'星星护送·参考作品','第 22 课｜改编规则，留下试玩证据')+[
        p.label('StateLabel','待开始：蓝色小球到达金色终点，避开红色障碍。',FontSize=18,Height=85),
        p.comp('StageCanvas','Canvas',[
            p.comp('Hero','Ball',Radius=12,Speed=0,OriginAtCenter='True',X=35,Y=290,PaintColor='&HFF1388CC'),
            p.comp('Obstacle','Ball',Radius=20,Speed=0,Interval=50,Heading=0,OriginAtCenter='True',X=160,Y=170,PaintColor='&HFFE4576B'),
            p.comp('Goal','Ball',Radius=24,Speed=0,OriginAtCenter='True',X=260,Y=40,PaintColor='&HFFF2BE4A')],Width=-2,Height=340,BackgroundColor='&HFFFFFFFF'),
        p.button('StartButton','开始一局'),p.label('HintLabel','在舞台上拖动手指，主角分步追随。先设计一条安全路线；结束后可重开。',FontSize=14,TextColor='&HFF56758B')])])
    # Limit each coordinate change to 18 px so a tap cannot teleport directly
    # through a moving obstacle or instantly jump from the start to the goal.
    def axis(axis,param):
        coord=p.get('Hero',axis)
        desired=p.mm('MAX',p.sub(copy.deepcopy(coord),p.num(18)),p.mm('MIN',p.add(p.get('Hero',axis),p.num(18)),p.param(param)))
        return p.mm('MAX',p.get('Hero','Radius'),p.mm('MIN',p.sub(p.get('StageCanvas','Width' if axis=='X' else 'Height'),p.get('Hero','Radius')),desired))
    move=p.iff(p.eq(p.var('状态'),p.text('运行')),p.method('Hero','MoveTo',axis('X','x'),axis('Y','y')))
    start=p.chain(p.set('Obstacle','Speed',p.num(0)),p.setvar('状态',p.text('待开始')),p.method('Hero','MoveTo',p.num(35),p.sub(p.get('StageCanvas','Height'),p.num(35))),p.method('Obstacle','MoveTo',p.div(p.get('StageCanvas','Width'),p.num(2)),p.div(p.get('StageCanvas','Height'),p.num(2))),p.method('Goal','MoveTo',p.sub(p.get('StageCanvas','Width'),p.num(40)),p.num(40)),p.set('Obstacle','Heading',p.num(0)),p.setvar('状态',p.text('运行')),p.set('Obstacle','Speed',p.num(3)),p.set('StateLabel','Text',p.text('运行中：拖动蓝球，避开红球，到达金色终点。')),p.set('StartButton','Text',p.text('重开一局')))
    finish=p.chain(p.setvar('状态',p.param('结果')),p.set('Obstacle','Speed',p.num(0)),p.set('StateLabel','Text',p.join(p.text('本轮结果：'),p.param('结果'),p.text('。点击重开一局。'))),p.set('StartButton','Text',p.text('重开一局')))
    collided=p.iff(p.eq(p.var('状态'),p.text('运行')),p.iff(p.eq(p.param('other',True),ref(p,'Obstacle')),p.call('结束',p.text('失败'),names=('结果',)),
        p.iff(p.eq(p.param('other',True),ref(p,'Goal')),p.call('结束',p.text('胜利'),names=('结果',)))))
    p.tops=[p.global_('状态',p.text('待开始')),p.define('移动主角',move,args=('x','y')),p.define('开始一局',start),p.define('结束',finish,args=('结果',)),
        p.event('StartButton','Click',p.call('开始一局')),p.event('StageCanvas','Dragged',p.call('移动主角',p.param('currentX',True),p.param('currentY',True),names=('x','y'))),
        p.event('StageCanvas','Touched',p.call('移动主角',p.param('x',True),p.param('y',True),names=('x','y'))),
        p.event('Obstacle','EdgeReached',p.method('Obstacle','Bounce',p.param('edge',True))),p.event('Hero','CollidedWith',collided)]
    p.class_tops=[copy.deepcopy(p.tops[0]),p.note(p.define('移动主角',p.set('StateLabel','Text',p.text('课堂任务：补齐运行时的主角移动与边界限制。')),args=('x','y')),'参考答案额外限制每次坐标变化至18像素，以免点一下就瞬移到终点。'),copy.deepcopy(p.tops[2]),
        p.note(p.define('结束',p.set('StateLabel','Text',p.text('课堂任务：停止障碍并显示结果参数。')),args=('结果',)),'补齐状态、停止速度与提示。')]+copy.deepcopy(p.tops[4:8])
    return p,dict(work='星星护送参考关卡',classroomKept=['global 状态','开始一局的完整摆位与重开','控制事件入口和障碍反弹','移动主角、结束的占位框架'],classroomTasks=['补齐运行态移动，中心坐标按半径限制边界','添加Hero.CollidedWith，区分Obstacle与Goal','结束过程保存结果、停止障碍并显示参数'],
        screenshotGroups=['移动主角','Hero.CollidedWith','开始一局'],tests=[
            dict(set={'StageCanvas.Width':320,'StageCanvas.Height':340},event='StartButton.Click',expect={'global 状态':'运行','Hero.X':35,'Hero.Y':305,'Obstacle.Speed':3,'Goal.X':280,'Goal.Y':40}),
            dict(set={'global 状态':'运行'},event='Hero.CollidedWith',args={'other':{'component':'Obstacle'}},expect={'global 状态':'失败','Obstacle.Speed':0}),
            dict(set={'global 状态':'运行'},event='Hero.CollidedWith',args={'other':{'component':'Goal'}},expect={'global 状态':'胜利','Obstacle.Speed':0}),
            dict(set={'global 状态':'胜利'},event='Hero.CollidedWith',args={'other':{'component':'Obstacle'}},expect={'global 状态':'胜利'}),
            dict(set={'global 状态':'运行','StageCanvas.Width':320,'StageCanvas.Height':340,'Hero.X':35,'Hero.Y':305},event='StageCanvas.Touched',args={'x':320,'y':0},expect={'Hero.X':53,'Hero.Y':287})],
        implementationNotes=['主角中心坐标限制在Radius到Canvas尺寸减Radius之间','每次事件X/Y各最多变化18像素，避免点击目标直接瞬移获胜；在此基础上学生可研究连续碰撞或移动速度'])


def emit(number):
    p,detail=globals()[f'build{number:02d}']();folder=OUT/f'lesson{number:02d}';versions=p.write(folder)
    (folder/'blocks.xml').write_bytes(p.xml('answer'));assets=folder/'assets';assets.mkdir(exist_ok=True)
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
        captureGroups=captures,assets=[dict(file=n,source='用户提供的羽轩品牌logo' if n=='logo.png' else '原第19课配套原创素材复用' if n in ['apple.png','basket.png'] else '本课程原创校园故事插画') for n in p.assets],sources=bp['sources'],
        staticValidation=dict(componentReferences='pass',designerProperties='pass: exact distribution metadata',eventMethods='pass: exact distribution metadata',valueSockets='pass',assetReferences='pass'),
        nativeImportValidation='pending',apkCompilation='pending',androidDeviceTest='not requested',**detail)
    (folder/'artifact-spec.json').write_text(json.dumps(spec,ensure_ascii=False,indent=2),encoding='utf8')
    print(json.dumps(dict(lesson=number,project=p.name,versions=[dict(kind=v['kind'],blocks=v['blockCount']) for v in versions]),ensure_ascii=False))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('lessons',nargs='*',type=int,default=[15,16,17,18,20,21,22]);args=parser.parse_args()
    for n in args.lessons:
        if n not in [15,16,17,18,20,21,22]:parser.error('This batch covers 15–22 and preserves lesson19')
        emit(n)
