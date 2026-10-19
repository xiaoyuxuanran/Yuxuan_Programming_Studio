from pathlib import Path
import json

ROOT = Path(__file__).resolve().parent
UI = 'https://ai2.appinventor.mit.edu/reference/components/userinterface.html'
LAYOUT = 'https://ai2.appinventor.mit.edu/reference/components/layout.html'
MEDIA = 'https://ai2.appinventor.mit.edu/reference/components/media.html'
LEARN = 'https://appinventor.mit.edu/explore/teach'

def slide(title, body, notes, layout='text', **extra):
    return dict(title=title, body=body, notes=notes, layout=layout, **extra)

def agenda(rows):
    return [dict(start=a,end=b,minutes=b-a,slides=s,teacher=t,students=u,checkpoint=c) for a,b,s,t,u,c in rows]

LESSONS = []
LESSONS.append(dict(
lesson=1,title='我的第一个手机 APP',projectName='Hello01',exampleTitle='点击问候',durationMinutes=90,
goals=['区分组件设计与逻辑设计，指出按钮和标签各自的作用。','用 HelloButton.Click 改变 GreetingLabel.Text。','通过两种点击顺序检查问候与重置，并导出可编辑 AIA。'],
exampleSpec={'summary':'初始显示“准备好了吗？点一下按钮。”；点击问候显示“你好，欢迎来到我的第一个 APP！”；点击重置恢复初始文本。','components':[{'name':'GreetingLabel','type':'Label','role':'显示问候和初始提示'},{'name':'HelloButton','type':'Button','role':'触发问候'},{'name':'ResetButton','type':'Button','role':'恢复初始文字'}],'logic':[{'event':'HelloButton.Click','actions':['GreetingLabel.Text ← 你好，欢迎来到我的第一个 APP！']},{'event':'ResetButton.Click','actions':['GreetingLabel.Text ← 准备好了吗？点一下按钮。']}],'scope':'不使用变量、条件、输入框、语音和联网；本课先把一个事件与一个属性连接清楚。'},
versions={'answer':'Hello01.aia：两个按钮事件均完整。','class':'Hello01Class.aia：保留界面及 ResetButton.Click 演示，学生添加 HelloButton.Click 的问候逻辑。','starter':'Hello01Starter.aia：只有组件设计与素材，没有积木；用于课后重新搭建。'},
agenda=agenda([(0,10,'1–3','演示问候与重置，先不展示积木。','说出点击前后发生了什么。','学生能描述一次输入和一次输出。'),(10,25,'4–8','带学生辨认设计界面、组件树和属性。','导入Class工程，指出按钮、标签和Text属性。','能选中GreetingLabel而不是Screen1。'),(25,45,'9–11','短示范事件容器与设置属性积木，然后巡视。','制作问候事件，修改为自己的文明问候。','Click内有一条连好的Text设置。'),(45,60,'12–14','解读已给出的重置事件，示范测试顺序。','完成问候→重置→问候和重复点击测试。','重置确实恢复初始提示。'),(60,75,'15–19','引导排查组件选错、文字块未连接，再做小改编。','修复一个问题，修改按钮文字与问候内容并导出。','界面文字变化不破坏按钮作用。'),(75,90,'20–24','组织双人体验、出口题和作品提交。','互测、解释“当……就……”，提交AIA和任务单。','能找到导出的AIA并口头解释自己的事件。')]),
tasks=[{'title':'找到屏幕上的角色','steps':['导入 Hello01Class.aia，切到组件设计。','点选 GreetingLabel，找到 Text；再点 HelloButton，比较两者的属性。','把按钮可见文字改为“向你问好”。'],'question':'为什么按钮和标签都有Text，却承担不同工作？','answer':'Text都是文字属性；按钮用于触发点击事件，标签主要负责展示信息。'},{'title':'完成点击问候','steps':['在逻辑设计中展开 HelloButton，拖出 Click 事件。','展开 GreetingLabel，放入“设置 GreetingLabel.Text 为”。','连接一个文字块，写“你好，欢迎来到我的第一个 APP！”或自己的问候。'],'question':'属性设置积木放在事件外面，会在点击时执行吗？','answer':'不会成为该Click事件的动作；需要把它连接在事件的do区域。'},{'title':'理解重置与保存','steps':['找到已提供的 ResetButton.Click，读出恢复的文字。','按问候→重置→问候测试，再连续点问候三次。','项目→导出项目(.aia)，以英文项目名保存可编辑工程。'],'question':'连续点三次问候，屏幕会出现三行问候吗？','answer':'不会；设置Text是把标签文字替换为同一段文字，本课没有追加文字。'}],
tests=[{'action':'刚启动','expected':'标签显示初始提示，两个按钮可见。'},{'action':'点击问候','expected':'标签变成完整问候文字。'},{'action':'连续点击问候三次','expected':'文字保持一份，不自动累加。'},{'action':'问候后点击重置','expected':'恢复初始提示。'},{'action':'重置后再次问候','expected':'仍可显示问候，事件没有失效。'}],
challenges=[{'level':'基础','task':'完成问候、重置两条路径，能解释一次点击触发什么。'},{'level':'提高','task':'只改变问候内容和按钮文字，让同伴无需说明就会用。'},{'level':'拓展','task':'增加晚安按钮并设置另一句文字；保留重置，测试每个按钮。'}],
misconceptions=[['设计器里点击按钮没有运行','设计器主要用于安排界面；运行需课堂已配置的Android环境。'],['积木选成HelloButton.Text','问候应显示在GreetingLabel，检查属性块的组件名。'],['文字块悬空','文字块必须插入设置Text的输入槽。']],
exitQuestions=[{'q':'“当HelloButton.Click，就设置GreetingLabel.Text”中，哪一段是事件？','a':'HelloButton.Click是事件，设置Text是事件发生后执行的动作。'},{'q':'想改开机时就出现的文字，先在哪设置？','a':'组件设计中选GreetingLabel并修改Text；本课重置事件也要与新的初始文字一致。'},{'q':'AIA和APK有什么不同？','a':'AIA保存可编辑工程；APK用于在Android环境安装。'}],
sources=[{'title':'MIT组件参考：Button与Label','url':UI,'use':'核对Click事件与Text属性。'},{'title':'MIT教学资源','url':LEARN,'use':'参考体验、创作、分享的组织方式；本课为独立编写课程。'}],
componentMetadata={'Button':'8','Label':'6','VerticalArrangement':'4'},
slides=[
slide('我的第一个手机 APP',['第1课 · 点击问候','90分钟：让一次点击产生看得见的回应'], '先让学生描述熟悉的APP按钮，再展示本课作品。不要先讲所有区域的名字；今天只需要按钮、标签和一个事件。'),
slide('一次点击带来的变化',['初始：准备好了吗？','点击问候：出现欢迎语','点击重置：回到初始提示'], '教师运行完整例子。先点问候，再点重置，最后连续点两次问候。请学生说“我点了什么、屏幕哪一处变了”，不用要求术语。', 'question'),
slide('今天的作品证据',['按钮能触发问候','标签能恢复初始文字','我能说清事件与动作'], '把目标转为可观察证据：学生能演示、能解释、能保存。按钮漂不漂亮不是本课首要评分项。'),
slide('90分钟的学习路线',['每次短示范后立即操作'], '前10分钟体验，15分钟认界面，20分钟做问候，15分钟测试重置，15分钟改编保存，15分钟分享。快组先做互测而非盲目增加功能。','table',table=[['时间','任务'],['0–10','体验问候与重置'],['10–25','认识组件和属性'],['25–45','制作点击问候'],['45–60','测试重置'],['60–75','排错、改编、保存'],['75–90','互测与展示']]),
slide('事件像门铃',['有人按门铃，铃声才响','有人点按钮，动作才开始','当……发生，就……'], '让学生分别扮演按钮和标签，按按钮卡片时标签同学举起问候牌。强调程序并非每条积木一直执行，本课动作由Click事件触发。'),
slide('组件设计中的按钮与标签',['按钮负责接收点击','标签负责展示文字','右侧属性决定初始外观'], '展示本课实际组件设计截图。指认GreetingLabel、HelloButton与ResetButton。设计器的外观预览不是正在运行的APP。','designer'),
slide('组件名与屏幕文字',['组件名帮助我们找到对象','Text是用户看见的文字','修改Text不会自动改组件名'], '本课保留英文组件名，方便对照积木与资料。中文可用于标签和按钮的可见文字；不要把整个项目命名限制误认为中文显示受限。','table',table=[['组件名','类型','作用'],['GreetingLabel','标签','显示提示与问候'],['HelloButton','按钮','发出问候'],['ResetButton','按钮','恢复初始提示']]),
slide('初始画面从属性开始',['选中GreetingLabel，再改Text','按钮文字让人看懂用途','文字不应被固定高度截住'], '让学生点选组件树中的标签，确认属性面板对应同一组件。若修改后屏幕没有变化，先检查是否选中了Screen1。适量放大字体，避免只为美观缩小可读文字。'),
slide('问候按钮的点击事件',['事件：HelloButton.Click','动作：设置GreetingLabel.Text','内容：一段文字'], '依次指认外层事件、内层属性设置与文字块。截图对应完整工程的问候按钮事件；学生Class版需要补上它。','blocks',blockIndex=1),
slide('文字块需要插入输入槽',['设置的是哪一个组件？','改变的是哪一项属性？','新的值是什么？'], '用三个问题读一条属性设置：GreetingLabel、Text、欢迎语。演示把文字块暂时拿开，让学生观察空输入槽，再立刻接回。不要把不完整积木作为可交作业。'),
slide('我的第一条事件',['给问候按钮连接Click事件','把文字设置到问候标签','先实现，再改写一句自己的问候'], '给学生8至10分钟独立/结对完成。巡视时只问“点哪个按钮、改哪个标签”，避免替学生拖完。要求文字文明友好且同伴能读懂。'),
slide('重置按钮恢复初始状态',['ResetButton.Click已在Class版中提供','它设置同一个标签的Text','它把文字恢复为最初的提示'], '截图对应重置按钮。让学生对照问候事件，只找出按钮名与文字值两个差别。重置不是重新导入工程，也不是撤销最近一次编辑。','blocks',blockIndex=2),
slide('按顺序预测屏幕文字',['先预测，再操作'], '让学生读动作序列，逐步说出最后屏幕文字。强调“设置”覆盖当前文字，而非追加。参考：问候→问候仍是一份欢迎语；问候→重置为初始提示。','table',table=[['动作顺序','最后显示'],['启动','准备好了吗？点一下按钮。'],['问候→问候','一份欢迎语'],['问候→重置','初始提示'],['重置→问候','欢迎语']]),
slide('测试不只点一次',['问候按钮至少点三次','问候后重置，再问候','记录实际看到的文字'], '为同伴分配操作者和记录者。记录者不能只打钩，还要读出实际文字。若班级暂无运行设备，先完成积木核对，并将实际运行栏明确标为待测。'),
slide('小故障的线索',['没变化：看事件是否连好','错地方：看组件名是否选对','没文字：看输入槽是否为空'], '只演示一个可逆故障，例如把设置目标临时换为按钮Text。让学生预测效果，再恢复。排错从看得见的现象回到具体事件。'),
slide('组件设计与逻辑设计',['组件设计：摆放对象、设置初始值','逻辑设计：事件发生后改变什么','两处描述的是同一个APP'], '让学生用左右手分别表示两个界面：一只手搭舞台，一只手决定互动。不要引入复杂架构术语；将“属性初始值”和“运行中设置”通过标签文字连接起来。'),
slide('AIA与APK的用途',['AIA：以后还能打开修改','APK：在Android环境安装运行','两种文件不互相代替'], '演示导出入口，不强制本节所有学生等待编译。AIA应与本课作品一起保存。APK运行与设备安装按教师已配置的课堂方式进行。'),
slide('保存后的检查',['找到刚导出的AIA文件','名称能分清课次和作者','不要只保留下载列表里的临时记录'], '让学生在文件夹中找到AIA，确认大小非0。工程内部名采用英文与数字，以兼容现有编译和导入规则；电脑上的课程文件夹可以用中文。'),
slide('一句问候也有设计选择',['面向新同学，还是家人？','按钮文字能否说明用途？','每次只改一项，再测试'], '学生改编欢迎语和按钮Text。提醒修改GreetingLabel初始文字后，重置事件也应同步，否则重置会恢复旧提示。提高组增加一个晚安按钮即可。'),
slide('同伴第一次打开作品',['不解释，让同伴先试用','问：你知道该点哪里吗？','把一个建议写在任务单上'], '两人交换操作者。记录一句具体建议，如“把按钮改成向你问好”，避免只写好看、好玩。课堂评价关注是否达成意图。'),
slide('我的事件说明',['当________发生','程序设置________的________','屏幕上的变化是________'], '邀请两组用完整句展示。参考：当HelloButton被点击，程序设置GreetingLabel的Text，屏幕显示欢迎语。学生也可先用中文描述，再补组件名。'),
slide('出口题：哪里需要修改？',['想让问候出现在标签上，却改了按钮上的字。','你会先检查哪一个积木？','连续点三次问候，为什么不会有三份文字？'], '参考答案：检查属性设置的组件选择，应为GreetingLabel；设置Text替换原文字，程序没有做追加。学生能说出原因比记住英文更重要。','question'),
slide('教师观察与分层',['基础：问候和重置都可解释','提高：完成一次有目的的文字改编','证据：AIA、互测记录、口头说明'], '量规建议功能4分、事件解释2分、测试2分、保存2分。若无运行设备，功能运行部分保持待评，不能用设计器截图替代运行验证。'),
slide('下一课：会互动的数字名片',['把一条问候扩展为多种介绍','按钮可以改变文字，也可以改变图片','本课资料来自MIT官方组件参考'], '来源：'+UI+'；'+LEARN+'。这是羽轩独立编写的课程序列，不是MIT官方课次。下课前确认AIA已保存，不把完整答案替代学生作业。')
]))

