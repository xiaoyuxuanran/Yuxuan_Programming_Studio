"""Lists, dictionaries, persistence, CSV and charts for lessons 29–36."""
from pathlib import Path
import argparse
import copy
import json
import xml.etree.ElementTree as ET

from aia_core import ROOT
from aia_phase1 import base, intro
from aia_phase2 import box, integer, numeric_text
from aia_phase3 import lists
from aia_phase4 import choose, empty, negate, emit_project


def view(p,name,height=220):return p.comp(name,'ListView',Width=-2,Height=height,BackgroundColor='&HFFFFFFFF',TextColor='&HFF123E62',FontSize=20,SelectionColor='&HFFDCEFFF',ShowFilterBar='False')
def length(p,value):return p.b('lists_length',values={'LIST':value})
def item(p,items,index):return p.b('lists_select_item',values={'LIST':items,'NUM':index})
def append(p,items,*values):return p.b('lists_add_items',values={'LIST':items,**{f'ITEM{i}':v for i,v in enumerate(values)}},mutation={'items':len(values)})
def replace(p,items,index,value):return p.b('lists_replace_item',values={'LIST':items,'NUM':index,'ITEM':value})
def remove(p,items,index):return p.b('lists_remove_item',values={'LIST':items,'INDEX':index})
def foreach(p,name,items,body):return p.b('controls_forEach',{'VAR':name},{'LIST':items},{'DO':body})
def lookup(p,dictionary,key,default='未填写'):return p.b('dictionaries_lookup',values={'DICT':dictionary,'KEY':p.text(key),'NOTFOUND':p.text(default) if isinstance(default,str) else default})
def setkey(p,dictionary,key,value):return p.b('dictionaries_set_pair',values={'DICT':dictionary,'KEY':p.text(key),'VALUE':value})
def islist(p,value):return p.b('lists_is_list',values={'ITEM':value})
def either(p,a,b):return p.b('logic_operation',{'OP':'OR'},{'A':a,'B':b},mutation={'items':2})
def lower(p,value):return p.b('text_changeCase',{'OP':'DOWNCASE'},{'TEXT':value})
def contains(p,haystack,needle):return p.b('text_contains',{'OP':'CONTAINS'},{'TEXT':haystack,'PIECE':needle},mutation={'mode':'CONTAINS'})


def dictionary(p,**values):
    pairs=[p.b('pair',values={'KEY':p.text(k),'VALUE':v}) for k,v in values.items()]
    return p.b('dictionaries_create_with',values={f'ADD{i}':v for i,v in enumerate(pairs)},mutation={'items':len(pairs)})


def valid_index(p,index,items):return p.both(p.cmp('GTE',index(),p.num(1)),p.cmp('LTE',index(),length(p,items())))


def localset(p,name,value):return p.b('lexical_variable_set',{'VAR':name},{'VALUE':value})


def local_decl(p,bindings,body,returns=False):
    """Native lexical local declarations, scoped only to STACK/RETURN."""
    node=p.b('local_declaration_expression' if returns else 'local_declaration_statement',
        {f'VAR{i}':name for i,(name,_) in enumerate(bindings)},
        {**{f'DECL{i}':value for i,(_,value) in enumerate(bindings)},**({'RETURN':body} if returns else {})},
        {} if returns else {'STACK':body},mutation={})
    mutation=node.find('mutation')
    if mutation is None:mutation=ET.Element('mutation');node.insert(0,mutation)
    for name,_ in bindings:ET.SubElement(mutation,'localname',{'name':name})
    return node


def do_return(p,body,value):return p.b('controls_do_then_return',values={'VALUE':value},statements={'STM':body})


def while_(p,test,body):return p.b('controls_while',values={'TEST':test},statements={'DO':body})


def build29():
    p=base(29,'YXCourse29','用列表管理信息')
    p.screen([p.page(intro(p,'野餐购物清单','第 29 课｜有顺序的一组信息')+[
        view(p,'ItemsView'),p.label('CountLabel','物品数：3',FontSize=19,Height=45),p.comp('ItemBox','TextBox',Hint='再添一件物品',Text='',Width=-2,Height=52,FontSize=20,BackgroundColor='&HFFFFFFFF'),
        p.button('AddButton','追加到清单末尾'),p.label('SelectionLabel','点击物品，查看序号和名称。',FontSize=20,Height=100),p.label('HintLabel','列表从1开始计数。本课允许重复物品，重开应用恢复示例。',FontSize=14,TextColor='&HFF56758B')])])
    p.tops=[p.global_('购物清单',lists(p,*[p.text(x) for x in ['水','面包','苹果']])),p.define('刷新清单',p.chain(p.set('ItemsView','Elements',p.var('购物清单')),p.set('ItemsView','SelectionIndex',p.num(0)),p.set('CountLabel','Text',p.join(p.text('物品数：'),length(p,p.var('购物清单')))),p.set('SelectionLabel','Text',p.text('点击物品，查看序号和名称。')))),
        p.event('Screen1','Initialize',p.call('刷新清单')),p.event('ItemsView','AfterPicking',p.iff(valid_index(p,lambda:p.get('ItemsView','SelectionIndex'),lambda:p.var('购物清单')),p.set('SelectionLabel','Text',p.join(p.text('第'),p.get('ItemsView','SelectionIndex'),p.text('项：'),p.get('ItemsView','Selection'))))),
        p.event('AddButton','Click',p.iff(empty(p,p.trim(p.get('ItemBox','Text'))),p.set('SelectionLabel','Text',p.text('请先填写物品名称')),p.chain(append(p,p.var('购物清单'),p.trim(p.get('ItemBox','Text'))),p.call('刷新清单'),p.set('ItemBox','Text',p.text('')))))]
    p.class_tops=copy.deepcopy(p.tops[:3])
    return p,dict(work='可追加和选择的购物清单',classroomKept=['global 购物清单','刷新清单','Screen1.Initialize'],classroomTasks=['添加ItemsView.AfterPicking，检查有效索引后显示序号和名称','添加AddButton.Click，非空时追加、刷新、清输入'],screenshotGroups=['刷新清单','ItemsView.AfterPicking','AddButton.Click'],tests=[dict(event='Screen1.Initialize',expect={'CountLabel.Text':'物品数：3'}),dict(set={'ItemsView.SelectionIndex':2,'ItemsView.Selection':'面包'},event='ItemsView.AfterPicking',expect={'SelectionLabel.Text':'第2项：面包'}),dict(set={'ItemBox.Text':'牛奶'},event='AddButton.Click',expect={'global 购物清单':['水','面包','苹果','牛奶'],'ItemBox.Text':'','CountLabel.Text':'物品数：4'}),dict(set={'ItemBox.Text':'   '},event='AddButton.Click',expect={'CountLabel.Text':'物品数：3','SelectionLabel.Text':'请先填写物品名称'})])


