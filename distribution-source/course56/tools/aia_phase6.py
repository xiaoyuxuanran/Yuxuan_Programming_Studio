"""Local classroom HTTP applications, lessons 37–42.

The host is always an editable teacher-computer IPv4 address.  The matching
standard-library teaching server implements the versioned endpoint contract.
"""
import argparse
import copy

from aia_phase1 import base
from aia_phase3 import lists
from aia_phase4 import choose, empty, negate, emit_project
from aia_phase5 import (view, length, item, append, foreach, lookup, dictionary,
                       islist, valid_index, local_decl, localset, do_return)


def isdict(p,value):return p.b('dictionaries_is_dict',values={'THING':value})
def intro(p,title,subtitle):
    return [p.label('PageTitle',title,FontSize=26,FontBold='True',Height=58,TextAlignment=1),p.label('SubtitleLabel',subtitle,FontSize=15,TextColor='&HFF56758B',Height=-1,TextAlignment=1),p.label('TopSpace','',Height=14)]
def istext(p,value):return p.b('text_is_string',values={'ITEM':value})
def textlen(p,value):return p.b('text_length',values={'VALUE':value})
def segment(p,value,start,count):return p.b('text_segment',values={'TEXT':value,'START':start,'LENGTH':count})
def safe_text(p,data,key,default='未填写'):
    return choose(p,istext(p,lookup(p,data(),key,default)),lookup(p,data(),key,default),p.text(default))


def host_ui(p):
    return [p.label('HostHint','教师电脑的局域网IPv4（下方只是示例，必须替换）',FontSize=14,Height=50),
        p.comp('HostBox','TextBox',Text='192.168.1.10',Hint='例如192.168.1.10，不带http://和端口',Width=-2,Height=50,FontSize=18,BackgroundColor='&HFFFFFFFF'),
        p.label('NetworkHint','手机与电脑使用同一教学局域网。先启动配套教学API；手机填写127.0.0.1会指向手机自己。',FontSize=13,TextColor='&HFF56758B',Height=75)]


def http_component(p):return p.comp('Http','Web',Timeout=5000,SaveResponse='False',ResponseTextEncoding='UTF-8')
def url(p,path):return p.join(p.text('http://'),p.trim(p.get('HostBox','Text')),p.text(':8765'),path)
def active(p):return p.both(p.var('请求中'),p.eq(p.param('url',True),p.var('当前URL')))
def finish(p,message):return p.call('结束请求',message,names=('提示',))


def common_globals(p):return [p.global_('请求中',p.boolean(False)),p.global_('当前URL',p.text(''))]


def end_proc(p,buttons=('RequestButton',)):
    return p.define('结束请求',p.chain(p.setvar('请求中',p.boolean(False)),*[p.set(x,'Enabled',p.boolean(True)) for x in buttons],p.set('HostBox','Enabled',p.boolean(True)),p.set('StatusLabel','Text',p.param('提示'))),args=('提示',))


def begin(p,path,buttons=('RequestButton',),method='Get',body=None):
    """One in-flight request; callbacks are correlated with its frozen URL."""
    return p.chain(p.setvar('请求中',p.boolean(True)),*[p.set(x,'Enabled',p.boolean(False)) for x in buttons],p.set('HostBox','Enabled',p.boolean(False)),p.set('StatusLabel','Text',p.text('请求中，请稍候…')),p.setvar('当前URL',url(p,path)),p.set('Http','Url',p.var('当前URL')),p.method('Http',method,*([body] if body is not None else [])))


def guarded(p,body):return p.iff(negate(p,p.var('请求中')),p.iff(empty(p,p.trim(p.get('HostBox','Text'))),p.set('StatusLabel','Text',p.text('请先填写教师电脑的局域网IPv4地址')),body))


def failure_events(p,post=False):
    timeout='请求超时，结果未确认；请先检查再重试，避免重复提交。' if post else '请求超时，请检查电脑地址与教学服务后重试。'
    return [p.event('Http','TimedOut',p.iff(active(p),finish(p,p.text(timeout)))),p.event('Screen1','ErrorOccurred',p.iff(p.var('请求中'),finish(p,p.join(p.text('通信或数据格式错误：'),p.param('message',True)))))]


def network_detail(**detail):
    detail.setdefault('implementationNotes',[])
    detail['implementationNotes']+=['HostBox默认192.168.1.10仅为示例，课堂替换为教师电脑的局域网IPv4','与teaching-http-api-spec.md及配套标准库服务使用同一协议；Timeout=5000ms','请求等待时禁用冲突按钮；GotText和TimedOut校验当前URL；所有错误出口恢复操作']
    detail.setdefault('limitations',[])
    detail['limitations']+=['未进行Android真机或用户已取消的物理断网验证；HTTP接口、原生工程导入与编译由主流程验证']
    return detail