LESSONS.append(dict(
lesson=2,title='会互动的数字名片',projectName='Card02',exampleTitle='我的数字名片',durationMinutes=90,
goals=['用Image、Label和Button分别组织图像、信息与操作。','通过不同按钮的Click事件改变同一个InfoLabel.Text。','保护个人信息，制作一张别人能够自主操作的介绍卡。'],
exampleSpec={'summary':'名片以公开的昵称和原创头像介绍一位虚构同学；“认识我”显示简短介绍，“我的爱好”显示兴趣，“重置”恢复操作提示。','components':[{'name':'AvatarImage','type':'Image','role':'显示打包进工程的头像图片'},{'name':'InfoLabel','type':'Label','role':'显示介绍、爱好或初始提示'},{'name':'IntroButton','type':'Button','role':'显示自我介绍'},{'name':'HobbyButton','type':'Button','role':'显示兴趣内容'},{'name':'ResetButton','type':'Button','role':'恢复提示'}],'logic':[{'event':'IntroButton.Click','actions':['InfoLabel.Text ← 你好！我是小羽，喜欢观察和创造。']},{'event':'HobbyButton.Click','actions':['InfoLabel.Text ← 我的爱好：阅读、画画和编程。']},{'event':'ResetButton.Click','actions':['InfoLabel.Text ← 点下面的按钮认识我。']}],'scope':'名片不填写真实电话、家庭地址或账号密码；本课不做登录、二维码或联网名片。图片使用随工程提供的原创建议素材，不直接复制搜索图片。'},
versions={'answer':'Card02.aia：介绍、爱好、重置三个按钮事件完整。','class':'Card02Class.aia：界面、头像与 IntroButton.Click 演示已给出；学生补 HobbyButton.Click 和 ResetButton.Click。','starter':'Card02Starter.aia：保留相同界面、头像及初始属性，无任何积木。'},
agenda=agenda([(0,10,'1–3','展示名片，让学生以访客身份探索。','说出按钮、图片与信息的不同作用。','能指出名片中一项适合公开的信息。'),(10,25,'4–8','从第1课迁移事件，演示组件树与图片资源。','导入Class版，找到AvatarImage和InfoLabel。','图片路径对应工程媒体中的文件。'),(25,45,'9–12','解读认识我事件，只示范一次属性设置。','完成爱好按钮，反复切换介绍与爱好。','两按钮改变同一InfoLabel。'),(45,60,'13–15','引导学生独立完成重置，再做顺序预测。','补重置事件，按不同顺序测试。','重置恢复提示而非删除头像。'),(60,75,'16–19','组织安全改编与可读性检查。','替换公开昵称、爱好和许可素材，检查长文字。','不出现真实联系方式；长文能读完整。'),(75,90,'20–24','访客互测、介绍作品、出口题与导出。','同伴独立操作，记录一处修改，导出AIA。','说出事件与目标属性的对应关系。')]),
tasks=[{'title':'认出名片的组成','steps':['导入 Card02Class.aia，找到AvatarImage、InfoLabel及三个按钮。','选AvatarImage查看Picture，核对图片文件在媒体区存在。','阅读“认识我”按钮的积木，圈出目标组件与属性。'],'question':'Picture里的文件名和InfoLabel.Text里的介绍文字，分别给哪个组件用？','answer':'Picture为Image提供图片资源；InfoLabel.Text是标签显示的文字。'},{'title':'补全爱好按钮','steps':['从HobbyButton取出Click事件。','设置InfoLabel.Text为“我的爱好：阅读、画画和编程。”或自己的公开兴趣。','在运行环境交替点“认识我”和“我的爱好”，观察只有信息区变化。'],'question':'为什么两个按钮可以设置同一个标签？','answer':'每个按钮的事件在被点击时执行，分别为同一标签写入新文字，最后一次设置决定当前显示。'},{'title':'补重置并安全改编','steps':['添加ResetButton.Click，使InfoLabel.Text恢复“点下面的按钮认识我。”。','只使用昵称、公开兴趣和许可头像，避免真实联系方式。','测试长文字与不同点击顺序，然后导出AIA。'],'question':'改了设计器里的初始提示，重置事件需要改吗？','answer':'需要同步；重置事件写入自己的文字值，不会自动读取原来的设计属性。'}],
tests=[{'action':'首次启动','expected':'头像可见，信息区显示操作提示，三个按钮含义清楚。'},{'action':'点认识我','expected':'信息区显示介绍，头像没有消失。'},{'action':'点我的爱好，再点认识我','expected':'分别显示对应内容，最后显示介绍。'},{'action':'任一内容后点重置','expected':'恢复初始提示，按钮仍然可用。'},{'action':'把爱好改为较长的一句话','expected':'文字完整可读，没有重要内容被裁掉。'}],
challenges=[{'level':'基础','task':'补完爱好和重置，三条路径都可解释。'},{'level':'提高','task':'为有兴趣了解你的新同学改写介绍，让信息简短且有层次。'},{'level':'拓展','task':'增加一个“我的作品”按钮展示一项真实完成的作品；只发布适合公开的信息。'}],
misconceptions=[['点爱好后按钮文字改变了','属性设置选成了HobbyButton.Text，应设置InfoLabel.Text。'],['头像不显示','核对Picture文件名、大小写与媒体资源，不把本机绝对路径填作打包素材。'],['文字变长后显示不全','检查标签宽度和高度，优先自动高度、适当留白，不只缩小字体。']],
exitQuestions=[{'q':'两个按钮都设置InfoLabel.Text，最后屏幕由哪个事件决定？','a':'最近一次实际执行的设置决定当前文字。'},{'q':'能否把家庭地址写到班级公开名片？为什么？','a':'不应把家庭地址等敏感信息放入公开名片；用昵称和公开兴趣表达自己。'},{'q':'头像图片为什么要在工程媒体区存在？','a':'打包时工程需包含资源，才能在运行环境按Picture路径显示。'}],
sources=[{'title':'MIT用户界面组件参考','url':UI,'use':'核对Image.Picture、Label.Text与按钮Click的作用。'},{'title':'MIT布局组件参考','url':LAYOUT,'use':'核对Arrangement对内部组件的排列方式。'}],
componentMetadata={'Button':'8','Label':'6','Image':'8','VerticalArrangement':'4','HorizontalArrangement':'4'},
slides=[
slide('会互动的数字名片',['第2课 · 我的数字名片','图片、介绍和按钮共同讲述我是谁'], '回顾第1课：按钮事件能改变标签。这节课把一条问候扩展为可选择的信息。示例用虚构人物与原创建议头像，学生可安全改编。'),
slide('一位新同学打开名片',['他先想知道什么？','他会点哪个按钮？','哪些信息适合公开？'], '先让学生作为访客体验完整卡片。收集“名字、爱好、作品”等需求，明确不收集电话、地址和密码。','question'),
slide('名片的三个功能证据',['认识我：显示介绍','我的爱好：显示兴趣','重置：恢复阅读提示'], '展示三次点击，询问哪个区域始终不变。头像不必跟着每个事件改变，变化集中在InfoLabel能帮助学生理解组件作用。'),
slide('今天的90分钟',['从一条问候到多种信息'], '按表执行，25分钟后应让学生开始补事件，不把美化占满课堂。75分钟后保留互测和保存。','table',table=[['时间','任务'],['0–10','访客体验'],['10–25','图片与组件'],['25–45','爱好事件'],['45–60','重置与测试'],['60–75','安全改编'],['75–90','展示与保存']]),
slide('一张卡片中的三种角色',['Image承载图片','Label承载信息','Button提供选择'], '用纸卡片比喻：照片不会替你发出操作，按钮也不适合塞满介绍文字。要求学生用功能而不是外观判断组件。'),
slide('实际名片的组件设计',['头像在上方','信息区在中间','按钮让读者选择内容'], '展示本课真实Designer截图，按组件树逐个点选。问学生：InfoLabel在哪，AvatarImage在哪。不能把截图当运行结果。','designer'),
slide('图片从哪里来？',['上传到工程媒体区','Picture填写工程中的文件名','图片和AIA一起导出'], '演示查看媒体区，不要求从网络寻找头像。学校可选自绘头像；本机路径C盘某文件不能当成另一台手机也能读取的资源。'),
slide('名片的组件分工',['先找对象，再改属性'], '阅读组件名与类型，为后面事件建立索引。英文组件名帮助区分InfoLabel与标题Label；中文可见文字不受影响。','table',table=[['组件','类型','作用'],['AvatarImage','Image','头像'],['InfoLabel','Label','介绍/爱好/提示'],['IntroButton','Button','认识我'],['HobbyButton','Button','我的爱好'],['ResetButton','Button','恢复提示']]),
slide('认识我按钮的演示事件',['IntroButton.Click','设置InfoLabel.Text','新文字是一段简短介绍'], 'Class版已给出此事件。让学生逐行读出，不急于复制。截图对应完整工程的IntroButton.Click。','blocks',blockIndex=1),
slide('一个信息区可以显示多种内容',['按钮决定何时更新','标签决定在哪里显示','文字块决定显示什么'], '用三问法检查理解。切换内容是同一标签Text被改写，本课尚未涉及多页面或数据库。'),
slide('爱好按钮的学生任务',['新事件属于HobbyButton','新文字写在InfoLabel中','头像和其他按钮无需修改'], '给学生独立制作时间。若学生照搬Intro事件而忘改事件组件，运行时一个按钮可能承担错误工作，提醒逐项核对。'),
slide('爱好按钮的目标逻辑',['HobbyButton.Click','InfoLabel.Text变成爱好内容','最后一次点击决定当前信息'], '截图用于任务完成后的对照，不在操作前直接投出答案。请学生用手指出与介绍事件的两个差别。','blocks',blockIndex=2),
slide('重置按钮的目标逻辑',['ResetButton.Click','恢复“点下面的按钮认识我。”','保留头像与可点击按钮'], '先让学生独立完成，再显示截图。重置只负责信息文字，没有清空图片、重开Screen或删除工程。','blocks',blockIndex=3),
slide('顺序改变，结果会怎样？',['先预测最后的信息，再点击验证'], '答案：介绍→爱好显示爱好；爱好→介绍显示介绍；介绍→重置显示初始提示。让学生解释是最近执行的一次设置生效。','table',table=[['点击顺序','最后的信息'],['认识我→我的爱好','爱好内容'],['我的爱好→认识我','自我介绍'],['认识我→重置','初始提示'],['重置→我的爱好','爱好内容']]),
slide('一次完整的互测',['按钮与文字是否对应？','重置后还能继续选择吗？','图片始终可见吗？'], '观察者按任务单逐项记录。运行未配置时标待测；可以先核对事件结构，但不可把所有运行行直接打钩。'),
slide('公开名片的信息边界',['可以：昵称、兴趣、作品','谨慎：真人照片与学校细节','不写：地址、密码、真实联系方式'], '让学生判断三张信息卡。强调只公开自己愿意公开且有权使用的信息；他人照片需要许可，图片资源也要有使用权。'),
slide('读起来轻松的信息',['介绍用一两句话','按钮文字说明会出现什么','较长文字要检查换行'], '教师把爱好故意改长，观察布局是否截断。优先检查标签自动高度、宽度和换行空间，不以极小字体解决所有问题。'),
slide('图片不见时的检查路径',['资源文件是否还在媒体区？','Picture是否写对文件名？','图片组件是否可见且有尺寸？'], '按资源、路径、组件三个层次排查。示例照片不由联网URL加载，因此无需课堂网络获取头像。不要在错误信息没看清时反复上传同一文件。'),
slide('我的名片主题',['为谁介绍我？','我希望对方记住什么？','只改内容，也能形成新作品'], '学生安全替换昵称与公开兴趣，可保留示例头像。提高组添加作品按钮时仍需写明对象和测试步骤。'),
slide('访客测试最有价值',['让同伴不听说明先操作','记录他犹豫的地方','把一条建议变成修改'], '观察者不抢答。若对方把重置理解为删除名片，说明按钮Text可改成“回到提示”，而不是要求访客记住规则。'),
slide('我的名片说明',['这张名片介绍________','我用________按钮显示________','我保护个人信息的方法是________'], '挑选两种不同主题分享，评价事件与内容是否一致。让学生提到一次测试而不是只朗读界面文字。'),
slide('出口题：两个按钮，一个标签',['先点爱好，再点介绍，会显示什么？','Picture里为什么要有正确资源名？','怎样避免名片泄露隐私？'], '参考：显示介绍；文件名让Image找到打包资源；用昵称、公开兴趣，避开地址联系方式等敏感信息。','question'),
slide('教师观察与分层',['功能4分：三个按钮分别正确','解释2分：最近一次Text设置','测试与保存各2分'], '同时观察是否存在真实联系方式。隐私提醒应在学生公开前完成。尚无运行证据的行保持待测，图片能在Designer显示不能证明手机运行全部正常。'),
slide('下一课：会发声的伙伴',['从视觉反馈走向听觉反馈','按钮事件可以调用组件方法','参考：MIT用户界面与布局文档'], '来源：'+UI+'；'+LAYOUT+'。下节使用本地提示音和语音，提示音不冒充真实动物录音。收齐学生AIA，保留个人改编。')
]))