def build30():
    p=base(30,'YXCourse30','信息的增加、修改与删除')
    p.screen([p.page(intro(p,'我的待办编辑器','第 30 课｜先选择，再修改或删除')+[
        view(p,'TodoView'),p.comp('TaskBox','TextBox',Hint='任务内容',Text='',Width=-2,Height=52,FontSize=20,BackgroundColor='&HFFFFFFFF'),
        p.button('AddButton','新增任务'),p.comp('EditRow','HorizontalArrangement',[p.button('UpdateButton','修改选中项',Width=-1050,Enabled='False'),p.button('DeleteButton','删除选中项',Width=-1050,Enabled='False',BackgroundColor='&HFFE4576B')],Width=-2,Height=58),
        p.label('HintLabel','先选择任务，或直接输入新增。',FontSize=19,Height=120)])])
    valid=lambda:p.call('选择有效',names=(),returns=True)
    refresh=p.chain(p.set('TodoView','Elements',p.var('任务')),p.set('TodoView','SelectionIndex',p.num(0)),p.setvar('选中序号',p.num(0)),p.set('TaskBox','Text',p.text('')),p.set('UpdateButton','Enabled',p.boolean(False)),p.set('DeleteButton','Enabled',p.boolean(False)),p.set('HintLabel','Text',p.text('先选择任务，或直接输入新增。')))
    p.tops=[p.global_('任务',lists(p,p.text('整理书包'),p.text('读书20分钟'))),p.global_('选中序号',p.num(0)),p.define('刷新并取消选择',refresh),p.define('选择有效',valid_index(p,lambda:p.var('选中序号'),lambda:p.var('任务')),returns=True),p.event('Screen1','Initialize',p.call('刷新并取消选择')),
        p.event('TodoView','AfterPicking',p.chain(p.setvar('选中序号',p.get('TodoView','SelectionIndex')),p.iff(valid(),p.chain(p.set('TaskBox','Text',item(p,p.var('任务'),p.var('选中序号'))),p.set('UpdateButton','Enabled',p.boolean(True)),p.set('DeleteButton','Enabled',p.boolean(True)),p.set('HintLabel','Text',p.join(p.text('已选择第'),p.var('选中序号'),p.text('项'))))))),
        p.event('AddButton','Click',p.iff(empty(p,p.trim(p.get('TaskBox','Text'))),p.set('HintLabel','Text',p.text('任务内容不能为空')),p.chain(append(p,p.var('任务'),p.trim(p.get('TaskBox','Text'))),p.call('刷新并取消选择'),p.set('HintLabel','Text',p.text('新增成功，已取消选择。'))))),
        p.event('UpdateButton','Click',p.iff(valid(),p.iff(empty(p,p.trim(p.get('TaskBox','Text'))),p.set('HintLabel','Text',p.text('任务内容不能为空')),p.chain(replace(p,p.var('任务'),p.var('选中序号'),p.trim(p.get('TaskBox','Text'))),p.call('刷新并取消选择'),p.set('HintLabel','Text',p.text('修改成功，已取消选择。')))),p.set('HintLabel','Text',p.text('请先选择有效任务')))),
        p.event('DeleteButton','Click',p.iff(valid(),p.chain(remove(p,p.var('任务'),p.var('选中序号')),p.call('刷新并取消选择'),p.set('HintLabel','Text',p.text('删除成功，已取消选择。'))),p.set('HintLabel','Text',p.text('请先选择有效任务'))))]
    p.class_tops=[copy.deepcopy(p.tops[i]) for i in [0,1,2,3,4,6]]
    return p,dict(work='增改删待办列表',classroomKept=['全部变量','刷新并取消选择、选择有效','初始化和新增'],classroomTasks=['TodoView.AfterPicking保存索引并载入内容，启用修改/删除','UpdateButton.Click校验后替换列表项','DeleteButton.Click删除后刷新并取消选择'],screenshotGroups=['TodoView.AfterPicking','UpdateButton.Click','DeleteButton.Click'],tests=[dict(event='UpdateButton.Click',expect={'global 任务':['整理书包','读书20分钟'],'HintLabel.Text':'请先选择有效任务'}),dict(set={'global 选中序号':2,'TaskBox.Text':'读书30分钟'},event='UpdateButton.Click',expect={'global 任务':['整理书包','读书30分钟'],'global 选中序号':0}),dict(set={'global 选中序号':1},events=['DeleteButton.Click','DeleteButton.Click'],expect={'global 任务':['读书20分钟'],'global 选中序号':0})])