def build37():
    p=base(37,'YXCourse37','APP 如何访问网络')
    p.screen([p.page(intro(p,'向课堂服务问个好','第 37 课｜地址、请求、状态码和响应')+host_ui(p)+[
        p.button('RequestButton','获取课堂问候'),p.button('ErrorButton','试试不存在的路径',BackgroundColor='&HFFDCEFFF',TextColor='&HFF123E62'),p.label('StatusLabel','尚未请求；本课读取普通文本。',FontSize=18,Height=100),p.label('ResultLabel','问候将显示在这里。',FontSize=23,Height=170,BackgroundColor='&HFFFFFFFF')]),http_component(p)])
    buttons=('RequestButton','ErrorButton')
    request=guarded(p,begin(p,p.param('路径'),buttons))
    got=p.iff(active(p),p.iff(p.cmp('EQ',p.param('responseCode',True),p.num(200)),p.chain(p.set('ResultLabel','Text',p.param('responseContent',True)),finish(p,p.text('HTTP 200：已收到课堂文本'))),p.chain(p.set('ResultLabel','Text',p.text('本次没有可显示的成功响应。')),finish(p,p.join(p.text('HTTP '),p.param('responseCode',True),p.text('：请求失败，请检查路径。'))))))
    p.tops=common_globals(p)+[end_proc(p,buttons),p.define('请求文本',request,args=('路径',)),p.event('RequestButton','Click',p.call('请求文本',p.text('/api/v1/hello'),names=('路径',))),p.event('ErrorButton','Click',p.call('请求文本',p.text('/api/v1/missing'),names=('路径',))),p.event('Http','GotText',got)]+failure_events(p)
    p.class_tops=copy.deepcopy(p.tops[:3])+[p.note(p.define('请求文本',guarded(p,p.chain(p.setvar('当前URL',url(p,p.param('路径'))),p.set('Http','Url',p.var('当前URL')),p.set('StatusLabel','Text',p.text('课堂任务：设请求状态并Get')))),args=('路径',)),'补等待状态、禁用按钮和Get调用。')]+copy.deepcopy(p.tops[4:6])+[p.note(p.event('Http','GotText',p.set('StatusLabel','Text',p.text('课堂任务：检查200，显示文本，结束请求。'))),'非200也要结束请求。')]
    return p,network_detail(work='本地HTTP文本问候与404恢复',classroomKept=['请求状态与当前URL','结束请求和两个按钮入口','请求文本地址组合占位、GotText占位'],classroomTasks=['请求文本加入请求中状态、禁用按钮和Get','GotText按200/其他状态处理并结束请求','添加TimedOut与ErrorOccurred恢复'],screenshotGroups=['请求文本','Http.GotText','Http.TimedOut'],tests=[dict(procedure='请求文本',args=['/api/v1/hello'],expect={'global 请求中':True,'RequestButton.Enabled':False,'Http.Url':'http://192.168.1.10:8765/api/v1/hello'},methodCounts={'Http.Get':1}),dict(set={'global 请求中':True,'global 当前URL':'x'},event='Http.GotText',args={'url':'x','responseCode':200,'responseContent':'你好，欢迎来到羽轩创意编程课堂！'},expect={'global 请求中':False,'RequestButton.Enabled':True,'ResultLabel.Text':'你好，欢迎来到羽轩创意编程课堂！'}),dict(set={'global 请求中':True,'global 当前URL':'x'},event='Http.GotText',args={'url':'x','responseCode':404,'responseContent':'{}'},contains={'StatusLabel.Text':['HTTP 404']},expect={'global 请求中':False}),dict(set={'global 请求中':True,'global 当前URL':'x'},event='Http.TimedOut',args={'url':'x'},expect={'global 请求中':False,'RequestButton.Enabled':True})])


def display_info(p,data,classname='ClassLabel',title='TitleLabel',activities='ActivitiesView'):
    """Safe missing/null/empty defaults; no first-item access before a guard."""
    first=lambda:item(p,p.param('公告列表'),p.num(1))
    announcements=p.chain(p.set(title,'Text',p.text('暂无公告')),p.iff(islist(p,p.param('公告列表')),p.iff(p.cmp('GT',length(p,p.param('公告列表')),p.num(0)),p.iff(isdict(p,first()),p.set(title,'Text',safe_text(p,first,'title','暂无公告'))))))
    return local_decl(p,[('公告列表',lookup(p,data(),'announcements',lists(p))),('活动列表',lookup(p,data(),'activities',lists(p)))],p.chain(p.set(classname,'Text',safe_text(p,data,'className','未命名班级')),announcements,p.set(activities,'Elements',choose(p,islist(p,p.param('活动列表')),p.param('活动列表'),lists(p)))))