LESSONS.append(dict(
lesson=3,title='会发声的伙伴',projectName='Course03Voice',exampleTitle='伙伴声音盒',durationMinutes=90,
goals=['区分设置属性与调用方法：文字显示用Text，发声用Speak/Play。','参照小猫事件完成小狗事件，并能同时停止语音和短提示音。','记录声音资源路径、语音引擎前提与实际听觉测试结果。'],
exampleSpec={'summary':'小猫或小狗按钮先停止上一段语音，播放本地操作提示音feedback.wav，更新StatusLabel并调用PetSpeech.Speak进行中文自我介绍；停止按钮同时停止语音与短音并显示停止提示。','components':[{'name':'StatusLabel','type':'Label','role':'显示当前伙伴及停止反馈'},{'name':'CatButton','type':'Button','role':'小猫语音介绍'},{'name':'DogButton','type':'Button','role':'小狗语音介绍'},{'name':'StopButton','type':'Button','role':'停止发声'},{'name':'PetSpeech','type':'TextToSpeech','role':'把中文文字交给设备语音引擎朗读'},{'name':'FeedbackSound','type':'Sound','role':'播放工程中的短操作提示音feedback.wav'}],'logic':[{'event':'CatButton.Click','actions':['调用PetSpeech.Stop','调用FeedbackSound.Play','StatusLabel.Text ← 小猫：我是小猫，喵喵喵。','调用PetSpeech.Speak，message=我是小猫，喵喵喵']},{'event':'DogButton.Click','actions':['调用PetSpeech.Stop','调用FeedbackSound.Play','StatusLabel.Text ← 小狗：我是小狗，汪汪汪。','调用PetSpeech.Speak，message=我是小狗，汪汪汪']},{'event':'StopButton.Click','actions':['调用PetSpeech.Stop','调用FeedbackSound.Stop','StatusLabel.Text ← 声音已停止，再选一个伙伴吧。']}],'scope':'本课的动物介绍由TextToSpeech合成，不是动物录音；feedback.wav是独立的短提示音。中文朗读依赖设备已安装并可用的中文TTS引擎，不能由AIA编译成功推断声音可听。可选真实动物音频需教师提前准备自录或有许可的文件。'},
versions={'answer':'Course03Voice.aia：Cat、Dog、Stop三组事件完整，带feedback.wav本地短提示音。','class':'Course03VoiceClass.aia：组件、素材与CatButton.Click示范已给出；学生完成DogButton.Click和StopButton.Click。','starter':'Course03VoiceStarter.aia：相同界面、非可视组件及短音资源，积木为空。'},
agenda=agenda([(0,10,'1–3','演示看得见和听得见的两种反馈，说明素材性质。','先听，再区分提示音与合成语音。','知道不是加载真实动物录音。'),(10,25,'4–8','辨认非可视组件、Source路径、Speak方法与中文引擎。','导入Class，找到PetSpeech和FeedbackSound。','能说出Source=feedback.wav。'),(25,45,'9–12','逐条解读Cat事件，示范调用与属性设置的差异。','完成Dog事件，保持文字与语音一致。','message插入的是文字值。'),(45,60,'13–15','让学生独立设计停止事件，指导有序听觉测试。','补Stop事件，小猫→停止→小狗，记录实际反馈。','停止同时处理两个声音组件。'),(60,75,'16–19','定位无声原因，组织短句改编与音量礼仪。','检查媒体音量/资源/语音引擎，改编一段伙伴自我介绍。','区分“标签变了”和“真的发声”。'),(75,90,'20–24','同伴盲听、方法解释、出口题与导出。','交替测试，两人记录版本、设备与听到的内容。','未听到的结果标待测或问题，而非通过。')]),
tasks=[{'title':'找到两种声音来源','steps':['导入Course03VoiceClass.aia，选择非可视组件PetSpeech与FeedbackSound。','检查FeedbackSound.Source为feedback.wav，媒体区有同名文件。','确认教师测试环境中的中文语音引擎可用，媒体音量适中。'],'question':'feedback.wav和Speak输入的文字是同一种资源吗？','answer':'不是；Sound播放已有音频文件，TextToSpeech把文字交给设备语音引擎合成。'},{'title':'参照小猫制作小狗','steps':['阅读已提供的CatButton.Click，指出Stop、Play、标签设置和Speak。','添加DogButton.Click：先PetSpeech.Stop，再FeedbackSound.Play。','设置StatusLabel.Text为“小狗：我是小狗，汪汪汪。”，调用PetSpeech.Speak并传入“我是小狗，汪汪汪”。'],'question':'为什么改了StatusLabel.Text，还不能保证听到声音？','answer':'标签只负责显示，声音需要Speak调用以及可工作的设备语音引擎与音量设置。'},{'title':'停止发声并互测','steps':['添加StopButton.Click，依次调用PetSpeech.Stop和FeedbackSound.Stop。','把StatusLabel.Text设为“声音已停止，再选一个伙伴吧。”。','依次测试小猫→停止→小狗；避免多人同时高音量播放，再导出AIA。'],'question':'为什么停止按钮不只改成“已经停止”的文字？','answer':'文字反馈不等于停止声音，必须调用对应声音组件的停止方法。'}],
tests=[{'action':'点击小猫','expected':'状态显示小猫介绍；应听到短提示音及中文语音，实际结果分别记录。'},{'action':'点击小狗','expected':'状态显示小狗介绍；Speak的内容与小狗一致。'},{'action':'正在发声时点击停止','expected':'调用两个Stop方法，状态显示“声音已停止，再选一个伙伴吧。”；实际听觉另测。'},{'action':'停止后再选小猫','expected':'仍可重新发声，不必重启App。'},{'action':'在教师允许下将媒体音量调低再恢复','expected':'区分无声音量原因与程序事件原因，测试后恢复适中音量。'}],
challenges=[{'level':'基础','task':'完成Dog与Stop，准确解释显示和发声是不同动作。'},{'level':'提高','task':'把语音改成一种原创伙伴的简短介绍，保持屏幕文字和朗读内容一致。'},{'level':'拓展','task':'经教师确认许可后导入一段短录音，另建Sound播放；记录素材来源，不将提示音标成动物录音。'}],
misconceptions=[['标签更新了，所以声音一定正常','标签与声音是两个证据；逐项记录短音、语音、停止效果。'],['没有语音就反复拖Speak积木','先检查设备TTS引擎/中文语言包和媒体音量，再检查message输入及事件连接。'],['Source填写电脑绝对路径','打包素材使用工程媒体中的feedback.wav；另一台设备不能读取教师电脑路径。'],['用Sound播放很长背景音乐','较长音频可选Player；本课只用Sound短音，不包含Player组件。']],
exitQuestions=[{'q':'设置StatusLabel.Text与调用PetSpeech.Speak有什么区别？','a':'前者改变屏幕文字属性，后者请求语音引擎朗读文字。'},{'q':'停止按钮应调用哪两个方法？','a':'PetSpeech.Stop和FeedbackSound.Stop。'},{'q':'APK编译成功，能否证明每台设备一定能中文朗读？','a':'不能，还需设备中文TTS引擎、媒体音量等条件，并做实际声音测试。'}],
sources=[{'title':'MIT媒体组件参考：Sound、Player、TextToSpeech','url':MEDIA,'use':'核对短音播放、语音合成及对应方法；本课仅使用Sound和TextToSpeech。'},{'title':'MIT按钮和标签参考','url':UI,'use':'核对按钮Click与标签Text。'}],
componentMetadata={'Button':'8','Label':'6','Sound':'4','TextToSpeech':'6','Player':'8（可选讲解，未加入本课工程）'},
slides=[
slide('会发声的伙伴',['第3课 · 伙伴声音盒','一次点击，得到文字和声音两种反馈'], '开场请同学先安静聆听。明确示例里的喵喵与汪汪是语音引擎朗读拟声文字，短提示音是操作反馈，两者都不是动物实录。'),
slide('听到的声音来自哪里？',['一声短提示音','一句中文自我介绍','屏幕也显示伙伴名称'], '教师分两次展示：先指出短音，再听中文介绍。请学生区分声音文件与文字合成。没有可用设备时只讲机制，听觉结果写待测。','question'),
slide('今天的作品证据',['小猫与小狗各有自己的介绍','停止按钮能处理两个声音组件','我能区分显示和发声'], '目标不要求所有人增加图片或动物录音。核心是事件里可以有多个动作，调用方法会请求组件执行任务。'),
slide('90分钟的学习路线',['先理解来源，再制作和听测'], '声音课要保留排查环境时间，不让所有同学同时播放。根据班级设备数分组轮换听测。','table',table=[['时间','任务'],['0–10','体验两种反馈'],['10–25','组件与资源'],['25–45','制作小狗事件'],['45–60','停止与听测'],['60–75','排查与改编'],['75–90','分享与导出']]),
slide('可见组件与非可视组件',['按钮、标签放在界面上','声音组件不占界面位置','它们仍然属于同一个工程'], '让学生在组件树里找到PetSpeech与FeedbackSound。非可视不是不存在；通过事件中的方法块才能请求它们工作。'),
slide('声音盒的实际界面',['小猫、小狗供用户选择','状态区说明当前内容','停止按钮始终容易找到'], '展示真实Designer截图，指出底部非可视组件区。本页展示布局与组件，不证明声音已可播放。','designer'),
slide('声音文件与语音合成',['Sound：播放已有短音文件','TextToSpeech：朗读传入的文字','Player：可用于较长音频，本课不使用'], '按官方组件分类做简短比较。工程中的feedback.wav已随包提供；可选自录动物音频要说明来源和许可，不能假装本课已包含。','table',table=[['组件','本课输入','触发方法'],['FeedbackSound / Sound','feedback.wav','Play / Stop'],['PetSpeech / TextToSpeech','中文文字','Speak / Stop'],['Player（拓展）','较长音频','Start / Pause / Stop']]),
slide('Source与message各指什么？',['Source指向工程里的feedback.wav','message是一段要朗读的文字','中文语音依赖设备引擎和语言支持'], '先检查文件存在，再解释message输入槽。不要让学生把文件名写到Speak message然后误认为在播放文件；Speak只会尝试朗读该字符串。'),
slide('小猫事件的四个动作',['停止上一段语音','播放短提示音并更新标签','调用Speak传入小猫介绍'], '截图对应CatButton.Click。Class版已提供。沿连接从上读到下，说明语音播放是组件异步工作，不承诺短音结束后才开始语音。','blocks',blockIndex=1),
slide('设置属性与调用方法',['Text：屏幕上显示什么','Play：请Sound开始播放','Speak：请语音引擎开始朗读'], '用“状态”和“动作”的生活比喻区分。课堂不要求掌握异步术语，只需知道调用开始声音，不等于程序等到整段朗读完才继续。'),
slide('小狗事件的学生任务',['事件必须属于DogButton','语音与标签都写小狗','保留先Stop再Speak的顺序'], '给8至10分钟补事件。巡视时检查复制后是否仍写小猫、是否还在CatButton事件里。最少改动也要保持界面与声音语义一致。'),
slide('小狗事件的对照逻辑',['DogButton.Click','StatusLabel显示小狗介绍','PetSpeech.Speak：我是小狗，汪汪汪'], '完成任务后显示实际截图。让学生指出文本显示有“小狗：”前缀，Speak输入只朗读介绍内容，说明两个文字值并不必逐字相同但意思需一致。','blocks',blockIndex=2),
slide('停止按钮的对照逻辑',['PetSpeech.Stop停止语音','FeedbackSound.Stop停止短音','标签说明声音已停止'], '先让学生提出设计，再显示答案截图。只改标签是常见假完成；必须找到两个Stop调用。','blocks',blockIndex=3),
slide('听测时分别记录三件事',['短音有没有？','中文介绍有没有、内容对不对？','停止后的实际声音怎样？'], '若没有中文引擎，可能短音正常而语音失败。请学生分别记录，不使用一个总勾号掩盖不同证据。'),
slide('切换伙伴的顺序实验',['小猫→停止→小狗','小狗→小猫','停止→停止→小猫'], '本课先Stop可减少上一段语音继续占用的情况，实际队列行为仍由引擎处理。观察结果写实，不承诺所有设备响应时长相同。'),
slide('有文字却没有声音',['媒体音量是否合适？','feedback.wav是否存在？','中文语音引擎能否朗读？'], '采用从环境到资源再到事件的顺序排查。先用设备已知可用声音确认媒体音量；不把网络打开作为所有问题的默认答案。'),
slide('让声音服务使用者',['短句比长段更适合按钮反馈','屏幕文字为听不到的同伴提供线索','课堂轮流播放、使用适中音量'], '本课不以音量大和语速快作为趣味目标。提醒学生声音应该有停止入口，同时提供可读文字。'),
slide('可选录音的资源路径',['先取得录音的使用许可','上传到工程媒体区','Sound.Source使用准确文件名'], '教师可在拓展环节播放自录短音。较长录音可另用Player，但当前工程没有Player，不能按这页误以为直接存在。素材清单写作者、来源与许可。'),
slide('我的伙伴改编',['它是谁？想说一句什么？','标签与朗读是否一致？','同伴能否随时停止？'], '学生可将小狗改成机器人、图书管理员或原创动物伙伴。不要要求新增大量素材；改变角色、语气和使用场景也能形成有意义的改编。'),
slide('同伴盲听与看屏',['先听声音猜伙伴','再看标签核对内容','记录一次有证据的发现'], '一人操作一人记录，再交换。若设备无声音，改做积木对照并明确待测，不设计虚假的“都听到了”反馈。'),
slide('我的声音程序说明',['我用________显示文字','我用________发起语音','停止时我调用________'], '参考：StatusLabel；PetSpeech.Speak；PetSpeech.Stop和FeedbackSound.Stop。鼓励学生指出非可视组件的位置。'),
slide('出口题：一句“停止”够不够？',['只把标签改成“已停止”，声音会停吗？','Sound.Source和Speak message有什么区别？','编译成功等于中文朗读正常吗？'], '参考：不一定，必须调用Stop；Source指音频文件，message是待朗读文字；编译不能验证设备语音引擎和听觉效果。','question'),
slide('教师观察与分层',['功能：Dog与Stop结构完整','理解：显示、文件、合成语音能区分','证据：分别记录短音和语音测试'], '设备功能评分依实际听觉结果。可给结构与概念分，不能把设备不可用的声音结果判为已通过。保存有待测说明的任务单也有价值。'),
slide('下一课：我的故事小舞台',['让画面和文字一起切换','一个屏幕可以放多个场景容器','技术参考：MIT媒体与界面组件'], '来源：'+MEDIA+'；'+UI+'。交付的短音为操作提示，不是动物录音。下节沿用按钮事件，增加Visible属性来控制场景。')
]))