def build31():
    p=base(31,'YXCourse31','让题目组成一个题库')
    p.screen([p.page(intro(p,'知识闯关小题库','第 31 课｜同一题号连接问题、答案与解释')+[
        p.label('QuestionLabel','准备抽题…',FontSize=25,FontBold='True',Height=115,BackgroundColor='&HFFFFFFFF'),p.comp('AnswerBox','TextBox',Hint='输入答案',Text='',Width=-2,Height=52,FontSize=21,BackgroundColor='&HFFFFFFFF'),
        p.comp('QuizButtons','HorizontalArrangement',[p.button('SubmitButton','提交答案',Width=-1050),p.button('NextButton','抽下一题',Width=-1050,BackgroundColor='&HFFDCEFFF',TextColor='&HFF123E62')],Width=-2,Height=58),
        p.label('ExplainLabel','每题只能提交一次；下一题可能重复抽到。',FontSize=20,Height=150),p.label('ScoreLabel','累计答对：0',FontSize=23,FontBold='True',Height=55),p.label('HintLabel','参考题采用精确文字匹配：东、7、冰；修改题库时同步修改三组列表。',FontSize=14,TextColor='&HFF56758B')])])
    def draw(random=True):return p.chain(p.setvar('题号',p.random(p.num(1),length(p,p.var('题目'))) if random else p.num(1)),p.set('QuestionLabel','Text',item(p,p.var('题目'),p.var('题号'))),p.setvar('已提交',p.boolean(False)),p.set('AnswerBox','Text',p.text('')),p.set('ExplainLabel','Text',p.text('请输入答案，每题只计分一次。')),p.set('SubmitButton','Enabled',p.boolean(True)))
    correct=lambda:p.eq(p.trim(p.get('AnswerBox','Text')),item(p,p.var('答案'),p.var('题号')))
    check=p.iff(negate(p,p.var('已提交')),p.chain(p.iff(correct(),p.setvar('得分',p.add(p.var('得分'),p.num(1)))),p.set('ExplainLabel','Text',p.join(choose(p,correct(),p.text('答对了！'),p.text('再想一想。')),p.text('\n参考答案：'),item(p,p.var('答案'),p.var('题号')),p.text('\n'),item(p,p.var('解释'),p.var('题号')))),p.set('ScoreLabel','Text',p.join(p.text('累计答对：'),p.var('得分'))),p.setvar('已提交',p.boolean(True)),p.set('SubmitButton','Enabled',p.boolean(False))))
    valid=p.both(p.cmp('GT',length(p,p.var('题目')),p.num(0)),p.both(p.cmp('EQ',length(p,p.var('题目')),length(p,p.var('答案'))),p.cmp('EQ',length(p,p.var('题目')),length(p,p.var('解释')))))
    p.tops=[p.global_('题目',lists(p,*[p.text(x) for x in ['太阳从哪边升起','一周有几天','水结冰后叫作什么']])),p.global_('答案',lists(p,p.text('东'),p.text('7'),p.text('冰'))),p.global_('解释',lists(p,*[p.text(x) for x in ['地球自转带来日出方向','一周按七天计算','冰是水的固态']])),p.global_('题号',p.num(1)),p.global_('得分',p.num(0)),p.global_('已提交',p.boolean(False)),
        p.define('抽题',draw()),p.define('检查答案',check),p.event('Screen1','Initialize',p.iff(valid,p.call('抽题'),p.chain(p.set('ExplainLabel','Text',p.text('题库错误：题目不能为空，三组列表长度须相同。')),p.set('SubmitButton','Enabled',p.boolean(False)),p.set('NextButton','Enabled',p.boolean(False))))),
        p.event('SubmitButton','Click',p.iff(negate(p,p.var('已提交')),p.iff(empty(p,p.trim(p.get('AnswerBox','Text'))),p.set('ExplainLabel','Text',p.text('请先输入答案')),p.call('检查答案')))),p.event('NextButton','Click',p.call('抽题'))]
    p.class_tops=copy.deepcopy(p.tops[:6])+[p.note(p.define('抽题',draw(False)),'课堂任务：把固定题号1改为1..题目长度的随机整数。'),p.note(p.define('检查答案',p.set('ExplainLabel','Text',p.text('课堂任务：比较答案、显示解释、计分并锁定提交。'))),'本过程待补齐。')]+copy.deepcopy(p.tops[8:])
    return p,dict(work='三题随机抽题与单次判分',classroomKept=['六个全局变量','初始化题库等长与非空检查','按钮入口与空输入保护','抽题固定1、检查答案占位'],classroomTasks=['抽题的题号随机1..列表长度','检查答案使用同一题号取答案和解释','判题后已提交True并禁用提交，抽题时恢复'],screenshotGroups=['抽题','SubmitButton.Click','NextButton.Click'],tests=[dict(set={'global 题号':2,'AnswerBox.Text':'7'},events=['SubmitButton.Click','SubmitButton.Click'],expect={'global 得分':1,'global 已提交':True,'SubmitButton.Enabled':False},contains={'ExplainLabel.Text':['一周按七天计算']}),dict(set={'AnswerBox.Text':'   '},event='SubmitButton.Click',expect={'global 已提交':False,'global 得分':0,'ExplainLabel.Text':'请先输入答案'}),dict(event='NextButton.Click',expect={'AnswerBox.Text':'','global 已提交':False,'SubmitButton.Enabled':True})])