def build38():
    p=base(38,'YXCourse38','读懂 JSON 数据')
    p.screen([p.page(intro(p,'班级信息解码器','第 38 课｜字典、列表与嵌套字段')+host_ui(p)+[
        p.button('RequestButton','读取班级教学示例'),p.label('StatusLabel','尚未读取。',FontSize=17,Height=80),p.label('ClassLabel','未命名班级',FontSize=25,FontBold='True',Height=55),p.label('TitleLabel','暂无公告',FontSize=22,Height=100,BackgroundColor='&HFFFFFFFF'),view(p,'ActivitiesView',150),p.label('SourceLabel','来源：配套本地教学API示例数据，不代表实时学校公告。',FontSize=14,Height=65)]),http_component(p)])
    got=p.iff(active(p),p.iff(p.cmp('EQ',p.param('responseCode',True),p.num(200)),p.chain(p.setvar('响应数据',p.method('Http','JsonTextDecodeWithDictionaries',p.param('responseContent',True))),p.iff(isdict(p,p.var('响应数据')),p.chain(p.call('显示公告',p.var('响应数据'),names=('数据',)),finish(p,p.text('已读取教学示例数据。'))),finish(p,p.text('响应格式错误：最外层应为JSON对象。')))),finish(p,p.join(p.text('HTTP '),p.param('responseCode',True),p.text('：读取失败，保留上次内容。')))))
    p.tops=common_globals(p)+[p.global_('响应数据',dictionary(p)),end_proc(p),p.define('读取公告',guarded(p,begin(p,p.text('/api/v1/info')))),p.define('显示公告',display_info(p,lambda:p.param('数据')),args=('数据',)),p.event('RequestButton','Click',p.call('读取公告')),p.event('Http','GotText',got)]+failure_events(p)
    p.class_tops=copy.deepcopy(p.tops[:5])+[p.note(p.define('显示公告',p.set('ClassLabel','Text',safe_text(p,lambda:p.param('数据'),'className','未命名班级')),args=('数据',)),'补首条公告和活动列表；先判断列表，再判断长度。')]+[copy.deepcopy(p.tops[6]),p.note(p.event('Http','GotText',p.iff(active(p),finish(p,p.text('课堂任务：200时解码为字典并显示公告')))),'使用JsonTextDecodeWithDictionaries和字典类型检查。')]+copy.deepcopy(p.tops[8:])
    return p,network_detail(work='JSON对象解码与缺字段默认值',classroomKept=['完整请求、结束请求与故障恢复','显示公告只保留顶层className默认读取','GotText占位与按钮入口'],classroomTasks=['GotText在200时解码并检查字典','公告列表判空后再读首项title','activities不是列表时使用空列表，缺班名默认未命名班级'],screenshotGroups=['Http.GotText','显示公告','RequestButton.Click'],tests=[dict(procedure='显示公告',args=[{'className':'创意班','announcements':[{'title':'欢迎来到创意班'}],'activities':['同伴试玩']}],expect={'ClassLabel.Text':'创意班','TitleLabel.Text':'欢迎来到创意班','ActivitiesView.Elements':['同伴试玩']}),dict(procedure='显示公告',args=[{'announcements':[],'activities':[]}],expect={'ClassLabel.Text':'未命名班级','TitleLabel.Text':'暂无公告','ActivitiesView.Elements':[]}),dict(procedure='显示公告',args=[{'className':None,'announcements':None,'activities':None}],expect={'ClassLabel.Text':'未命名班级','TitleLabel.Text':'暂无公告','ActivitiesView.Elements':[]})])


def dict_list_valid(p,value,fields=()):
    body=p.iff(islist(p,value()),foreach(p,'记录',value(),p.iff(isdict(p,p.param('记录')),p.chain(*[p.iff(negate(p,istext(p,lookup(p,p.param('记录'),key,p.num(0)))),localset(p,'有效',p.boolean(False))) for key in fields]),localset(p,'有效',p.boolean(False)))),localset(p,'有效',p.boolean(False)))
    return local_decl(p,[('有效',p.boolean(True))],do_return(p,body,p.param('有效')),returns=True)


