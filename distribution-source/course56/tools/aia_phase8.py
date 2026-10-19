"""One evolving graduation project, 51–56; no simulated persistence claims."""
import argparse
import copy

from aia_core import ROOT
from aia_phase1 import base, intro
from aia_phase2 import integer, numeric_text
from aia_phase3 import lists
from aia_phase4 import choose, empty, negate, emit_project
from aia_phase5 import view,length,item,append,remove,foreach,lookup,setkey,islist,either,dictionary,valid_index


def textlen(p,v):return p.b('text_length',values={'VALUE':v})
def insert(p,items,index,v):return p.b('lists_insert_item',values={'LIST':items,'INDEX':index,'ITEM':v})
def isdict(p,v):return p.b('dictionaries_is_dict',values={'THING':v})


def build(number):
    p=base(number,f'YXCourse{number:02d}',{51:'发现问题，确定选题',52:'设计界面与操作流程',53:'搭建项目基础版本',54:'实现核心功能',55:'同伴测试与迭代',56:'作品发布与成果展示'}[number])
    advanced=number>=53;persist=number>=54;safe=number>=55;export=number>=56
    edit=[p.comp('BookBox','TextBox',Text='',Hint='例如：小王子',Width=-2,Height=55,FontSize=20,BackgroundColor='&HFFFFFFFF'),p.comp('TargetBox','TextBox',Text='20',Hint='目标分钟',NumbersOnly='True',Width=-2,Height=55,FontSize=20,BackgroundColor='&HFFFFFFFF'),p.button('PreviewButton','预览本次计划')]
    if advanced:edit.append(p.button('AddButton','保存到计划列表'))
    home=[p.label('PlanLabel','先填写一本书和目标分钟，再预览计划。',FontSize=22,Height=120,BackgroundColor='&HFFFFFFFF')]
    if advanced:home += [view(p,'PlansView',230),p.label('DetailLabel','选择计划查看详情。',FontSize=19,Height=110)]
    if persist:home += [p.button('CompleteButton','标记所选计划已完成',Enabled='False'),p.label('StatsLabel','总计划0｜完成0｜已完成目标0分钟',FontSize=18,Height=90)]
    if safe:home += [p.button('DeleteButton','删除选中计划',Enabled='False',BackgroundColor='&HFFE4576B'),p.button('UndoButton','撤销最近一次删除',Enabled='False',BackgroundColor='&HFFDCEFFF',TextColor='&HFF123E62')]
    if export:home += [p.button('ExportButton','生成CSV备份'),p.button('ShareButton','分享已生成的CSV',Enabled='False')]
    stageversion={51:'0.1',52:'0.2',53:'0.3',54:'0.4',55:'0.5',56:'1.0'}[number]
    about=f'阅读搭子 {stageversion}\n用途：把阅读愿望整理为可执行计划。\n作者：请在设计界面填写自己的署名。\n素材：原生组件、用户提供的羽轩品牌logo。\n'+('数据只保存在本机。已完成目标分钟不是实测阅读时长。' if persist else '本阶段仅内存数据，重开不保存。')
    if export:about+='\nCSV包含书名、目标分钟、完成状态；分享前由你选择接收方。未实现CSV导入恢复。'
    if number>=52:
        panels=[p.comp('HomePanel','VerticalArrangement',home,Width=-2,Height=-1,Visible='True'),p.comp('EditPanel','VerticalArrangement',edit,Width=-2,Height=-1,Visible='False'),p.comp('AboutPanel','VerticalArrangement',[p.label('AboutLabel',about,Height=-1,FontSize=17)],Width=-2,Height=-1,Visible='False')]
        nav=p.comp('NavRow','HorizontalArrangement',[p.button('HomeTab','首页',Width=-1033),p.button('EditTab','编辑计划',Width=-1034),p.button('AboutTab','关于',Width=-1033)],Width=-2,Height=56)
        children=intro(p,'阅读搭子',f'第 {number} 课｜连续毕业参考案例 {stageversion}')+[nav]+panels
    else:children=intro(p,'阅读搭子','第 51 课｜一条具体可执行的阅读计划')+edit+home
    children.append(p.label('HintLabel','先输入书名与正整数分钟。',FontSize=16,Height=110,TextColor='&HFF56758B'))
    nonvisual=[]
    if persist:nonvisual.append(p.comp('LocalDB','TinyDB',Namespace='YXReadingBuddy'))
    if safe:nonvisual.append(p.comp('Confirm','Notifier'))
    if export:nonvisual += [p.comp('ExportFile','File',DefaultScope='App'),p.comp('Share1','Sharing')]
    p.screen([p.page(children)]+nonvisual,VersionName=stageversion)
    txt=lambda:p.trim(p.get('BookBox','Text'));mins=lambda:numeric_text(p,'TargetBox')
    goodrange=lambda:p.both(integer(p,mins()),p.both(p.cmp('GTE',mins(),p.num(1)),p.cmp('LTE',mins(),p.num(180) if safe else p.num(1440))))
    # The graduation reference gains strict upper bounds in lesson55; earlier
    # positive integers are bounded to one day for a meaningful runnable app.
    hint=lambda s:p.set('HintLabel','Text',p.text(s))
    valid=p.chain(p.setvar('输入有效',p.boolean(False)),p.iff(empty(p,txt()),hint('请填写阅读内容'),p.iff(p.isnum(mins()),p.iff(goodrange(),p.iff(p.cmp('LTE',textlen(p,txt()),p.num(40 if safe else 100)),p.setvar('输入有效',p.boolean(True)),hint('书名过长，请缩短到40字以内' if safe else '书名请控制在100字以内')),hint('分钟须为1～180的整数' if safe else '分钟须为1～1440的整数')),hint('请输入正整数分钟'))))
    plan=p.chain(p.setvar('当前书名',txt()),p.setvar('目标分钟',p.add(mins(),p.num(0))),p.set('PlanLabel','Text',p.join(p.text('我计划阅读《'),p.var('当前书名'),p.text('》'),p.var('目标分钟'),p.text('分钟'))),hint('这是计划预览；保存到列表需要点击保存。' if advanced else '计划已生成，可以继续修改。'))
    if number>=52:plan=p.chain(plan,p.call('切换页面',p.text('首页'),names=('名称',)))
    p.tops=[p.global_('当前书名',p.text('')),p.global_('目标分钟',p.num(0)),p.global_('输入有效',p.boolean(False)),p.define('校验输入',valid),p.define('生成计划',p.chain(p.call('校验输入'),p.iff(p.var('输入有效'),plan,p.set('PlanLabel','Text',p.text(''))))),p.event('PreviewButton','Click',p.call('生成计划'))]
    if number>=52:
        visibility = [p.set(panel,'Visible',p.eq(p.param('名称'),p.text(name))) for panel,name in [('HomePanel','首页'),('EditPanel','编辑'),('AboutPanel','关于')]]
        navcolors = [p.set(tab,'BackgroundColor',choose(p,p.eq(p.param('名称'),p.text(name)),p.num(-15497012),p.num(-2297857))) for tab,name in [('HomeTab','首页'),('EditTab','编辑'),('AboutTab','关于')]]
        p.tops += [p.global_('页面',p.text('首页')),p.define('切换页面',p.chain(p.setvar('页面',p.param('名称')),*visibility,*navcolors),args=('名称',))]
        p.tops += [p.event(tab,'Click',p.call('切换页面',p.text(name),names=('名称',))) for tab,name in [('HomeTab','首页'),('EditTab','编辑'),('AboutTab','关于')]]
    if advanced:
        p.tops += [p.global_('计划',lists(p)),p.global_('选中序号',p.num(0)),p.global_('显示标题',lists(p)),p.global_('重复未完成',p.boolean(False))]
        idx=lambda:valid_index(p,lambda:p.var('选中序号'),lambda:p.var('计划'))
        record=lambda:item(p,p.var('计划'),p.var('选中序号'))
        refresh=p.chain(p.setvar('显示标题',lists(p)),foreach(p,'记录',p.var('计划'),append(p,p.var('显示标题'),p.join(choose(p,lookup(p,p.param('记录'),'done',p.boolean(False)),p.text('✓ '),p.text('○ ')),lookup(p,p.param('记录'),'title'),p.text(' · '),lookup(p,p.param('记录'),'target',p.num(0)),p.text(' 分钟')))),p.set('PlansView','Elements',p.var('显示标题')),p.set('PlansView','SelectionIndex',p.num(0)),p.setvar('选中序号',p.num(0)),p.set('DetailLabel','Text',p.text('选择计划查看详情。')))
        if persist:refresh=p.chain(refresh,p.set('CompleteButton','Enabled',p.boolean(False)),p.call('刷新统计'))
        if safe:refresh=p.chain(refresh,p.set('DeleteButton','Enabled',p.boolean(False)),p.set('UndoButton','Enabled',p.var('可撤销')))
        show=p.iff(idx(),p.chain(p.set('DetailLabel','Text',p.join(lookup(p,record(),'title'),p.text('\n目标：'),lookup(p,record(),'target',p.num(0)),p.text(' 分钟\n状态：'),choose(p,lookup(p,record(),'done',p.boolean(False)),p.text('已完成'),p.text('未完成')))),p.set('CompleteButton','Enabled',negate(p,lookup(p,record(),'done',p.boolean(False)))) if persist else None,p.set('DeleteButton','Enabled',p.boolean(True)) if safe else None))
        after=lambda:p.call('保存并刷新') if persist else p.call('刷新计划')
        addbody=p.chain(append(p,p.var('计划'),dictionary(p,title=txt(),target=p.add(mins(),p.num(0)),done=p.boolean(False))),after(),p.set('BookBox','Text',p.text('')),p.set('TargetBox','Text',p.text('20')),p.call('切换页面',p.text('首页'),names=('名称',)),hint('计划已保存到本机。' if persist else '计划已加入内存列表；重开不保留。'))
        add=p.chain(p.call('校验输入'),p.iff(p.var('输入有效'),addbody))
        if safe:
            dup=p.chain(p.setvar('重复未完成',p.boolean(False)),foreach(p,'检查项',p.var('计划'),p.iff(p.both(p.eq(lookup(p,p.param('检查项'),'title'),txt()),negate(p,lookup(p,p.param('检查项'),'done',p.boolean(False)))),p.setvar('重复未完成',p.boolean(True)))))
            add=p.chain(p.call('校验输入'),p.iff(p.var('输入有效'),p.chain(dup,p.iff(p.var('重复未完成'),hint('已有同名未完成计划，请先完成或修改书名'),addbody))))
        p.tops += [p.define('刷新计划',refresh),p.define('显示详情',show),p.define('新增计划',add),p.event('AddButton','Click',p.call('新增计划')),p.event('PlansView','AfterPicking',p.chain(p.setvar('选中序号',p.get('PlansView','SelectionIndex')),p.call('显示详情')))]
    if persist:
        stats=p.chain(p.setvar('完成数',p.num(0)),p.setvar('完成目标分钟',p.num(0)),foreach(p,'统计项',p.var('计划'),p.iff(lookup(p,p.param('统计项'),'done',p.boolean(False)),p.chain(p.setvar('完成数',p.add(p.var('完成数'),p.num(1))),p.setvar('完成目标分钟',p.add(p.var('完成目标分钟'),lookup(p,p.param('统计项'),'target',p.num(0))))))),p.set('StatsLabel','Text',p.join(p.text('总计划'),length(p,p.var('计划')),p.text('｜完成'),p.var('完成数'),p.text('\n已完成目标：'),p.var('完成目标分钟'),p.text(' 分钟（非实测时长）'))))
        # Restore validates every record before adopting it, without overwriting
        # an unreadable tag merely by opening the project.
        shape=p.iff(isdict(p,p.param('恢复项')),p.iff(p.isnum(lookup(p,p.param('恢复项'),'target',p.text('invalid'))),p.iff(p.cmp('LTE',lookup(p,p.param('恢复项'),'target',p.num(0)),p.num(0)),p.setvar('恢复有效',p.boolean(False))),p.setvar('恢复有效',p.boolean(False))),p.setvar('恢复有效',p.boolean(False)))
        restore=p.chain(p.setvar('恢复临时',p.method('LocalDB','GetValue',p.text('plansV1'),lists(p))),p.setvar('恢复有效',p.boolean(True)),p.iff(islist(p,p.var('恢复临时')),foreach(p,'恢复项',p.var('恢复临时'),shape),p.setvar('恢复有效',p.boolean(False))),p.iff(p.var('恢复有效'),p.setvar('计划',p.var('恢复临时')),p.chain(p.setvar('计划',lists(p)),hint('本地记录结构异常，未覆盖旧标签，请检查备份。'))),p.call('刷新计划'))
        p.tops += [p.global_('完成数',p.num(0)),p.global_('完成目标分钟',p.num(0)),p.global_('恢复临时',lists(p)),p.global_('恢复有效',p.boolean(True)),p.define('刷新统计',stats),p.define('保存并刷新',p.chain(p.method('LocalDB','StoreValue',p.text('plansV1'),p.var('计划')),p.call('刷新计划'))),p.define('恢复计划',restore),p.define('标记完成',p.iff(idx(),p.iff(negate(p,lookup(p,record(),'done',p.boolean(False))),p.chain(setkey(p,record(),'done',p.boolean(True)),p.call('保存并刷新'),hint('已完成；统计为目标分钟，不是自动计时。'))))),p.event('CompleteButton','Click',p.call('标记完成'))]
    if safe:
        disable=p.chain(*[p.set(n,'Enabled',p.boolean(False)) for n in ['AddButton','CompleteButton','DeleteButton','UndoButton']],p.set('PlansView','Enabled',p.boolean(False)) if 'Enabled' in {x['name'] for x in __import__('aia_core').METADATA['ListView']['blockProperties']} else None)
        enable=p.chain(p.set('AddButton','Enabled',p.boolean(True)),p.set('PlansView','Enabled',p.boolean(True)) if 'Enabled' in {x['name'] for x in __import__('aia_core').METADATA['ListView']['blockProperties']} else None,p.call('刷新计划'))
        # A modal notifier blocks background UI interaction on Android. A
        # snapshot of the selected dictionary additionally protects the target.
        request=p.iff(idx(),p.chain(p.setvar('待删序号',p.var('选中序号')),p.setvar('待删记录',record()),disable,p.method('Confirm','ShowChooseDialog',p.join(p.text('删除《'),lookup(p,record(),'title'),p.text('》？可撤销最近一次删除。')),p.text('确认删除'),p.text('删除'),p.text('取消'),p.boolean(False))))
        delete=p.iff(valid_index(p,lambda:p.var('待删序号'),lambda:p.var('计划')),p.chain(p.setvar('最近删除记录',p.var('待删记录')),p.setvar('最近删除位置',p.var('待删序号')),remove(p,p.var('计划'),p.var('待删序号')),p.setvar('可撤销',p.boolean(True)),p.call('保存并刷新'),hint('已删除，可撤销最近一次。')))
        undo=p.iff(p.var('可撤销'),p.chain(insert(p,p.var('计划'),p.mm('MAX',p.num(1),p.mm('MIN',p.var('最近删除位置'),p.add(length(p,p.var('计划')),p.num(1)))),p.var('最近删除记录')),p.setvar('可撤销',p.boolean(False)),p.call('保存并刷新'),hint('已恢复最近删除的计划。')))
        p.tops += [p.global_('待删序号',p.num(0)),p.global_('待删记录',dictionary(p)),p.global_('最近删除记录',dictionary(p)),p.global_('最近删除位置',p.num(0)),p.global_('可撤销',p.boolean(False)),p.define('请求删除',request),p.define('确认删除',delete),p.define('撤销删除',undo),p.event('DeleteButton','Click',p.call('请求删除')),p.event('Confirm','AfterChoosing',p.chain(p.iff(p.eq(p.param('choice',True),p.text('删除')),p.call('确认删除'),hint('已取消删除，计划保持不变。')),p.setvar('待删序号',p.num(0)),enable)),p.event('UndoButton','Click',p.call('撤销删除'))]
    if export:
        scope=lambda:p.b('helpers_dropdown',{'OPTION':'App'},mutation={'key':'FileScope','value':'App'})
        makecsv=p.chain(p.set('ShareButton','Enabled',p.boolean(False)),p.setvar('导出表',lists(p,lists(p,p.text('title'),p.text('target'),p.text('done')))),foreach(p,'导出项',p.var('计划'),append(p,p.var('导出表'),lists(p,lookup(p,p.param('导出项'),'title'),lookup(p,p.param('导出项'),'target',p.num(0)),choose(p,lookup(p,p.param('导出项'),'done',p.boolean(False)),p.text('true'),p.text('false'))))),p.method('ExportFile','SaveFile',p.b('lists_to_csv_table',values={'LIST':p.var('导出表')}),p.text('reading-buddy.csv')),hint('正在写入CSV，完成后可分享。'))
        p.tops += [p.global_('导出表',lists(p)),p.define('导出作品数据',makecsv),p.event('ExportButton','Click',p.call('导出作品数据')),p.event('ExportFile','AfterFileSaved',p.chain(p.set('ShareButton','Enabled',p.boolean(True)),hint('CSV已生成，包含书名、目标分钟与完成状态。'))),p.event('ShareButton','Click',p.iff(p.get('ShareButton','Enabled'),p.method('Share1','ShareFile',p.method('ExportFile','MakeFullPath',scope(),p.text('reading-buddy.csv'))))),p.event('Screen1','ErrorOccurred',p.chain(p.set('ShareButton','Enabled',p.boolean(False)),p.set('HintLabel','Text',p.join(p.text('本次操作未完成：'),p.param('message',True)))))]
    init=[]
    if number>=52:init.append(p.call('切换页面',p.text('首页'),names=('名称',)))
    if advanced:init.append(p.call('恢复计划') if persist else p.call('刷新计划'))
    if init:p.tops.append(p.event('Screen1','Initialize',p.chain(*init)))
    # Explicit classroom cuts keep all calls bound to working or instructional
    # stubs, rather than leaving invalid sockets in imported projects.
    tasks={51:['校验输入','生成计划'],52:['切换页面'],53:['新增计划','显示详情'],54:['标记完成','保存并刷新','刷新统计'],55:['确认删除','撤销删除'],56:['导出作品数据']}
    p.class_tops=[]
    for top in p.tops:
        fields={f.get('name'):f.text for f in top.findall('field')}
        if top.get('type')=='procedures_defnoreturn' and fields.get('NAME') in tasks[number]:
            name=fields['NAME'];m=top.find('mutation');args=[a.get('name') for a in m.findall('arg')] if m is not None else []
            p.class_tops.append(p.note(p.define(name,hint('课堂任务：补齐'+name+'的逻辑。'),args=args),'根据本课任务单完成；所有参数和调用保留。'))
        else:p.class_tops.append(copy.deepcopy(top))
    captures={51:['PreviewButton.Click','生成计划','校验输入'],52:['切换页面','PreviewButton.Click','AboutTab.Click'],53:['新增计划','刷新计划','PlansView.AfterPicking'],54:['标记完成','保存并刷新','刷新统计'],55:['新增计划','Confirm.AfterChoosing','撤销删除'],56:['导出作品数据','ExportFile.AfterFileSaved','ShareButton.Click']}[number]
    tests=[dict(set={'BookBox.Text':'小王子','TargetBox.Text':'20'},event='PreviewButton.Click',expect={'PlanLabel.Text':'我计划阅读《小王子》20分钟'}),dict(set={'BookBox.Text':'   ','TargetBox.Text':'20'},event='PreviewButton.Click',expect={'HintLabel.Text':'请填写阅读内容'}),dict(set={'BookBox.Text':'小王子','TargetBox.Text':'0'},event='PreviewButton.Click',expect={'global 输入有效':False})]
    if number>=52:tests.append(dict(event='AboutTab.Click',expect={'HomePanel.Visible':False,'EditPanel.Visible':False,'AboutPanel.Visible':True}))
    if advanced:tests += [dict(set={'BookBox.Text':'神奇校车','TargetBox.Text':'15'},event='AddButton.Click',expect={'global 计划':[{'title':'神奇校车','target':15,'done':False}],'global 选中序号':0})]
    if persist:tests += [dict(set={'global 计划':[{'title':'小王子','target':20,'done':False}],'global 选中序号':1},event='CompleteButton.Click',expect={'global 完成数':1,'global 完成目标分钟':20},stores={'plansV1':[{'title':'小王子','target':20,'done':True}]})]
    if safe:tests += [dict(set={'global 计划':[{'title':'小王子','target':20,'done':False}],'BookBox.Text':'小王子','TargetBox.Text':'20'},event='AddButton.Click',expect={'global 计划':[{'title':'小王子','target':20,'done':False}],'HintLabel.Text':'已有同名未完成计划，请先完成或修改书名'}),dict(set={'global 计划':[],'global 最近删除记录':{'title':'小王子','target':20,'done':False},'global 最近删除位置':1,'global 可撤销':True},event='UndoButton.Click',expect={'global 计划':[{'title':'小王子','target':20,'done':False}],'global 可撤销':False})]
    detail=dict(work=f'阅读搭子 {stageversion}：'+{51:'需求与单计划预览',52:'单Screen三页导航',53:'字典列表主流程',54:'完成与本地持久化',55:'删除确认与一次撤销',56:'CSV分享与最终交付'}[number],classroomKept=['前课已完成结构和非本课核心事件','本课所有同名组件、参数与过程调用'],classroomTasks=['补齐'+n+'过程' for n in tasks[number]],screenshotGroups=captures,tests=tests,implementationNotes=['连续毕业案例，组件标识与字典结构保持一致','本课版本：'+stageversion,'已完成目标分钟为目标值累计，不冒充实际阅读时长'],limitations=['未进行Android真机运行；文件与TinyDB跨进程行为由课堂真机核验','各课独立AIA包名不保证自动共享同一TinyDB，连续开发请在自己的同一工程中逐步扩展'])
    return p,detail


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('lessons',nargs='*',type=int,default=list(range(51,57)));args=ap.parse_args()
    for n in args.lessons:
        if not 51<=n<=56:ap.error('51–56 only')
        p,d=build(n);emit_project(n,p,d)