def build32():
    p=base(32,'YXCourse32','用字典描述一条记录')
    p.screen([p.page(intro(p,'校园植物观察卡','第 32 课｜字段有名字，记录更清楚')+[
        view(p,'PlantView',140),p.label('NameLabel','名称：未选择',FontSize=23,Height=50),p.label('PlaceLabel','地点：—',FontSize=20,Height=50),
        p.comp('FeatureBox','TextBox',Text='',Hint='观察到的特征',MultiLine='True',Width=-2,Height=100,FontSize=20,BackgroundColor='&HFFFFFFFF'),p.button('SaveButton','保存所选植物的特征'),p.label('HintLabel','先从列表选择一种植物。',FontSize=18,Height=110)])])
    records=lists(p,dictionary(p,名称=p.text('桂花'),地点=p.text('校门旁'),特征=p.text('小花成簇')),dictionary(p,名称=p.text('银杏'),地点=p.text('操场边'),特征=p.text('扇形叶')))
    valid=lambda:valid_index(p,lambda:p.var('选中序号'),lambda:p.var('记录'))
    show=p.iff(valid_index(p,lambda:p.param('序号'),lambda:p.var('记录')),p.chain(p.setvar('当前记录',item(p,p.var('记录'),p.param('序号'))),p.set('NameLabel','Text',p.join(p.text('名称：'),lookup(p,p.var('当前记录'),'名称'))),p.set('PlaceLabel','Text',p.join(p.text('地点：'),lookup(p,p.var('当前记录'),'地点'))),p.set('FeatureBox','Text',lookup(p,p.var('当前记录'),'特征')),p.set('HintLabel','Text',p.text('可编辑特征；本课修改仅保留在运行中。'))))
    p.tops=[p.global_('记录',records),p.global_('选中序号',p.num(0)),p.global_('显示名称',lists(p)),p.global_('当前记录',dictionary(p)),
        p.define('刷新名称',p.chain(p.setvar('显示名称',lists(p)),foreach(p,'植物',p.var('记录'),append(p,p.var('显示名称'),lookup(p,p.param('植物'),'名称'))),p.set('PlantView','Elements',p.var('显示名称')))),p.define('显示记录',show,args=('序号',)),
        p.define('保存特征',p.iff(valid(),p.iff(empty(p,p.trim(p.get('FeatureBox','Text'))),p.set('HintLabel','Text',p.text('特征不能为空')),p.chain(setkey(p,item(p,p.var('记录'),p.var('选中序号')),'特征',p.trim(p.get('FeatureBox','Text'))),p.call('显示记录',p.var('选中序号'),names=('序号',)),p.set('HintLabel','Text',p.text('已更新这一条记录的特征。')))),p.set('HintLabel','Text',p.text('请先选择植物')))),
        p.event('Screen1','Initialize',p.call('刷新名称')),p.event('PlantView','AfterPicking',p.chain(p.setvar('选中序号',p.get('PlantView','SelectionIndex')),p.call('显示记录',p.var('选中序号'),names=('序号',)))),p.event('SaveButton','Click',p.call('保存特征'))]
    p.class_tops=copy.deepcopy(p.tops[:5])+[p.note(p.define('显示记录',p.set('HintLabel','Text',p.text('课堂任务：按名称、地点、特征键显示记录。')),args=('序号',)),'缺键时使用未填写作为默认值。'),p.note(p.define('保存特征',p.set('HintLabel','Text',p.text('课堂任务：更新所选字典的特征键。'))),'先检查有效索引和非空特征。')]+copy.deepcopy(p.tops[7:])
    return p,dict(work='列表中存放植物字典并编辑字段',classroomKept=['两条植物字典及辅助变量','刷新名称和全部事件入口','显示记录、保存特征的占位过程'],classroomTasks=['显示记录按键读取，缺键显示未填写','保存特征只更改选中的那一份字典','验证另一条记录不受影响'],screenshotGroups=['刷新名称','显示记录','保存特征'],tests=[dict(set={'PlantView.SelectionIndex':2},event='PlantView.AfterPicking',expect={'NameLabel.Text':'名称：银杏','PlaceLabel.Text':'地点：操场边','FeatureBox.Text':'扇形叶'}),dict(set={'global 选中序号':1,'FeatureBox.Text':'有香味'},event='SaveButton.Click',expect={'FeatureBox.Text':'有香味'}),dict(set={'global 记录':[{'名称':'无特征植物','地点':'花坛'}]},procedure='显示记录',args=[1],expect={'FeatureBox.Text':'未填写'})])