def build39():
    p=base(39,'YXCourse39','制作信息查询工具')
    p.screen([p.page(intro(p,'校园地点查询器','第 39 课｜中文查询、结果列表与详情')+host_ui(p)+[
        p.comp('QueryBox','TextBox',Text='',Hint='输入图书、创客等地点关键词',Width=-2,Height=52,FontSize=20,BackgroundColor='&HFFFFFFFF'),p.button('RequestButton','查询校园地点'),p.label('StatusLabel','输入关键词后查询本地教学地点表。',FontSize=17,Height=85),view(p,'PlacesView',150),p.label('DetailLabel','',FontSize=21,Height=140,BackgroundColor='&HFFFFFFFF')]),http_component(p)])
    names=p.chain(p.setvar('地点结果',p.param('列表')),p.setvar('地点名称',lists(p)),foreach(p,'地点',p.var('地点结果'),append(p,p.var('地点名称'),safe_text(p,lambda:p.param('地点'),'name','未命名地点'))),p.set('PlacesView','Elements',p.var('地点名称')),p.set('PlacesView','SelectionIndex',p.num(0)),p.set('DetailLabel','Text',p.text('')),finish(p,choose(p,p.cmp('EQ',length(p,p.var('地点结果')),p.num(0)),p.text('找到0项，请换个关键词。'),p.join(p.text('找到'),length(p,p.var('地点结果')),p.text('项，请选择查看。')))))
    query=guarded(p,p.iff(empty(p,p.trim(p.get('QueryBox','Text'))),p.set('StatusLabel','Text',p.text('请先输入地点关键词')),p.chain(p.set('DetailLabel','Text',p.text('')),begin(p,p.join(p.text('/api/v1/places?q='),p.method('Http','UriEncode',p.trim(p.get('QueryBox','Text'))))))))
    got=p.iff(active(p),p.iff(p.cmp('EQ',p.param('responseCode',True),p.num(200)),p.chain(p.setvar('响应数据',p.method('Http','JsonTextDecodeWithDictionaries',p.param('responseContent',True))),p.iff(isdict(p,p.var('响应数据')),p.iff(dict_list_valid(p,lambda:lookup(p,p.var('响应数据'),'items',p.text('缺少items')),('name',)),p.call('显示地点结果',lookup(p,p.var('响应数据'),'items',lists(p)),names=('列表',)),finish(p,p.text('响应格式错误：items应为地点字典列表。'))),finish(p,p.text('响应格式错误：需要JSON对象。')))),finish(p,p.join(p.text('HTTP '),p.param('responseCode',True),p.text('：查询失败，检查关键词和服务。')))))
    selected=lambda:item(p,p.var('地点结果'),p.get('PlacesView','SelectionIndex'))
    detail=p.iff(valid_index(p,lambda:p.get('PlacesView','SelectionIndex'),lambda:p.var('地点结果')),p.set('DetailLabel','Text',p.join(safe_text(p,selected,'name','未命名地点'),p.text('\n楼层：'),lookup(p,selected(),'floor','未填写'),p.text('\n提示：'),safe_text(p,selected,'note','暂无提示'))))
    p.tops=common_globals(p)+[p.global_('地点结果',lists(p)),p.global_('地点名称',lists(p)),p.global_('响应数据',dictionary(p)),end_proc(p),p.define('查询地点',query),p.define('显示地点结果',names,args=('列表',)),p.event('RequestButton','Click',p.call('查询地点')),p.event('Http','GotText',got),p.event('PlacesView','AfterPicking',detail)]+failure_events(p)
    p.class_tops=copy.deepcopy(p.tops[:6])+[p.note(p.define('查询地点',guarded(p,p.set('StatusLabel','Text',p.text('课堂任务：trim、非空检查和UriEncode后请求。')))),'查询中文必须经过UriEncode。'),p.note(p.define('显示地点结果',p.chain(p.setvar('地点结果',p.param('列表')),p.setvar('地点名称',lists(p)),foreach(p,'地点',p.var('地点结果'),append(p,p.var('地点名称'),safe_text(p,lambda:p.param('地点'),'name','未命名地点'))),p.set('PlacesView','Elements',p.var('地点名称')),finish(p,p.text('课堂任务：添加数量、清详情和0项状态'))),args=('列表',)),'补清旧选择、详情和空结果状态。')]+copy.deepcopy(p.tops[8:10])+[p.note(p.event('PlacesView','AfterPicking',p.set('DetailLabel','Text',p.text('课堂任务：有效索引下读取floor和note。'))),'列表索引与地点字典列表同序。')]+copy.deepcopy(p.tops[11:])
    return p,network_detail(work='中文编码查询与地点详情',classroomKept=['请求响应解码与items类型验证','显示地点结果主体列表生成','结束请求和错误恢复；查询与详情占位'],classroomTasks=['查询地点添加非空检查和UriEncode参数','详情校验SelectionIndex后按键显示','空结果清旧详情、取消选择并显示0项'],screenshotGroups=['查询地点','显示地点结果','PlacesView.AfterPicking'],tests=[dict(set={'QueryBox.Text':'  图书  '},procedure='查询地点',contains={'Http.Url':['/api/v1/places?q=']},methodCounts={'Http.UriEncode':1,'Http.Get':1}),dict(procedure='显示地点结果',args=[[{'name':'图书角','floor':2,'note':'课间可借阅'}]],expect={'PlacesView.Elements':['图书角'],'DetailLabel.Text':''}),dict(set={'global 地点结果':[{'name':'创客教室','floor':3,'note':'在教师陪同下使用'}],'PlacesView.SelectionIndex':1},event='PlacesView.AfterPicking',expect={'DetailLabel.Text':'创客教室\n楼层：3\n提示：在教师陪同下使用'}),dict(set={'DetailLabel.Text':'旧地点'},procedure='显示地点结果',args=[[]],expect={'DetailLabel.Text':'','PlacesView.Elements':[]},contains={'StatusLabel.Text':['0项']})])


def form_headers(p):return p.set('Http','RequestHeaders',lists(p,lists(p,p.text('Content-Type'),p.text('application/x-www-form-urlencoded; charset=UTF-8'))))
def form_body(p,**fields):return p.method('Http','BuildRequestData',lists(p,*[lists(p,p.text(k),v) for k,v in fields.items()]))
def valid_text_length(p,value,minlen,maxlen):return p.both(p.cmp('GTE',textlen(p,value()),p.num(minlen)),p.cmp('LTE',textlen(p,value()),p.num(maxlen)))