def align_actual(x):
    replacements={1:{'Hello01':'Course01Hello','准备好了吗？点一下按钮。':'我准备好和你打招呼了！','你好，欢迎来到我的第一个 APP！':'你好！这是我做的第一个手机 APP。','初始：准备好了吗？':'初始：我准备好和你打招呼了！'},2:{'Card02':'Course02Card','点下面的按钮认识我。':'欢迎认识我！点击下面的按钮。','你好！我是小羽，喜欢观察和创造。':'大家好，我是林小羽。我喜欢提出问题，也喜欢把想法做成作品。','我的爱好：阅读、画画和编程。':'我的爱好：画画、阅读和编程。我想做一个帮助同学的小工具。','“认识我”':'“我的介绍”','认识我：':'我的介绍：','认识我按钮':'我的介绍按钮','认识我→':'我的介绍→','→认识我':'→我的介绍','点认识我':'点我的介绍','认识我和':'我的介绍和'}}
    text=json.dumps(x,ensure_ascii=False)
    for old,new in replacements.get(x['lesson'],{}).items():text=text.replace(old,new)
    x=json.loads(text)
    if x['lesson']==2:
        x['exampleSpec']['components'].insert(1,{'name':'NameLabel','type':'Label','role':'显示姓名与当前介绍分类'})
        x['exampleSpec']['summary']='名片用虚构的“林小羽”和品牌标志头像介绍自己；“我的介绍”与“我的爱好”同时更新分类标题NameLabel及正文InfoLabel，“回到名片首页”恢复两处初始文字。'
        titles=['林小羽｜关于我','林小羽｜我的爱好','林小羽｜创意小队']
        for e,title in zip(x['exampleSpec']['logic'],titles):e['actions'].insert(0,'NameLabel.Text ← '+title)
        x['tasks'][1]['steps'].insert(2,'同时设置NameLabel.Text为“林小羽｜我的爱好”，使分类标题和正文一致。')
        x['tasks'][2]['steps'][0]='添加ResetButton.Click，同时把InfoLabel.Text恢复“欢迎认识我！点击下面的按钮。”、NameLabel.Text恢复“林小羽｜创意小队”。'
        for s in x['slides']:
            if s.get('layout')=='blocks':
                s['body'].append('同步更新NameLabel的分类标题')
                s['notes']+=' 实际事件还会设置NameLabel.Text，分类标题与正文必须同步更新。'
        x['versions']['class']='Course02CardClass.aia：界面、品牌标志头像与IntroButton.Click演示已给出；学生补HobbyButton.Click和ResetButton.Click，每个事件同步更新NameLabel与InfoLabel。'
        x['misconceptions'].append(['切换后正文变了但分类标题没变','检查是否遗漏NameLabel.Text设置；每个按钮都要同步处理标题和正文。'])
    spec=json.loads((ROOT.parent/'aia'/f"lesson{x['lesson']:02}"/'artifact-spec.json').read_text(encoding='utf8'))
    x['artifactSpec']='work/course56/aia/lesson%02d/artifact-spec.json'%x['lesson']
    x['actualScreenshotGroups']=spec['screenshotGroups']
    x['actualExpectedOutputs']=spec['tests']
    assert x['projectName']==spec['projectName'],(x['lesson'],x['projectName'],spec['projectName'])
    return x