def build33():
    p=base(33,'YXCourse33','关闭 APP 后还能记住')
    p.screen([p.page(intro(p,'我的阅读打卡本','第 33 课｜运行状态写进本地数据库')+[
        p.comp('BookBox','TextBox',Text='',Hint='读了哪本书或哪一章？',Width=-2,Height=55,FontSize=20,BackgroundColor='&HFFFFFFFF'),box(p,'MinutesBox','本次1～240分钟'),p.button('SaveButton','打卡并保存'),
        p.label('TotalLabel','累计阅读：0 分钟',FontSize=26,FontBold='True',Height=85),p.label('LastLabel','最近内容：暂无记录',FontSize=21,Height=110,BackgroundColor='&HFFFFFFFF'),
        p.button('ResetButton','清空本课阅读记录',BackgroundColor='&HFFDCEFFF',TextColor='&HFF123E62'),p.label('StatusLabel','仅清理YXCourse33命名空间下两个阅读标签。',FontSize=15,Height=90)]),p.comp('LocalDB','TinyDB',Namespace='YXCourse33')])
    refresh=p.chain(p.set('TotalLabel','Text',p.join(p.text('累计阅读：'),p.var('累计分钟'),p.text(' 分钟'))),p.set('LastLabel','Text',p.join(p.text('最近内容：'),choose(p,empty(p,p.var('最近内容')),p.text('暂无记录'),p.var('最近内容')))))
    valid=p.both(integer(p,numeric_text(p,'MinutesBox')),p.both(p.cmp('GTE',numeric_text(p,'MinutesBox'),p.num(1)),p.cmp('LTE',numeric_text(p,'MinutesBox'),p.num(240))))
    save=p.iff(empty(p,p.trim(p.get('BookBox','Text'))),p.set('StatusLabel','Text',p.text('请先填写阅读内容')),p.iff(p.isnum(numeric_text(p,'MinutesBox')),p.iff(valid,p.chain(p.setvar('累计分钟',p.add(p.var('累计分钟'),numeric_text(p,'MinutesBox'))),p.setvar('最近内容',p.trim(p.get('BookBox','Text'))),p.call('保存阅读'),p.set('MinutesBox','Text',p.text('')),p.set('StatusLabel','Text',p.text('本次阅读已保存在本机。'))),p.set('StatusLabel','Text',p.text('分钟须为1～240的整数'))),p.set('StatusLabel','Text',p.text('分钟须为1～240的整数'))))
    p.tops=[p.global_('累计分钟',p.num(0)),p.global_('最近内容',p.text('')),p.define('刷新阅读',refresh),p.define('保存阅读',p.chain(p.method('LocalDB','StoreValue',p.text('totalMinutes'),p.var('累计分钟')),p.method('LocalDB','StoreValue',p.text('lastBook'),p.var('最近内容')),p.call('刷新阅读'))),
        p.define('恢复阅读',p.chain(p.setvar('累计分钟',p.method('LocalDB','GetValue',p.text('totalMinutes'),p.num(0))),p.setvar('最近内容',p.method('LocalDB','GetValue',p.text('lastBook'),p.text(''))),p.call('刷新阅读'))),p.event('Screen1','Initialize',p.call('恢复阅读')),p.event('SaveButton','Click',save),
        p.event('ResetButton','Click',p.chain(p.method('LocalDB','ClearTag',p.text('totalMinutes')),p.method('LocalDB','ClearTag',p.text('lastBook')),p.setvar('累计分钟',p.num(0)),p.setvar('最近内容',p.text('')),p.call('刷新阅读'),p.set('StatusLabel','Text',p.text('本课两个阅读标签已清空。'))))]
    p.class_tops=copy.deepcopy(p.tops[:3])+[p.note(p.define('保存阅读',p.call('刷新阅读')),'课堂任务：在刷新前StoreValue保存两个指定标签。')]+copy.deepcopy(p.tops[4:7])
    return p,dict(work='TinyDB阅读持久化',classroomKept=['全部变量','刷新阅读、恢复阅读','输入校验与Save按钮调用','保存阅读占位仅刷新显示'],classroomTasks=['保存阅读加入totalMinutes、lastBook的StoreValue','添加ResetButton.Click，ClearTag后重置变量与显示','模拟重开并比较首次默认和旧记录'],screenshotGroups=['恢复阅读','SaveButton.Click','ResetButton.Click'],tests=[dict(event='Screen1.Initialize',expect={'global 累计分钟':0,'LastLabel.Text':'最近内容：暂无记录'}),dict(set={'BookBox.Text':'第一本','MinutesBox.Text':'20'},event='SaveButton.Click',expect={'global 累计分钟':20},stores={'totalMinutes':20,'lastBook':'第一本'}),dict(set={'BookBox.Text':'一本书','MinutesBox.Text':'0'},event='SaveButton.Click',expect={'global 累计分钟':0}),dict(event='ResetButton.Click',expect={'global 累计分钟':0,'global 最近内容':''},clearedTags=['totalMinutes','lastBook'])],limitations=['Android真实TinyDB跨进程持久化没有进行真机重启实测；编译与事件逻辑另行验证'])


def build34():
    p=base(34,'YXCourse34','找到我需要的信息')
    p.screen([p.page(intro(p,'本地图书查找器','第 34 课｜筛选结果仍要找到原始记录')+[
        p.comp('SearchBox','TextBox',Text='',Hint='书名关键词，空白显示全部',Width=-2,Height=55,FontSize=20,BackgroundColor='&HFFFFFFFF'),p.button('SearchButton','查找书名'),p.label('CountLabel','结果：0 项',FontSize=18,Height=45),
        view(p,'ResultsView',220),p.label('DetailLabel','',FontSize=21,Height=130),p.label('HintLabel','英文关键词忽略大小写。本课数据只在本机，不需要联网。',FontSize=14,TextColor='&HFF56758B')])])
    books=lists(p,dictionary(p,书名=p.text('神奇校车'),分类=p.text('科普'),编号=p.text('A01')),dictionary(p,书名=p.text('小王子'),分类=p.text('故事'),编号=p.text('B02')),dictionary(p,书名=p.text('Scratch创意编程'),分类=p.text('编程'),编号=p.text('C03')))
    source=lambda:item(p,p.var('图书'),p.param('i'))
    match=either(p,empty(p,p.trim(p.param('关键词'))),contains(p,lower(p,lookup(p,source(),'书名')),lower(p,p.trim(p.param('关键词')))))
    filterbody=p.chain(p.setvar('结果索引',lists(p)),p.setvar('结果书名',lists(p)),p.set('DetailLabel','Text',p.text('')),p.forrange('i',p.num(1),length(p,p.var('图书')),p.num(1),p.iff(match,p.chain(append(p,p.var('结果索引'),p.param('i')),append(p,p.var('结果书名'),lookup(p,source(),'书名'))))),p.set('ResultsView','Elements',p.var('结果书名')),p.set('ResultsView','SelectionIndex',p.num(0)),p.set('CountLabel','Text',p.join(p.text('结果：'),length(p,p.var('结果索引')),p.text(' 项'))),p.iff(p.cmp('EQ',length(p,p.var('结果索引')),p.num(0)),p.set('DetailLabel','Text',p.text('未找到匹配书名，请换一个关键词。'))))
    detail=p.iff(valid_index(p,lambda:p.get('ResultsView','SelectionIndex'),lambda:p.var('结果索引')),p.chain(p.setvar('原始序号',item(p,p.var('结果索引'),p.get('ResultsView','SelectionIndex'))),p.set('DetailLabel','Text',p.join(p.text('分类：'),lookup(p,item(p,p.var('图书'),p.var('原始序号')),'分类'),p.text('\n编号：'),lookup(p,item(p,p.var('图书'),p.var('原始序号')),'编号')))))
    p.tops=[p.global_('图书',books),p.global_('结果索引',lists(p)),p.global_('结果书名',lists(p)),p.global_('原始序号',p.num(0)),p.define('筛选',filterbody,args=('关键词',)),p.define('显示结果详情',detail),p.event('Screen1','Initialize',p.call('筛选',p.text(''),names=('关键词',))),p.event('SearchButton','Click',p.chain(p.set('DetailLabel','Text',p.text('')),p.call('筛选',p.get('SearchBox','Text'),names=('关键词',)))),p.event('ResultsView','AfterPicking',p.call('显示结果详情'))]
    p.class_tops=copy.deepcopy(p.tops[:4])+[p.note(p.define('筛选',p.chain(p.setvar('结果索引',lists(p)),p.setvar('结果书名',lists(p)),p.set('ResultsView','Elements',p.var('结果书名')),p.set('CountLabel','Text',p.text('课堂任务：遍历并筛选书名'))),args=('关键词',)),'补上匹配遍历、原始索引、结果显示与0项提示。'),p.note(p.define('显示结果详情',p.set('DetailLabel','Text',p.text('课堂任务：先映射原序号，再读取字典字段。'))),'不要直接用结果中的第1项索引读取原表。')]+copy.deepcopy(p.tops[6:])
    return p,dict(work='大小写无关的关键词筛选与结果索引映射',classroomKept=['三条图书字典和辅助变量','初始化、搜索、选择事件入口','筛选与显示详情占位'],classroomTasks=['筛选过程实现trim/lower、contains和原序号收集','详情先读取结果索引再查原表','数量0时清旧详情并提示未找到'],screenshotGroups=['筛选','显示结果详情','SearchButton.Click'],tests=[dict(set={'SearchBox.Text':'scratch'},event='SearchButton.Click',expect={'global 结果索引':[3],'CountLabel.Text':'结果：1 项'}),dict(set={'global 结果索引':[3],'ResultsView.SelectionIndex':1},procedure='显示结果详情',expect={'DetailLabel.Text':'分类：编程\n编号：C03'}),dict(set={'SearchBox.Text':'   '},event='SearchButton.Click',expect={'global 结果索引':[1,2,3]}),dict(set={'SearchBox.Text':'不存在'},event='SearchButton.Click',expect={'global 结果索引':[],'CountLabel.Text':'结果：0 项','DetailLabel.Text':'未找到匹配书名，请换一个关键词。'})])