def build40():
    p=base(40,'YXCourse40','把数据提交出去')
    p.screen([p.page(intro(p,'课堂意见箱','第 40 课｜表单POST、服务回执与保留草稿')+host_ui(p)+[
        p.comp('KindPicker','ListPicker',Text='类型：建议',ElementsFromString='建议,问题,表扬',Title='选择反馈类型',Width=-2,Height=50,FontSize=18,BackgroundColor='&HFFDCEFFF',TextColor='&HFF123E62'),p.comp('MessageBox','TextBox',Text='',Hint='1～200字教学反馈，不需要真实姓名或电话',MultiLine='True',Width=-2,Height=120,FontSize=20,BackgroundColor='&HFFFFFFFF'),p.button('RequestButton','提交教学反馈'),p.label('StatusLabel','输入后发送；未确认时不会自动重复提交。',FontSize=17,Height=100),p.label('ReceiptLabel','回执编号将在成功提交后显示。',FontSize=22,Height=130,BackgroundColor='&HFFFFFFFF')]),http_component(p)])
    content=lambda:p.trim(p.get('MessageBox','Text'))
    submit=guarded(p,p.iff(valid_text_length(p,content,1,200),p.chain(p.set('ReceiptLabel','Text',p.text('等待服务回执…')),form_headers(p),begin(p,p.text('/api/v1/feedback'),method='PostText',body=form_body(p,kind=p.var('类型'),message=content()))),p.set('StatusLabel','Text',p.text('正文须为1～200字，空格不能作正文。'))))
    validreceipt=p.both(istext(p,lookup(p,p.var('响应数据'),'id',p.num(0))),negate(p,empty(p,lookup(p,p.var('响应数据'),'id',''))))
    success=p.chain(p.setvar('响应数据',p.method('Http','JsonTextDecodeWithDictionaries',p.param('responseContent',True))),p.iff(isdict(p,p.var('响应数据')),p.iff(validreceipt,p.chain(p.set('ReceiptLabel','Text',p.join(p.text('已接收，编号：'),lookup(p,p.var('响应数据'),'id',''))),p.set('MessageBox','Text',p.text('')),finish(p,p.text('HTTP 201：反馈已接收。'))),finish(p,p.text('回执格式异常，结果未确认；草稿保留，请先检查。'))),finish(p,p.text('回执不是JSON对象；结果未确认，请先检查。'))))
    got=p.iff(active(p),p.iff(p.cmp('EQ',p.param('responseCode',True),p.num(201)),success,finish(p,p.join(p.text('HTTP '),p.param('responseCode',True),p.text('：提交未确认，正文已保留；请检查类型、长度或教学服务。')))))
    p.tops=common_globals(p)+[p.global_('类型',p.text('建议')),p.global_('响应数据',dictionary(p)),end_proc(p),p.define('提交反馈',submit),p.define('结束提交',finish(p,p.param('提示')),args=('提示',)),p.event('KindPicker','BeforePicking',p.set('KindPicker','Elements',lists(p,p.text('建议'),p.text('问题'),p.text('表扬')))),p.event('KindPicker','AfterPicking',p.iff(valid_index(p,lambda:p.get('KindPicker','SelectionIndex'),lambda:lists(p,p.text('建议'),p.text('问题'),p.text('表扬'))),p.chain(p.setvar('类型',p.get('KindPicker','Selection')),p.set('KindPicker','Text',p.join(p.text('类型：'),p.var('类型')))))),p.event('RequestButton','Click',p.call('提交反馈')),p.event('Http','GotText',got)]+failure_events(p,post=True)
    p.class_tops=copy.deepcopy(p.tops[:5])+[p.note(p.define('提交反馈',p.set('StatusLabel','Text',p.text('课堂任务：正文校验、表单编码与PostText。'))),'BuildRequestData负责中文、&与=等表单转义。')]+copy.deepcopy(p.tops[6:10])+[p.note(p.event('Http','GotText',p.iff(active(p),finish(p,p.text('课堂任务：只有201且有id才清空正文')))),'失败保留草稿，不假报成功。')]+copy.deepcopy(p.tops[11:])
    return p,network_detail(work='URL编码反馈表单与201回执',classroomKept=['类型选择与变量','结束请求/结束提交及超时错误恢复','提交反馈与GotText占位'],classroomTasks=['校验trim正文长度1～200，设置表单Content-Type','BuildRequestData封装kind和message并PostText','201解析有效id后清稿，400/超时保留草稿'],screenshotGroups=['提交反馈','Http.GotText','Http.TimedOut'],tests=[dict(set={'MessageBox.Text':'  '},procedure='提交反馈',expect={'global 请求中':False},methodCounts={'Http.PostText':0}),dict(set={'MessageBox.Text':'增加阅读角'},procedure='提交反馈',expect={'global 请求中':True,'RequestButton.Enabled':False},methodCounts={'Http.PostText':1,'Http.BuildRequestData':1}),dict(set={'global 请求中':True,'global 当前URL':'x','MessageBox.Text':'草稿'},event='Http.GotText',args={'url':'x','responseCode':400,'responseContent':'{"error":"bad"}'},expect={'MessageBox.Text':'草稿','global 请求中':False}),dict(set={'global 请求中':True,'global 当前URL':'x','MessageBox.Text':'草稿'},event='Http.TimedOut',args={'url':'x'},expect={'MessageBox.Text':'草稿','global 请求中':False},contains={'StatusLabel.Text':['结果未确认']})],implementationNotes=['统一请求中变量承担蓝图提交中状态，避免两个忙状态不一致','POST无自动重试；只有有效201回执才清空正文'])