def write_lesson(x):
    x=align_actual(x)
    p=ROOT/f"lesson{x['lesson']:02}"
    p.mkdir(parents=True,exist_ok=True)
    (p/'content.json').write_text(json.dumps(x,ensure_ascii=False,indent=2),encoding='utf8')
    def table(headers,rows):
        return '\n'.join(['| '+' | '.join(headers)+' |','| '+' | '.join(['---']*len(headers))+' |']+['| '+' | '.join(str(c).replace('\n','<br>') for c in r)+' |' for r in rows])
    src='\n'.join(f"- [{s['title']}]({s['url']})：{s['use']}" for s in x['sources'])
    versions=table(['版本','内容'],[[k,v] for k,v in [('完整答案',x['versions']['answer']),('课堂支架',x['versions']['class']),('纯界面起始版',x['versions']['starter'])]])
    plan=f"# 第{x['lesson']}课｜{x['title']}\n\n**项目：{x['exampleTitle']}　时长：90分钟　配套课件：{len(x['slides'])}页**\n\n## 课前准备\n\n本课采用“体验—预测—制作—改编—分享”的节奏。先向学生发课堂支架版，完成后再对照答案。纯界面版用于课后重建，避免90分钟都用于重复搭界面。\n\n{versions}\n\n运行使用教师已配置的Android设备或模拟器；组件设计器不执行点击逻辑。无设备时仍可做积木分析，但任务单的运行结果须写“待测”。\n\n## 学习目标与达标证据\n\n"+'\n'.join(f'{i+1}. {g}' for i,g in enumerate(x['goals']))+f"\n\n## 示例边界\n\n{x['exampleSpec']['summary']}\n\n{x['exampleSpec']['scope']}\n\n## 90分钟安排\n\n"+table(['时间','PPT页','教师组织','学生活动','检查点'],[[f"{r['start']:02}–{r['end']:02}",r['slides'],r['teacher'],r['students'],r['checkpoint']] for r in x['agenda']])+"\n\n每段示范以2至3分钟为宜，随后让学生立即操作；两人一组时每个任务交换操作者。\n\n## 核心任务与参考答案\n\n"
    for i,t in enumerate(x['tasks'],1):
        plan+=f"### 任务{i}：{t['title']}\n\n"+'\n'.join(f'{n}. {z}' for n,z in enumerate(t['steps'],1))+f"\n\n提问：{t['question']}\n\n参考：{t['answer']}\n\n"
    plan+='## 组件与程序核对\n\n'+table(['名称','类型','教学作用'],[[c['name'],c['type'],c['role']] for c in x['exampleSpec']['components']])+"\n\n"
    for e in x['exampleSpec']['logic']:
        plan+=f"- 当 `{e['event']}`："+'；'.join(e['actions'])+'。\n'
    plan+='\n## 结对测试清单\n\n'+table(['动作','期望结果','实际结果'],[[t['action'],t['expected'],'课堂填写'] for t in x['tests']])+"\n\n## 常见问题\n\n"+table(['现象或误解','排查提示'],x['misconceptions'])+'\n\n## 分层与评价\n\n'+'\n'.join(f"- **{c['level']}：**{c['task']}" for c in x['challenges'])+'\n\n建议功能与规则4分、概念解释2分、测试修正2分、工程保存2分。未完成设备运行的项目，运行分保持待评。\n\n## 出口题参考\n\n'+'\n'.join(f"{i+1}. {q['q']}\n   参考：{q['a']}" for i,q in enumerate(x['exitQuestions']))+'\n\n## 验证范围与来源\n\n本内容文件描述教学目标、预期逻辑与测试方法，不代表工程已完成导入、编译或Android运行验证。实际验证结果由课程包中的验证说明单独记录。\n\n'+src+'\n\n本课为独立编写的羽轩课程，不是MIT官方编号或官方课件。\n'
    (p/'教师教案.md').write_text(plan,encoding='utf8')
    sheet=f"# 第{x['lesson']}课｜{x['exampleTitle']}：学生任务单\n\n姓名：________　同伴：________　日期：________\n\n## 今天的目标\n\n"+'\n'.join('- '+g for g in x['goals'])+f"\n\n打开课堂支架 `{x['projectName']}Class.aia`。先观察作品，再作出预测，不要提前把完整答案覆盖到自己的作品上。\n\n## 观察与预测\n\n我准备让谁使用这个APP：________________。\n\n我预测点下第一个功能按钮后，________________会发生变化。\n\n"
    for i,t in enumerate(x['tasks'],1):
        sheet+=f"## 任务{i}：{t['title']}\n\n"+'\n'.join('- [ ] '+z for z in t['steps'])+f"\n\n想一想：{t['question']}\n\n我的解释：________________________________________________\n\n"
    sheet+='## 互测：交换操作者与观察者\n\n'+table(['动作','期望','实际观察/通过或待测'],[[t['action'],t['expected'],'________________'] for t in x['tests']])+'\n\n发现的问题：________________________________________________\n\n我期望：____________________________________________________\n\n实际发生：__________________________________________________\n\n我检查的事件、组件或属性：__________________________________\n\n修改后再测：________________________________________________\n\n## 我的微改编\n\n'+'\n'.join('- [ ] '+c['task'] for c in x['challenges'][1:])+'\n\n我改了________________，因为________________；我再次测试了________________。\n\n## 分享与出口题\n\n“我的作品给________使用。最关键的事件是________，它会________。同伴测试发现________，我改了________。”\n\n'+'\n\n'.join(f"{i+1}. {q['q']}\n\n   ________________________________________________________" for i,q in enumerate(x['exitQuestions']))+f"\n\n提交：自己导出的AIA、这份任务单、一个具体测试结果。建议工程内部名使用 `L{x['lesson']:02}MyApp` 这样的英文数字组合，课程文件夹可使用中文。\n"
    (p/'学生任务单.md').write_text(sheet,encoding='utf8')
    readme=f"# 第{x['lesson']}课｜{x['title']}\n\n这是一份90分钟课程的教学内容源稿，项目为**{x['exampleTitle']}**。\n\n{x['exampleSpec']['summary']}\n\n## 建议阅读顺序\n\n1. 教师教案：了解本课目标、90分钟安排和答疑。\n2. 学生任务单：按支架任务预测、制作、互测。\n3. PPT：文字与表格可编辑，逐页教师备注对应本教案。\n4. AIA：先发Class版，完成后再对照完整答案。\n\n## 三个工程版本\n\n{versions}\n\n## 当前内容说明\n\n`content.json` 是PPT与课程包装配的结构化源内容；此目录中的“工程名”描述交付规格，实际AIA/PPT/截图由制作流程装配到最终输出目录。不能据此声称导入、编译或设备运行已经通过。查看最终课程包的验证说明确认验证范围。\n\n导入路径：平台App Inventor → 项目 → 导入项目(.aia)。设计器预览不执行程序；运行需课堂已有Android环境。项目内部名采用英文数字以保持兼容；屏幕上的中文文字不受此限制。\n\n技术参考：\n\n{src}\n"
    (p/'先读我.md').write_text(readme,encoding='utf8')
    assert sum(z['minutes'] for z in x['agenda'])==90
    assert len(x['slides'])>=22
    assert 2 <= sum(s['layout']=='blocks' for s in x['slides']) <= 4
    return p

if __name__=='__main__':
    for lesson in LESSONS:
        print(write_lesson(lesson))