def build35():
    p=base(35,'YXCourse35','数据导入、导出与分享')
    p.assets['reading-example.csv']='title,minutes\r\n小王子,20\r\n"地球,我们的家",15\r\n"他说""你好""",10\r\n'.encode('utf-8')
    p.assets['reading-invalid.csv']='title,minutes\r\n小王子,20\r\n坏记录,abc\r\n'.encode('utf-8')
    p.screen([p.page(intro(p,'阅读备份工具','第 35 课｜先完整校验，再替换记录')+[
        view(p,'RowsView',125),p.comp('PreviewBox','TextBox',MultiLine='True',Text='',Hint='导出后显示CSV，也可粘贴待导入文本',Width=-2,Height=190,FontSize=17,BackgroundColor='&HFFFFFFFF'),p.button('ExportButton','生成CSV并保存备份'),p.button('ImportButton','验证并导入上方CSV'),p.button('ShareButton','分享已保存备份',Enabled='False',BackgroundColor='&HFFDCEFFF',TextColor='&HFF123E62'),p.label('StatusLabel','表头须为title,minutes；分钟为1～240整数。',FontSize=17,Height=100)]),p.comp('BackupFile','File',DefaultScope='App'),p.comp('Share1','Sharing')])
    refresh=p.chain(p.setvar('显示记录',lists(p)),foreach(p,'行',p.var('记录'),append(p,p.var('显示记录'),p.join(item(p,p.param('行'),p.num(1)),p.text('｜'),item(p,p.param('行'),p.num(2)),p.text('分钟')))),p.set('RowsView','Elements',p.var('显示记录')))
    invalidate=lambda:p.chain(p.setvar('导出完成',p.boolean(False)),p.set('ShareButton','Enabled',p.boolean(False)))
    export=p.chain(p.setvar('导出表',lists(p,lists(p,p.text('title'),p.text('minutes')))),foreach(p,'行',p.var('记录'),append(p,p.var('导出表'),p.param('行'))),p.set('PreviewBox','Text',p.b('lists_to_csv_table',values={'LIST':p.var('导出表')})),invalidate(),p.setvar('写入中',p.boolean(True)),p.set('ExportButton','Enabled',p.boolean(False)),p.set('ImportButton','Enabled',p.boolean(False)),p.set('StatusLabel','Text',p.text('正在写入App作用域reading.csv…')),p.method('BackupFile','SaveFile',p.get('PreviewBox','Text'),p.text('reading.csv')))
    row=lambda:p.param('当前行')
    fail=lambda text:localset(p,'错误',p.join(p.text('第'),p.param('i'),p.text('行：'+text)))
    minutes=lambda:p.trim(item(p,row(),p.num(2)))
    numeric_valid=p.both(integer(p,minutes()),p.both(p.cmp('GTE',minutes(),p.num(1)),p.cmp('LTE',minutes(),p.num(240))))
    rowcheck=p.iff(islist(p,row()),p.iff(p.cmp('EQ',length(p,row()),p.num(2)),p.iff(empty(p,p.trim(item(p,row(),p.num(1)))),fail('书名不能为空'),p.iff(p.isnum(minutes()),p.iff(numeric_valid,append(p,p.param('临时表'),lists(p,p.trim(item(p,row(),p.num(1))),p.add(minutes(),p.num(0)))),fail('分钟须为1～240整数')),fail('分钟须为1～240整数'))),fail('须恰好有两列')),fail('不是列表'))
    rows=p.forrange('i',p.num(2),length(p,p.param('表')),p.num(1),local_decl(p,[('当前行',item(p,p.param('表'),p.param('i')))],rowcheck))
    header=lambda:item(p,p.param('表'),p.num(1))
    badheader=lambda:localset(p,'错误',p.text('表头须完全匹配title,minutes'))
    headercheck=p.iff(islist(p,header()),p.iff(p.cmp('EQ',length(p,header()),p.num(2)),p.iff(p.both(p.eq(item(p,header(),p.num(1)),p.text('title')),p.eq(item(p,header(),p.num(2)),p.text('minutes'))),rows,badheader()),badheader()),badheader())
    validation=local_decl(p,[('临时表',lists(p)),('错误',p.text(''))],do_return(p,p.iff(islist(p,p.param('表')),p.iff(p.cmp('GTE',length(p,p.param('表')),p.num(1)),headercheck,badheader()),badheader()),choose(p,empty(p,p.param('错误')),p.param('临时表'),p.param('错误'))),returns=True)
    importbody=p.iff(negate(p,p.var('写入中')),p.chain(p.setvar('导入结果',p.call('验证导入',p.b('lists_from_csv_table',values={'TEXT':p.get('PreviewBox','Text')}),names=('表',),returns=True)),p.iff(islist(p,p.var('导入结果')),p.chain(p.setvar('记录',p.var('导入结果')),p.call('刷新记录'),invalidate(),p.set('StatusLabel','Text',p.join(p.text('导入成功：'),length(p,p.var('记录')),p.text('条；重新导出后再分享。')))),p.set('StatusLabel','Text',p.var('导入结果')))))
    aftersave=p.iff(p.var('写入中'),p.chain(p.setvar('写入中',p.boolean(False)),p.setvar('导出完成',p.boolean(True)),p.setvar('备份路径',p.method('BackupFile','MakeFullPath',p.b('helpers_dropdown',{'OPTION':'App'},mutation={'key':'FileScope','value':'App'}),p.text('reading.csv'))),p.set('ShareButton','Enabled',p.boolean(True)),p.set('ExportButton','Enabled',p.boolean(True)),p.set('ImportButton','Enabled',p.boolean(True)),p.set('StatusLabel','Text',p.text('reading.csv已保存，可以分享。'))))
    p.tops=[p.global_('记录',lists(p,lists(p,p.text('小王子'),p.num(20)),lists(p,p.text('地球,我们的家'),p.num(15)))),p.global_('导出完成',p.boolean(False)),p.global_('写入中',p.boolean(False)),p.global_('备份路径',p.text('')),p.global_('显示记录',lists(p)),p.global_('导出表',lists(p)),p.global_('导入结果',p.text('')),p.define('刷新记录',refresh),p.define('导出CSV',export),p.define('验证导入',validation,args=('表',),returns=True),p.event('Screen1','Initialize',p.call('刷新记录')),p.event('ExportButton','Click',p.iff(negate(p,p.var('写入中')),p.call('导出CSV'))),p.event('ImportButton','Click',importbody),p.event('BackupFile','AfterFileSaved',aftersave),p.event('ShareButton','Click',p.iff(p.var('导出完成'),p.method('Share1','ShareFile',p.var('备份路径')))),p.event('Screen1','ErrorOccurred',p.chain(p.setvar('写入中',p.boolean(False)),invalidate(),p.set('ExportButton','Enabled',p.boolean(True)),p.set('ImportButton','Enabled',p.boolean(True)),p.set('StatusLabel','Text',p.join(p.text('格式或文件错误，原记录保留：'),p.param('message',True)))))]
    p.class_tops=copy.deepcopy(p.tops[:8])+[p.note(p.define('导出CSV',p.set('StatusLabel','Text',p.text('课堂任务：构造表头、转CSV并保存文件。'))),'不要手工split逗号。'),p.note(p.define('验证导入',p.text('课堂任务：在局部临时表中逐行校验'),args=('表',),returns=True),'全部合法返回列表，否则返回错误文字。')]+[copy.deepcopy(p.tops[i]) for i in [10,11,12,14,15]]
    return p,dict(work='CSV原子导入、App文件备份与分享',classroomKept=['示例记录、辅助变量与刷新记录','全部操作入口、导入提交的类型保护和分享保护','导出CSV与验证导入占位；错误恢复'],classroomTasks=['用原生CSV转换而非手工逗号分割','验证导入使用局部临时表，全部成功才返回列表','补BackupFile.AfterFileSaved，MakeFullPath后启用分享'],screenshotGroups=['导出CSV','验证导入','BackupFile.AfterFileSaved'],tests=[dict(procedure='验证导入',args=[[['title','minutes'],['地球,我们的家','15']]],returns=[['地球,我们的家',15]]),dict(procedure='验证导入',args=[[['title','minutes'],['坏记录','abc']]],returns='第2行：分钟须为1～240整数'),dict(procedure='验证导入',args=[[['title','minutes']]],returns=[]),dict(event='ShareButton.Click',methodCounts={'Share1.ShareFile':0}),dict(set={'global 写入中':True},event='BackupFile.AfterFileSaved',args={'fileName':'reading.csv'},expect={'global 导出完成':True,'ShareButton.Enabled':True,'ExportButton.Enabled':True})],implementationNotes=['局部临时表避免校验过程中改动正式记录','MakeFullPath使用FileScope.App枚举，分享按钮在AfterFileSaved后启用','写文件时禁止导入或重复导出，避免并发覆盖备份内容'],limitations=['Android文件作用域和系统分享面板未进行真机操作实测'])