def build41():
    p=base(41,'YXCourse41','多个用户共享信息')
    p.screen([p.page(intro(p,'共享课堂留言板','第 41 课｜同一服务、多端读取与发布后刷新')+host_ui(p)+[
        p.comp('NickBox','TextBox',Text='星星',Hint='课堂化名，1～12字',Width=-2,Height=50,FontSize=18,BackgroundColor='&HFFFFFFFF'),p.comp('MessageBox','TextBox',Text='',Hint='1～120字，不填写个人隐私',MultiLine='True',Width=-2,Height=90,FontSize=18,BackgroundColor='&HFFFFFFFF'),p.comp('Buttons','HorizontalArrangement',[p.button('RequestButton','刷新留言',Width=-1050),p.button('PostButton','发布留言',Width=-1050)],Width=-2,Height=58),p.label('StatusLabel','先刷新；服务保留最近50条教学留言。',FontSize=16,Height=85),view(p,'MessagesView',155),p.label('DetailLabel','选择一条留言查看完整正文与服务时间。',FontSize=18,Height=150,BackgroundColor='&HFFFFFFFF')]),http_component(p)])
    buttons=('RequestButton','PostButton')
    read=guarded(p,p.chain(p.setvar('操作',p.text('读取')),p.set('Http','RequestHeaders',lists(p)),begin(p,p.text('/api/v1/messages'),buttons)))
    validinput=p.both(valid_text_length(p,lambda:p.trim(p.get('NickBox','Text')),1,12),valid_text_length(p,lambda:p.trim(p.get('MessageBox','Text')),1,120))
    post=guarded(p,p.iff(validinput,p.chain(p.setvar('操作',p.text('发布')),form_headers(p),begin(p,p.text('/api/v1/messages'),buttons,method='PostText',body=form_body(p,nick=p.trim(p.get('NickBox','Text')),message=p.trim(p.get('MessageBox','Text'))))),p.set('StatusLabel','Text',p.text('昵称须1～12字，正文须1～120字；不能为空。'))))
    summary=p.join(safe_text(p,lambda:p.param('项'),'nick','匿名'),p.text('：'),segment(p,safe_text(p,lambda:p.param('项'),'message',''),p.num(1),p.mm('MIN',textlen(p,safe_text(p,lambda:p.param('项'),'message','')),p.num(20))))
    show=p.chain(p.setvar('显示留言',lists(p)),foreach(p,'项',p.var('留言'),append(p,p.var('显示留言'),summary)),p.set('MessagesView','Elements',p.var('显示留言')),p.set('MessagesView','SelectionIndex',p.num(0)),p.set('DetailLabel','Text',p.text('')),finish(p,p.join(p.text('读取'),length(p,p.var('留言')),p.text('条，服务最多保留最近50条。'))))
    decode=lambda:p.setvar('响应数据',p.method('Http','JsonTextDecodeWithDictionaries',p.param('responseContent',True)))
    readsuccess=p.chain(decode(),p.iff(isdict(p,p.var('响应数据')),p.iff(dict_list_valid(p,lambda:lookup(p,p.var('响应数据'),'items',p.num(0)),('nick','message','createdAt')),p.chain(p.setvar('留言',lookup(p,p.var('响应数据'),'items',lists(p))),p.call('显示留言')),finish(p,p.text('留言items格式错误，保留上次列表。'))),finish(p,p.text('读取响应不是JSON对象。'))))
    # A successful POST must have a usable server id before clearing the draft.
    postsuccess=p.chain(decode(),p.iff(isdict(p,p.var('响应数据')),p.iff(p.isnum(lookup(p,p.var('响应数据'),'id',p.text('缺少id'))),p.chain(p.set('MessageBox','Text',p.text('')),p.setvar('请求中',p.boolean(False)),p.call('读取留言')),finish(p,p.text('发布回执缺少id，结果未确认，请先刷新检查。'))),finish(p,p.text('发布回执格式错误；正文保留，请先刷新检查。'))))
    got=p.iff(active(p),p.iff(p.eq(p.var('操作'),p.text('发布')),p.iff(p.cmp('EQ',p.param('responseCode',True),p.num(201)),postsuccess,finish(p,p.join(p.text('发布HTTP '),p.param('responseCode',True),p.text('：未确认，保留正文。')))),p.iff(p.cmp('EQ',p.param('responseCode',True),p.num(200)),readsuccess,finish(p,p.join(p.text('读取HTTP '),p.param('responseCode',True),p.text('：失败，保留列表。'))))))
    selected=lambda:item(p,p.var('留言'),p.get('MessagesView','SelectionIndex'))
    details=p.iff(valid_index(p,lambda:p.get('MessagesView','SelectionIndex'),lambda:p.var('留言')),p.set('DetailLabel','Text',p.join(p.text('昵称：'),safe_text(p,selected,'nick','匿名'),p.text('\n正文：'),safe_text(p,selected,'message',''),p.text('\n编号：'),lookup(p,selected(),'id','未填写'),p.text('\n服务时间：'),safe_text(p,selected,'createdAt','未提供'))))
    p.tops=common_globals(p)+[p.global_('操作',p.text('无')),p.global_('留言',lists(p)),p.global_('显示留言',lists(p)),p.global_('响应数据',dictionary(p)),end_proc(p,buttons),p.define('读取留言',read),p.define('发布留言',post),p.define('显示留言',show),p.event('RequestButton','Click',p.call('读取留言')),p.event('PostButton','Click',p.call('发布留言')),p.event('Http','GotText',got),p.event('MessagesView','AfterPicking',details)]+failure_events(p,post=True)
    p.class_tops=copy.deepcopy(p.tops[:8])+[p.note(p.define('发布留言',p.set('StatusLabel','Text',p.text('课堂任务：校验并发布表单'))),'设置操作为发布，POST期间禁用两个按钮。')]+copy.deepcopy(p.tops[9:12])+[p.note(p.event('Http','GotText',p.iff(active(p),p.iff(p.both(p.eq(p.var('操作'),p.text('读取')),p.cmp('EQ',p.param('responseCode',True),p.num(200))),copy.deepcopy(readsuccess),finish(p,p.text('课堂任务：添加发布201分支及发布后读取'))))),'现有读取可用，补发布响应分支。')]+copy.deepcopy(p.tops[13:])
    return p,network_detail(work='共享留言GET/POST与发布后自动刷新',classroomKept=['数据变量、完整读取和显示列表','双按钮入口、详情与故障恢复','GotText仅支持读取200；发布留言占位'],classroomTasks=['发布留言校验昵称1～12和正文1～120并编码表单','GotText按操作区分发布201和读取200','201有id才清稿，再Get刷新；绝不再次Post自动重发'],screenshotGroups=['读取留言','Http.GotText','MessagesView.AfterPicking'],tests=[dict(set={'NickBox.Text':'','MessageBox.Text':'正文'},procedure='发布留言',expect={'global 请求中':False},methodCounts={'Http.PostText':0}),dict(set={'NickBox.Text':'星星','MessageBox.Text':'我的作品完成啦'},procedure='发布留言',expect={'global 操作':'发布','RequestButton.Enabled':False,'PostButton.Enabled':False},methodCounts={'Http.PostText':1}),dict(set={'global 留言':[{'id':1,'nick':'星星','message':'完整正文','createdAt':'2026-10-18T09:00:00+08:00'}],'MessagesView.SelectionIndex':1},event='MessagesView.AfterPicking',contains={'DetailLabel.Text':['星星','完整正文','编号：1','服务时间：2026-10-18']}),dict(set={'global 留言':[]},procedure='显示留言',expect={'MessagesView.Elements':[],'DetailLabel.Text':'','global 请求中':False})],implementationNotes=['请求中禁用刷新与发布；操作变量区分同一URL的GET/POST回调','昵称和正文摘要20字符；详情展示全文及id、createdAt','发布成功回执有数字id后仅重新GET，避免重复发布'])