def build36():
    p=base(36,'YXCourse36','让数据讲故事')
    p.screen([p.page(intro(p,'一周阅读仪表板','第 36 课｜同一份数据，图表和统计一起变化')+[
        p.comp('ReadingChart','Chart',[p.comp('Bars','ChartData2D',Color='&HFF1388CC',Label='阅读分钟')],Width=-2,Height=270,Type=3,Description='一周阅读分钟数',LegendEnabled='False',YFromZero='True',XFromZero='True',BackgroundColor='&HFFFFFFFF',LabelsFromString='周一,周二,周三,周四,周五,周六,周日'),
        p.comp('DayPicker','ListPicker',Text='选择日期：周一',Title='选择要更新的日期',Width=-2,Height=52,FontSize=18,ElementsFromString='周一,周二,周三,周四,周五,周六,周日',BackgroundColor='&HFF1388CC',TextColor='&HFFFFFFFF'),box(p,'MinuteBox','当日0～240分钟',Text='20'),p.button('UpdateButton','更新这一天'),
        p.label('SummaryLabel','等待统计…',FontSize=21,Height=160,BackgroundColor='&HFFFFFFFF'),p.label('HintLabel','最高日并列时显示最先出现的一天；日均按全部7天计算。',FontSize=14,TextColor='&HFF56758B')])])
    current=lambda:item(p,p.var('分钟'),p.param('i'))
    stat=p.chain(p.setvar('总计',p.num(0)),p.setvar('最高值',p.num(-1)),p.setvar('最高日',p.num(1)),p.forrange('i',p.num(1),p.num(7),p.num(1),p.chain(p.setvar('总计',p.add(p.var('总计'),current())),p.iff(p.cmp('GT',current(),p.var('最高值')),p.chain(p.setvar('最高值',current()),p.setvar('最高日',p.param('i')))))),
        p.set('SummaryLabel','Text',p.join(p.text('总计：'),p.var('总计'),p.text(' 分钟\n日均：'),p.b('math_format_as_decimal',values={'NUM':p.div(p.var('总计'),p.num(7)),'PLACES':p.num(1)}),p.text(' 分钟（7天）\n最高：'),item(p,p.var('日期'),p.var('最高日')),p.text(' '),p.var('最高值'),p.text(' 分钟'))))
    # Chart labels are zero-indexed.  List positions remain one-indexed, so the
    # numeric chart x is i-1; this avoids shifting Monday's bar to Tuesday.
    chart=p.chain(p.method('Bars','Clear'),p.set('ReadingChart','Labels',p.var('日期')),p.forrange('i',p.num(1),p.num(7),p.num(1),p.method('Bars','AddEntry',p.sub(p.param('i'),p.num(1)),current())))
    valid=p.both(integer(p,numeric_text(p,'MinuteBox')),p.both(p.cmp('GTE',numeric_text(p,'MinuteBox'),p.num(0)),p.cmp('LTE',numeric_text(p,'MinuteBox'),p.num(240))))
    update=p.iff(p.isnum(numeric_text(p,'MinuteBox')),p.iff(valid,p.chain(replace(p,p.var('分钟'),p.var('选中日'),p.add(numeric_text(p,'MinuteBox'),p.num(0))),p.call('刷新统计'),p.call('刷新图表')),p.set('SummaryLabel','Text',p.text('分钟须为0～240的整数'))),p.set('SummaryLabel','Text',p.text('分钟须为0～240的整数')))
    p.tops=[p.global_('分钟',lists(p,*[p.num(x) for x in [20,15,0,30,25,10,40]])),p.global_('日期',lists(p,*[p.text(x) for x in ['周一','周二','周三','周四','周五','周六','周日']])),p.global_('选中日',p.num(1)),p.global_('总计',p.num(0)),p.global_('最高值',p.num(0)),p.global_('最高日',p.num(1)),p.define('刷新统计',stat),p.define('刷新图表',chart),p.define('更新一天',update),
        p.event('Screen1','Initialize',p.chain(p.call('刷新统计'),p.call('刷新图表'))),p.event('DayPicker','BeforePicking',p.set('DayPicker','Elements',p.var('日期'))),p.event('DayPicker','AfterPicking',p.iff(valid_index(p,lambda:p.get('DayPicker','SelectionIndex'),lambda:p.var('日期')),p.chain(p.setvar('选中日',p.get('DayPicker','SelectionIndex')),p.set('MinuteBox','Text',item(p,p.var('分钟'),p.var('选中日'))),p.set('DayPicker','Text',p.join(p.text('选择日期：'),item(p,p.var('日期'),p.var('选中日'))))))),p.event('UpdateButton','Click',p.call('更新一天'))]
    p.class_tops=copy.deepcopy(p.tops[:6])+[p.note(p.define('刷新统计',p.set('SummaryLabel','Text',p.text('课堂任务：累加、平均与最高日。'))),'日均按7天，不把0分钟日期排除。'),p.note(p.define('刷新图表',p.method('Bars','Clear')),'在Clear后循环添加七个点，X为i-1，对应七天标签。')]+copy.deepcopy(p.tops[8:])
    return p,dict(work='柱状图与7天阅读统计',classroomKept=['七天数据及所有辅助变量','日期选择、更新校验和事件入口','刷新统计占位、刷新图表仅Clear'],classroomTasks=['刷新统计遍历累加，日均除7，最高并列取第一天','刷新图表Clear后加7个点，列表索引i对应图表X=i-1','修改周三为20，观察图表与统计同步'],screenshotGroups=['刷新统计','刷新图表','UpdateButton.Click'],tests=[dict(event='Screen1.Initialize',expect={'global 总计':140,'global 最高值':40,'global 最高日':7},contains={'SummaryLabel.Text':['日均：20.0','周日 40']},methodCounts={'Bars.AddEntry':7}),dict(set={'global 选中日':3,'MinuteBox.Text':'20'},event='UpdateButton.Click',expect={'global 总计':160}),dict(events=['Screen1.Initialize']*3,methodCounts={'Bars.Clear':3,'Bars.AddEntry':21})],implementationNotes=['Chart.Type=3为Bar，已用本地CommonConstants.jar ChartType字节码核对','日期标签下标0..6，AddEntry的x=i-1；数据列表仍使用1..7索引'],limitations=['未进行Android原生图表渲染实测，图表导入与APK编译由主流程验证'])


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('lessons',nargs='*',type=int,default=list(range(29,37)));args=parser.parse_args()
    for n in args.lessons:
        if n not in range(29,37):parser.error('This module authors lessons29..36')
        emit_project(n,*globals()[f'build{n:02d}']())