def valid_info(p,value):
    activity=lambda:lookup(p,value(),'activities',p.num(0))
    checks=p.chain(p.iff(negate(p,istext(p,lookup(p,value(),'className',p.num(0)))),localset(p,'结构有效',p.boolean(False))),p.iff(negate(p,istext(p,lookup(p,value(),'updatedAt',p.num(0)))),localset(p,'结构有效',p.boolean(False))),p.iff(negate(p,dict_list_valid(p,lambda:lookup(p,value(),'announcements',p.num(0)),('title','body'))),localset(p,'结构有效',p.boolean(False))),p.iff(islist(p,activity()),foreach(p,'活动',activity(),p.iff(negate(p,istext(p,p.param('活动'))),localset(p,'结构有效',p.boolean(False)))),localset(p,'结构有效',p.boolean(False))))
    return local_decl(p,[('结构有效',p.boolean(True))],do_return(p,p.iff(isdict(p,value()),checks,localset(p,'结构有效',p.boolean(False))),p.param('结构有效')),returns=True)


def build42():
    p=base(42,'YXCourse42','完善一个网络应用')
    p.screen([p.page(intro(p,'可靠的班级信息窗','第 42 课｜先看缓存，成功更新，失败保留')+host_ui(p)+[
        p.button('RequestButton','刷新教学公告'),p.label('StatusLabel','启动后先读取本机缓存。',FontSize=17,Height=100),p.label('InfoLabel','尚无资料，请刷新。',FontSize=23,Height=170,BackgroundColor='&HFFFFFFFF'),p.label('CacheLabel','暂无成功接收记录。',FontSize=15,Height=110),view(p,'ActivitiesView',150),p.label('SourceHint','本课为教学示例。缓存接收时间来自本机；服务updatedAt是示例修改时间。',FontSize=13,Height=75)]),p.comp('LocalDB','TinyDB',Namespace='YXCourse42'),p.comp('TimeClock','Clock',TimerEnabled='False'),http_component(p)])
    first=lambda:item(p,p.param('公告'),p.num(1))
    show=local_decl(p,[('公告',lookup(p,p.param('数据'),'announcements',lists(p))),('标题',p.text('暂无公告'))],p.chain(p.iff(islist(p,p.param('公告')),p.iff(p.cmp('GT',length(p,p.param('公告')),p.num(0)),p.iff(isdict(p,first()),localset(p,'标题',safe_text(p,first,'title','暂无公告'))))),p.set('InfoLabel','Text',p.join(safe_text(p,lambda:p.param('数据'),'className','未命名班级'),p.text('\n'),p.param('标题'))),p.set('ActivitiesView','Elements',lookup(p,p.param('数据'),'activities',lists(p))),p.set('CacheLabel','Text',p.join(p.text('来源：'),p.param('来源'),p.text('\n上次成功接收：'),p.var('缓存时间'),p.text('\n示例修改时间：'),safe_text(p,lambda:p.param('数据'),'updatedAt','未提供')))))
    valid=lambda data:p.call('公告结构有效',data,names=('数据',),returns=True)
    load=p.chain(p.setvar('缓存数据',p.method('LocalDB','GetValue',p.text('info'),dictionary(p))),p.setvar('缓存时间',p.method('LocalDB','GetValue',p.text('savedAt'),p.text(''))),p.iff(p.both(valid(p.var('缓存数据')),p.both(istext(p,p.var('缓存时间')),negate(p,empty(p,p.var('缓存时间'))))),p.chain(p.call('显示数据',p.var('缓存数据'),p.text('本机缓存（内容可能过时）'),names=('数据','来源')),p.set('StatusLabel','Text',p.text('已显示缓存，可刷新获取本次结果。'))),p.chain(p.setvar('缓存数据',dictionary(p)),p.setvar('缓存时间',p.text('')),p.set('InfoLabel','Text',p.text('尚无资料，请刷新。')),p.set('ActivitiesView','Elements',lists(p)),p.set('CacheLabel','Text',p.text('暂无成功接收记录。')),p.set('StatusLabel','Text',p.text('尚无有效缓存，检查地址后点击刷新。')))))
    fail=p.chain(p.iff(valid(p.var('缓存数据')),p.call('显示数据',p.var('缓存数据'),p.text('本机缓存（内容可能过时）'),names=('数据','来源')),p.set('CacheLabel','Text',p.text('没有可用缓存；尚未收到成功结果。'))),finish(p,p.join(p.text('本次更新失败：'),p.param('原因'),p.text('。可以再次刷新。'))))
    success=p.iff(valid(p.param('数据')),p.chain(p.setvar('缓存数据',p.param('数据')),p.setvar('缓存时间',p.method('TimeClock','FormatDateTime',p.method('TimeClock','Now'),p.text('yyyy-MM-dd HH:mm:ss'))),p.method('LocalDB','StoreValue',p.text('info'),p.var('缓存数据')),p.method('LocalDB','StoreValue',p.text('savedAt'),p.var('缓存时间')),p.call('显示数据',p.var('缓存数据'),p.text('本次网络结果（教学示例）'),names=('数据','来源')),finish(p,p.text('刷新成功，数据与接收时间已缓存。'))),p.call('失败恢复',p.text('JSON结构不符合教学接口'),names=('原因',)))
    got=p.iff(active(p),p.iff(p.cmp('EQ',p.param('responseCode',True),p.num(200)),p.chain(p.setvar('响应数据',p.method('Http','JsonTextDecodeWithDictionaries',p.param('responseContent',True))),p.call('成功更新',p.var('响应数据'),names=('数据',))),p.call('失败恢复',p.join(p.text('HTTP '),p.param('responseCode',True)),names=('原因',))))
    timeout=p.event('Http','TimedOut',p.iff(active(p),p.call('失败恢复',p.text('请求超过5秒，请检查地址与教学服务'),names=('原因',))))
    error=p.event('Screen1','ErrorOccurred',p.iff(p.var('请求中'),p.call('失败恢复',p.join(p.text('通信或格式错误：'),p.param('message',True)),names=('原因',))))
    p.tops=common_globals(p)+[p.global_('缓存数据',dictionary(p)),p.global_('缓存时间',p.text('')),p.global_('响应数据',dictionary(p)),end_proc(p),p.define('公告结构有效',valid_info(p,lambda:p.param('数据')),args=('数据',),returns=True),p.define('显示数据',show,args=('数据','来源')),p.define('载入缓存',load),p.define('刷新公告',guarded(p,begin(p,p.text('/api/v1/info')))),p.define('成功更新',success,args=('数据',)),p.define('失败恢复',fail,args=('原因',)),p.event('Screen1','Initialize',p.call('载入缓存')),p.event('RequestButton','Click',p.call('刷新公告')),p.event('Http','GotText',got),timeout,error]
    p.class_tops=copy.deepcopy(p.tops[:9])+[p.note(p.define('刷新公告',guarded(p,p.set('StatusLabel','Text',p.text('课堂任务：请求状态、禁用按钮、Get')))),'使用http://教师电脑IPv4:8765/api/v1/info。'),p.note(p.define('成功更新',p.set('StatusLabel','Text',p.text('课堂任务：验证后StoreValue保存info和savedAt。')),args=('数据',)),'不得将500、坏JSON或坏结构覆盖好缓存。'),p.note(p.define('失败恢复',p.set('StatusLabel','Text',p.join(p.text('课堂任务：恢复按钮并保留缓存；原因：'),p.param('原因'))),args=('原因',)),'显示缓存来源、可能过时和失败原因。')]+copy.deepcopy(p.tops[12:])
    sample={'className':'创意班','announcements':[{'id':1,'title':'欢迎来到创意班','body':'今天用程序表达一个想法'}],'activities':['同伴试玩'],'updatedAt':'2026-10-18T09:00:00+08:00'}
    return p,network_detail(work='结构校验、TinyDB缓存与失败保留',classroomKept=['缓存与请求变量、结构验证和结束请求','完整显示数据、载入缓存和所有事件入口','刷新公告、成功更新、失败恢复占位'],classroomTasks=['刷新公告设置等待状态并Get','成功更新先结构验证，再存info和savedAt并显示网络来源','失败恢复保留缓存、标记可能过时并恢复按钮'],screenshotGroups=['载入缓存','成功更新','失败恢复'],tests=[dict(event='Screen1.Initialize',expect={'InfoLabel.Text':'尚无资料，请刷新。','ActivitiesView.Elements':[]}),dict(procedure='公告结构有效',args=[sample],returns=True),dict(procedure='公告结构有效',args=[{'className':'坏表','announcements':None,'activities':[]}],returns=False),dict(set={'global 缓存数据':sample,'global 缓存时间':'2026-10-18 10:00:00','global 请求中':True},procedure='失败恢复',args=['HTTP 500'],contains={'InfoLabel.Text':['创意班','欢迎来到创意班'],'CacheLabel.Text':['本机缓存','可能过时','2026-10-18 10:00:00'],'StatusLabel.Text':['HTTP 500']},expect={'global 请求中':False,'RequestButton.Enabled':True}),dict(set={'global 缓存数据':sample,'global 缓存时间':'旧时间'},procedure='成功更新',args=[{'wrong':1}],expect={'global 缓存数据':sample,'global 缓存时间':'旧时间'},methodCounts={'LocalDB.StoreValue':0})],implementationNotes=['成功缓存前验证className/updatedAt文本、announcements字典列表及activities文本列表','缓存数据和savedAt只在有效200后保存；失败保留旧值','缓存接收时间用本机Clock.Now，和服务示例updatedAt分开显示'])


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('lessons',nargs='*',type=int,default=list(range(37,43)));args=parser.parse_args()
    for n in args.lessons:
        if n not in range(37,43):parser.error('This module authors lessons37..42')
        emit_project(n,*globals()[f'build{n:02d}']())
