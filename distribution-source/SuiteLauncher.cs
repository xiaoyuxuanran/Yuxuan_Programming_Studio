using System;
using System.IO;
using System.Net;
using System.Diagnostics;
using System.Linq;
using System.Text;
using System.Threading;
using System.Drawing;
using System.Drawing.Drawing2D;
using System.Windows.Forms;
using System.Security.Cryptography;
using System.Runtime.InteropServices;
using System.Web.Script.Serialization;

internal static partial class Suite {
  static readonly string root=AppDomain.CurrentDomain.BaseDirectory;
  static string data,studioUrl,token,aiUrl,mixlyUrl,mixlyToken;
  static Process studio,core,mixly; static Form form; static Label status; static Button[] choices;
  static volatile bool closing;static bool noBrowser; static readonly object gate=new object(); static IntPtr job;
  static string Q(string value) { return "\""+value.Replace("\"","\\\"").TrimEnd('\\')+"\""; }
  static string RandomToken() {var b=new byte[32];using(var rng=RandomNumberGenerator.Create())rng.GetBytes(b);return BitConverter.ToString(b).Replace("-","").ToLowerInvariant();}
  internal static bool ToolInstalled(string mode) {
    if(mode=="ai")return File.Exists(Path.Combine(root,"AppInventorCore.exe"));
    if(mode=="mixly")return File.Exists(Path.Combine(root,"mixly/runtime/Mixly.exe"));
    if(!File.Exists(Path.Combine(root,"studio/server.py")))return false;
    return File.Exists(Path.Combine(root,mode=="python"?"runtime/python3.8.9/python.exe":"runtime/llvm-mingw/bin/clang++.exe"));
  }
  static void EnableInstalledChoices(){foreach(var button in choices)button.Enabled=licensed&&ToolInstalled((string)button.Tag);}
  static void Update(string message) {if(form!=null && form.IsHandleCreated)form.BeginInvoke((Action)(()=>status.Text=message));}
  static Process Spawn(string exe,string args,string workingDirectory=null) {
    var info=new ProcessStartInfo(exe,args){UseShellExecute=false,CreateNoWindow=true,WindowStyle=ProcessWindowStyle.Hidden,WorkingDirectory=workingDirectory??root};
    info.EnvironmentVariables.Remove("PYTHONHOME");info.EnvironmentVariables.Remove("PYTHONPATH");
    var p=Process.Start(info);if(job!=IntPtr.Zero&&!AssignProcessToJobObject(job,p.Handle)){p.Kill();throw new Exception("无法管理本地服务进程。");}return p;
  }
  static string Get(string address) {var r=(HttpWebRequest)WebRequest.Create(address);r.Proxy=null;r.Timeout=2000;using(var res=r.GetResponse())using(var reader=new StreamReader(res.GetResponseStream()))return reader.ReadToEnd();}
  static void Browse(string address) {if(!noBrowser&&!closing)Process.Start(new ProcessStartInfo(address){UseShellExecute=true});}
  static void StartStudio(string mode) {
    if(studio==null||studio.HasExited) {
      Update("正在启动代码工作区……");string folder=Path.Combine(data,"studio");Directory.CreateDirectory(folder);
      string running=Path.Combine(folder,"studio-running.json");if(File.Exists(running))File.Delete(running);
      token=RandomToken();studio=Spawn(Path.Combine(root,"runtime/python3.13.16/python.exe"),"-X utf8 "+Q(Path.Combine(root,"studio/server.py"))+" --data "+Q(folder)+" --token "+token);
      var timer=Stopwatch.StartNew();studioUrl=null;
      while(timer.Elapsed.TotalSeconds<30&&!closing) {
        if(studio.HasExited)throw new Exception("代码工作区启动失败。");
        try{var info=new JavaScriptSerializer().DeserializeObject(File.ReadAllText(running)) as System.Collections.Generic.Dictionary<string,object>;string address="http://127.0.0.1:"+info["port"]+"/";if(Get(address+"health").Contains("YuxuanStudio")){studioUrl=address;break;}}catch{}
        Thread.Sleep(200);
      }
      if(studioUrl==null&&!closing)throw new Exception("代码工作区启动超时。");
    }
    if(!closing){Browse(studioUrl+"?mode="+mode+"#"+token);Update((mode=="python"?"Python":"C++")+" 工作区已打开 · 可继续选择其他工具");}
  }
  static void StartAI() {
    if(core==null||core.HasExited) {
      Update("正在启动 App Inventor 和 APK 编译服务……");
      core=Spawn(Path.Combine(root,"AppInventorCore.exe"),"--headless --no-browser --data-dir "+Q(data));aiUrl=null;var timer=Stopwatch.StartNew();
      while(timer.Elapsed.TotalSeconds<240&&!closing) {
        if(core.HasExited)throw new Exception("App Inventor 启动失败，请重试。");
        try{string address=File.ReadAllLines(Path.Combine(data,"running.ini")).First(x=>x.StartsWith("url=")).Substring(4);if(Get(address+"login/_health").Contains("AppInventorOffline/1")){aiUrl=address;break;}}catch{}
        Thread.Sleep(500);
      }
      if(aiUrl==null&&!closing)throw new Exception("App Inventor 启动超时。");
    }
    if(!closing){Browse(aiUrl);Update("App Inventor 已打开 · 默认使用旧布局");}
  }
  static void MixlyCommand(string command) {
    var r=(HttpWebRequest)WebRequest.Create(mixlyUrl+command);r.Proxy=null;r.Timeout=3000;r.Method="POST";r.Headers["X-Suite-Token"]=mixlyToken;r.ContentLength=0;using(var response=r.GetResponse()){}
  }
  static void StartMixly() {
    if(mixly==null||mixly.HasExited){
      Update("正在启动 Mixly 硬件编程……");string folder=Path.Combine(data,"mixly");Directory.CreateDirectory(folder);string running=Path.Combine(folder,"mixly-running.json");if(File.Exists(running))File.Delete(running);
      string runtime=Path.Combine(root,"mixly/runtime");mixlyToken=RandomToken();mixly=Spawn(Path.Combine(runtime,"Mixly.exe"),"--data-dir "+Q(folder)+" --suite-token "+mixlyToken,runtime);mixlyUrl=null;var timer=Stopwatch.StartNew();
      while(timer.Elapsed.TotalSeconds<90&&!closing){if(mixly.HasExited)throw new Exception("Mixly 启动失败，请重试。");try{var info=new JavaScriptSerializer().DeserializeObject(File.ReadAllText(running)) as System.Collections.Generic.Dictionary<string,object>;string address="http://127.0.0.1:"+info["port"]+"/";if(Get(address+"health").Contains("YuxuanMixly")){mixlyUrl=address;break;}}catch{}Thread.Sleep(200);}
      if(mixlyUrl==null&&!closing)throw new Exception("Mixly 首次启动超时，请重试。");
    }else MixlyCommand("focus");
    if(!closing)Update("Mixly 已打开 · 四类开发板、云端库、串口调试与驱动下载");
  }
  static void Launch(string mode) {
    if(!ToolInstalled(mode)){MessageBox.Show(form,"此项目尚未安装，请重新运行完整安装包，勾选需要添加的项目。","羽轩编程工作台");return;}
    if(!licensed){ShowActivation("请先激活软件。");return;}
    foreach(var b in choices)b.Enabled=false;
    ThreadPool.QueueUserWorkItem(_=>{try{lock(gate){if(!closing&&licensed){if(mode=="ai")StartAI();else if(mode=="mixly")StartMixly();else StartStudio(mode);}}}catch(Exception e){Update(e.Message);if(!closing)form.BeginInvoke((Action)(()=>MessageBox.Show(form,e.Message,"羽轩编程工作台",MessageBoxButtons.OK,MessageBoxIcon.Error)));}finally{if(!closing&&form.IsHandleCreated)form.BeginInvoke((Action)(()=>{EnableInstalledChoices();}));}});
  }
  static void StopTools() {
    lock(gate) {
      if(mixly!=null&&!mixly.HasExited){try{if(mixlyUrl!=null)MixlyCommand("shutdown");}catch{}while(!mixly.WaitForExit(1000)){Update("请在 Mixly 中保存项目并关闭窗口，以完成退出……");}}
      if(studio!=null&&!studio.HasExited) {try{var r=(HttpWebRequest)WebRequest.Create(studioUrl+"api/shutdown");r.Proxy=null;r.Timeout=3000;r.Method="POST";r.Headers["X-Studio-Token"]=token;r.ContentType="application/json";var bytes=Encoding.UTF8.GetBytes("{}");r.ContentLength=bytes.Length;using(var stream=r.GetRequestStream())stream.Write(bytes,0,bytes.Length);using(var response=r.GetResponse()){}studio.WaitForExit(10000);}catch{} }
      // Core clears stale requests while starting; repeat so an early stop survives that cleanup.
      if(core!=null&&!core.HasExited){try{File.WriteAllText(Path.Combine(data,"stop.request"),"");while(!core.WaitForExit(1000)){File.WriteAllText(Path.Combine(data,"stop.request"),"");Update("正在保存 App Inventor 项目，等待正在进行的构建结束……");}}catch{}}
      studio=null;core=null;mixly=null;studioUrl=null;aiUrl=null;mixlyUrl=null;
    }
  }
  static void Shutdown() {StopTools();StopLicense();lock(gate){if(job!=IntPtr.Zero){CloseHandle(job);job=IntPtr.Zero;}}}
  static Label TextLabel(string text,float size,Color color,bool bold=false) {return new Label{AutoSize=true,Text=text,Font=new Font("Microsoft YaHei UI",size,bold?FontStyle.Bold:FontStyle.Regular),ForeColor=color,Margin=new Padding(0,0,0,12)};}
  static Button Card(TableLayoutPanel parent,string name,string caption,string detail,int column,int row,string mode) {
    var panel=new Panel{Dock=DockStyle.Fill,BackColor=Color.White,Padding=new Padding(16),Margin=new Padding(7)};
    panel.Paint+=(s,e)=>{using(var pen=new Pen(Color.FromArgb(212,230,243)))e.Graphics.DrawRectangle(pen,0,0,panel.Width-1,panel.Height-1);};
    var stack=new TableLayoutPanel{Dock=DockStyle.Fill,ColumnCount=1,RowCount=6,Margin=new Padding(0)};stack.ColumnStyles.Add(new ColumnStyle(SizeType.Percent,100));
    for(int i=0;i<4;i++)stack.RowStyles.Add(new RowStyle(SizeType.AutoSize));stack.RowStyles.Add(new RowStyle(SizeType.Percent,100));stack.RowStyles.Add(new RowStyle(SizeType.Absolute,44));
    var badge=new Label{Width=74,Height=32,Text=mode=="ai"?"AI":mode=="python"?"Py":mode=="mixly"?"Mixly":"C++",BackColor=Color.FromArgb(227,244,255),ForeColor=Color.FromArgb(17,127,192),Font=new Font("Segoe UI",12,FontStyle.Bold),TextAlign=ContentAlignment.MiddleCenter,Margin=new Padding(0,0,0,10)};stack.Controls.Add(badge,0,0);
    var title=TextLabel(name,14,Color.FromArgb(32,59,82),true);var intro=TextLabel(caption,9,Color.FromArgb(73,101,122));var extra=TextLabel(detail,8,Color.FromArgb(125,145,161));
    title.Margin=new Padding(0,0,0,6);intro.Margin=new Padding(0,0,0,6);extra.Margin=new Padding(0,0,0,6);
    stack.Controls.Add(title,0,1);stack.Controls.Add(intro,0,2);stack.Controls.Add(extra,0,3);stack.SizeChanged+=(s,e)=>{int width=Math.Max(130,stack.ClientSize.Width);foreach(var label in new[]{title,intro,extra})label.MaximumSize=new Size(width,0);};
    bool installed=ToolInstalled(mode);if(!installed)extra.Text="未安装 · 可通过完整安装包添加";
    var button=new Button{Tag=mode,Dock=DockStyle.Fill,Text=(installed?"启动 ":"未安装 · ")+name,BackColor=Color.FromArgb(21,131,207),ForeColor=Color.White,FlatStyle=FlatStyle.Flat,Font=new Font("Microsoft YaHei UI",9,FontStyle.Bold),Margin=new Padding(0,4,0,0)};button.FlatAppearance.BorderSize=0;button.Click+=(s,e)=>Launch(mode);stack.Controls.Add(button,0,5);panel.Controls.Add(stack);parent.Controls.Add(panel,column,row);return button;
  }
  internal static Button BuildLauncherForm() {
        form=new Form{Text="羽轩编程工作台",Icon=new Icon(Path.Combine(root,"resources/brand.ico")),ClientSize=new Size(940,730),MinimumSize=new Size(900,750),BackColor=Color.FromArgb(241,248,253),StartPosition=FormStartPosition.CenterScreen,AutoScaleDimensions=new SizeF(96,96),AutoScaleMode=AutoScaleMode.Dpi};
        var layout=new TableLayoutPanel{Dock=DockStyle.Fill,ColumnCount=1,RowCount=3,Padding=new Padding(24)};layout.ColumnStyles.Add(new ColumnStyle(SizeType.Percent,100));layout.RowStyles.Add(new RowStyle(SizeType.AutoSize));layout.RowStyles.Add(new RowStyle(SizeType.Percent,100));layout.RowStyles.Add(new RowStyle(SizeType.AutoSize));form.Controls.Add(layout);
        var header=new TableLayoutPanel{Dock=DockStyle.Top,AutoSize=true,AutoSizeMode=AutoSizeMode.GrowAndShrink,ColumnCount=2,RowCount=1,Margin=new Padding(7,0,7,15)};header.ColumnStyles.Add(new ColumnStyle(SizeType.Absolute,120));header.ColumnStyles.Add(new ColumnStyle(SizeType.Percent,100));header.RowStyles.Add(new RowStyle(SizeType.AutoSize));
        header.Controls.Add(new PictureBox{Width=96,Height=96,Anchor=AnchorStyles.Top|AnchorStyles.Left,SizeMode=PictureBoxSizeMode.Zoom,Margin=new Padding(0,8,0,8),Image=Image.FromFile(Path.Combine(root,"resources/brand-logo.png"))},0,0);
        var headings=new TableLayoutPanel{Dock=DockStyle.Top,AutoSize=true,AutoSizeMode=AutoSizeMode.GrowAndShrink,ColumnCount=1,RowCount=4,Margin=new Padding(0),Padding=new Padding(0,8,0,8)};headings.ColumnStyles.Add(new ColumnStyle(SizeType.Percent,100));for(int i=0;i<4;i++)headings.RowStyles.Add(new RowStyle(SizeType.AutoSize));
        var headingTitle=TextLabel("羽轩编程工作台",22,Color.FromArgb(24,69,103),true);headingTitle.Margin=new Padding(0,0,0,8);headings.Controls.Add(headingTitle,0,0);var tagline=TextLabel("从积木到代码，让创作更简单。",10,Color.FromArgb(73,111,142));tagline.Margin=new Padding(0,0,0,6);headings.Controls.Add(tagline,0,1);licenseInfo=TextLabel("正在检查授权……",8,Color.FromArgb(96,138,168));licenseInfo.Margin=new Padding(0);headings.Controls.Add(licenseInfo,0,2);
        headings.SizeChanged+=(s,e)=>{int width=Math.Max(1,headings.ClientSize.Width-headings.Padding.Horizontal);foreach(var label in new[]{headingTitle,tagline,licenseInfo})if(label.MaximumSize.Width!=width)label.MaximumSize=new Size(width,0);};header.Controls.Add(headings,1,0);layout.Controls.Add(header,0,0);
        var updates=new FlowLayoutPanel{AutoSize=true,Dock=DockStyle.Top,Margin=new Padding(0,9,0,0),WrapContents=true};updates.Controls.Add(new Label{Text="v"+ProductVersion,AutoSize=true,Margin=new Padding(0,7,12,0),ForeColor=Color.FromArgb(96,138,168)});foreach(bool checkUpdate in new[]{false,true}){bool checkNow=checkUpdate;var updateButton=new Button{Text=checkNow?"检查更新":"更新日志",AutoSize=true,Height=30,FlatStyle=FlatStyle.Flat,BackColor=Color.White,ForeColor=Color.FromArgb(43,97,135),Margin=new Padding(0,0,8,0)};updateButton.FlatAppearance.BorderColor=Color.FromArgb(196,219,236);updateButton.Click+=(s,e)=>ShowUpdates(checkNow);updates.Controls.Add(updateButton);}headings.Controls.Add(updates,0,3);
        var cards=new TableLayoutPanel{Dock=DockStyle.Fill,ColumnCount=2,RowCount=2,Margin=new Padding(0)};for(int i=0;i<2;i++){cards.ColumnStyles.Add(new ColumnStyle(SizeType.Percent,50));cards.RowStyles.Add(new RowStyle(SizeType.Percent,50));}layout.Controls.Add(cards,0,1);
        choices=new[]{Card(cards,"App Inventor","可视化 Android 应用开发","经典布局 · 蓝白主题 · 本机 APK 构建",0,0,"ai"),Card(cards,"Mixly 桌面编程","AVR / ESP8266 / ESP32 / Python ESP32","云端库 · 串口调试 · 驱动下载",1,0,"mixly"),Card(cards,"Python","脚本、绘图与图形窗口","3.8.9 / 3.13.16 · 清华源 pip · 图形库",0,1,"python"),Card(cards,"C++","编辑、编译与运行一键完成","内置 Clang++ · 项目文件树 · Light / Dark",1,1,"cpp")};
        foreach(var choice in choices)choice.Enabled=false;
        var footer=new TableLayoutPanel{Dock=DockStyle.Top,AutoSize=true,AutoSizeMode=AutoSizeMode.GrowAndShrink,MinimumSize=new Size(0,66),ColumnCount=3,RowCount=1,Padding=new Padding(7,15,7,0)};footer.RowStyles.Add(new RowStyle(SizeType.AutoSize));footer.ColumnStyles.Add(new ColumnStyle(SizeType.Percent,100));footer.ColumnStyles.Add(new ColumnStyle(SizeType.Absolute,130));footer.ColumnStyles.Add(new ColumnStyle(SizeType.Absolute,138));layout.Controls.Add(footer,0,2);
        status=new Label{Dock=DockStyle.Fill,Margin=new Padding(0),Text="准备就绪 · 选择任意工具开始",Font=new Font("Microsoft YaHei UI",9),ForeColor=Color.FromArgb(76,111,138),TextAlign=ContentAlignment.MiddleLeft};footer.Controls.Add(status,0,0);
        var activation=new Button{Dock=DockStyle.Fill,AutoSize=true,MinimumSize=new Size(0,40),Text="激活 / 验证授权",FlatStyle=FlatStyle.Flat,BackColor=Color.White,ForeColor=Color.FromArgb(43,97,135),Font=new Font("Microsoft YaHei UI",8),Margin=new Padding(0,0,10,5)};activation.FlatAppearance.BorderColor=Color.FromArgb(196,219,236);activation.Click+=(s,e)=>ShowActivation(null);footer.Controls.Add(activation,1,0);
        var exit=new Button{Dock=DockStyle.Fill,AutoSize=true,MinimumSize=new Size(0,40),Text="保存并退出",FlatStyle=FlatStyle.Flat,BackColor=Color.White,ForeColor=Color.FromArgb(43,97,135),Font=new Font("Microsoft YaHei UI",9),Margin=new Padding(0,0,0,5)};exit.FlatAppearance.BorderColor=Color.FromArgb(196,219,236);exit.Click+=(s,e)=>form.Close();footer.Controls.Add(exit,2,0);
    return exit;
  }
  static void RunHeadless(string[] args) {
    bool stop=args.Contains("--stop");headlessMode=!stop;Process process=null;
    try {
      if(!stop){Directory.CreateDirectory(data);if(!AuthorizeHeadless()){Environment.ExitCode=4;return;}}
      lock(gate){
        // A timer or network check can invalidate authorization before Core is registered.
        if(!stop&&(!licensed||Interlocked.CompareExchange(ref headlessLicenseLost,0,0)!=0)){Environment.ExitCode=4;return;}
        process=Process.Start(new ProcessStartInfo(Path.Combine(root,"AppInventorCore.exe"),String.Join(" ",args.Select(Q))){UseShellExecute=false,CreateNoWindow=true});
        if(!stop)core=process;
      }
      process.WaitForExit();Environment.ExitCode=!stop&&Interlocked.CompareExchange(ref headlessLicenseLost,0,0)!=0?4:process.ExitCode;
    }finally{
      closing=true;StopLicense();
      // StopTools may still be waiting for Core's graceful shutdown; retain this local reference.
      lock(gate){if(Object.ReferenceEquals(core,process))core=null;if(process!=null)process.Dispose();}
    }
  }
  [STAThread] static void Main(string[] args) {
    // Preview never enters the launcher or touches activation/user data.
    if(args.Contains("--preview-startup-animation")) {Application.EnableVisualStyles();Application.SetCompatibleTextRenderingDefault(false);using(var preview=new StartupAnimation())preview.ShowDialog();return;}
    data=Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData),"AppInventorOffline");for(int i=0;i<args.Length;i++)if(args[i]=="--data-dir"&&i+1<args.Length)data=Path.GetFullPath(args[++i]);
    // Retain the existing automation and graceful-stop command line.
    if(args.Contains("--headless")||args.Contains("--stop")){RunHeadless(args);return;}
    noBrowser=args.Contains("--no-browser");Directory.CreateDirectory(data);string hash;using(var sha=SHA256.Create())hash=BitConverter.ToString(sha.ComputeHash(Encoding.UTF8.GetBytes(data.ToUpperInvariant()))).Replace("-","");
    bool created;using(var mutex=new Mutex(true,"Local\\YuxuanStudioSuite-"+hash,out created)){
      if(!created){MessageBox.Show("羽轩编程工作台已运行，请在任务栏中打开启动器。","羽轩编程工作台");return;}
      using(var installerMutex=new Mutex(false,"Local\\AppInventorOfflineDesktop"))try {
        job=CreateJobObject(IntPtr.Zero,null);var info=new JOB_LIMIT();info.Basic.LimitFlags=0x2000;int size=Marshal.SizeOf(info);var ptr=Marshal.AllocHGlobal(size);try{Marshal.StructureToPtr(info,ptr,false);if(!SetInformationJobObject(job,9,ptr,(uint)size))throw new Exception("无法创建服务进程组。");}finally{Marshal.FreeHGlobal(ptr);}
        Application.EnableVisualStyles();Application.SetCompatibleTextRenderingDefault(false);
        // Decoration only: skipping this cannot skip the authorization below.
        if(!args.Contains("--no-startup-animation"))try{using(var splash=new StartupAnimation())splash.ShowDialog();}catch{ /* A display/asset failure must never block startup. */ }
        var exit=BuildLauncherForm();
        form.Shown+=(s,e)=>QueueLicenseCheck(true);
        bool done=false;form.FormClosing+=(s,e)=>{if(!done){e.Cancel=true;if(!closing){closing=true;foreach(var b in choices)b.Enabled=false;exit.Enabled=false;Update("正在停止运行任务并保存项目……");ThreadPool.QueueUserWorkItem(_=>{Shutdown();done=true;if(form.IsHandleCreated)form.BeginInvoke((Action)(()=>form.Close()));});}}};Application.Run(form);
      }catch(Exception e){MessageBox.Show(e.Message,"羽轩编程工作台");Environment.ExitCode=1;}finally{Shutdown();mutex.ReleaseMutex();}
    }
    InstallPendingUpdate();
  }
  static void InstallPendingUpdate() {if(pendingInstaller!=null)Process.Start(new ProcessStartInfo(pendingInstaller,"/DIR="+Q(root)){UseShellExecute=true});}
  [StructLayout(LayoutKind.Sequential)] struct BASIC {public long Time1,Time2;public uint LimitFlags;public UIntPtr Working1,Working2;public uint Active;public UIntPtr Affinity;public uint Priority,Schedule;}
  [StructLayout(LayoutKind.Sequential)] struct COUNTERS {public ulong A,B,C,D,E,F;}
  [StructLayout(LayoutKind.Sequential)] struct JOB_LIMIT {public BASIC Basic;public COUNTERS Io;public UIntPtr ProcessMemory,JobMemory,PeakProcess,PeakJob;}
  [DllImport("kernel32.dll",CharSet=CharSet.Unicode,SetLastError=true)]static extern IntPtr CreateJobObject(IntPtr a,string n);
  [DllImport("kernel32.dll",SetLastError=true)]static extern bool SetInformationJobObject(IntPtr h,int c,IntPtr p,uint n);
  [DllImport("kernel32.dll",SetLastError=true)]static extern bool AssignProcessToJobObject(IntPtr j,IntPtr p);
  [DllImport("kernel32.dll")]static extern bool CloseHandle(IntPtr h);
  // Original native artwork inspired by dsh-startup-screen's staged introduction.
  // No third-party voice/video assets, network requests or authorization decisions.
  internal sealed class StartupAnimation : Form {
    readonly System.Windows.Forms.Timer frames=new System.Windows.Forms.Timer{Interval=16};
    readonly Stopwatch clock=new Stopwatch();
    readonly Image logo;
    readonly Font titleFont=new Font("Microsoft YaHei UI",32,FontStyle.Bold,GraphicsUnit.Pixel);
    readonly Font smallFont=new Font("Microsoft YaHei UI",16,FontStyle.Regular,GraphicsUnit.Pixel);
    readonly Font monoFont=new Font("Consolas",13,FontStyle.Regular,GraphicsUnit.Pixel);
    readonly Font brandFont=new Font("Segoe UI",19,FontStyle.Bold,GraphicsUnit.Pixel);
    readonly Button skip;
    const double Duration=7.2;
    static readonly Color Ink=Color.FromArgb(22,64,96),Blue=Color.FromArgb(21,131,207),Muted=Color.FromArgb(100,135,158);
    internal StartupAnimation() {
      Text="羽轩编程工作台 · 启动动画";FormBorderStyle=FormBorderStyle.None;StartPosition=FormStartPosition.CenterScreen;
      AutoScaleMode=AutoScaleMode.None;KeyPreview=true;DoubleBuffered=true;BackColor=Color.FromArgb(244,250,255);
      var area=Screen.FromPoint(Cursor.Position).WorkingArea;
      float scale=Math.Min(1.25f,Math.Min((area.Width-48)/1100f,(area.Height-48)/700f));scale=Math.Max(.4f,scale);
      ClientSize=new Size((int)(1100*scale),(int)(700*scale));
      try{Icon=new Icon(Path.Combine(root,"resources/brand.ico"));using(var original=Image.FromFile(Path.Combine(root,"resources/brand-logo.png")))logo=new Bitmap(original);}catch{}
      skip=new Button{Text="跳过动画  Esc",AccessibleName="跳过动画，进入工作台",FlatStyle=FlatStyle.Flat,BackColor=Color.White,ForeColor=Ink,TabIndex=0};
      skip.FlatAppearance.BorderColor=Color.FromArgb(192,219,237);skip.Click+=(s,e)=>Close();Controls.Add(skip);Resize+=(s,e)=>PlaceSkip();PlaceSkip();
      frames.Tick+=(s,e)=>{if(clock.Elapsed.TotalSeconds>=Duration){Close();return;}Invalidate();};
      Shown+=(s,e)=>{clock.Restart();frames.Start();skip.Focus();};
    }
    void PlaceSkip(){float s=ClientSize.Width/1100f;skip.SetBounds((int)(900*s),(int)(30*s),(int)(166*s),(int)(38*s));var oldFont=skip.Font;skip.Font=new Font("Microsoft YaHei UI",Math.Max(8,12*s),FontStyle.Regular,GraphicsUnit.Pixel);if(oldFont!=null&&!oldFont.IsSystemFont)oldFont.Dispose();}
    protected override bool ProcessCmdKey(ref Message msg,Keys keyData){if(keyData==Keys.Escape){Close();return true;}return base.ProcessCmdKey(ref msg,keyData);}
    protected override void Dispose(bool disposing){if(disposing){frames.Stop();frames.Dispose();clock.Stop();if(logo!=null)logo.Dispose();titleFont.Dispose();smallFont.Dispose();monoFont.Dispose();brandFont.Dispose();if(skip!=null)skip.Font.Dispose();}base.Dispose(disposing);}
    static float Clamp(double n){return (float)Math.Max(0,Math.Min(1,n));}
    static float Ease(double n){float t=Clamp(n);return 1-(1-t)*(1-t)*(1-t);}
    void TextAt(Graphics g,string text,Font font,Color color,float x,float y,float w,float h,bool center=false,float opacity=1){using(var b=new SolidBrush(Color.FromArgb((int)(255*Clamp(opacity)),color)))using(var f=new StringFormat{Alignment=center?StringAlignment.Center:StringAlignment.Near,LineAlignment=StringAlignment.Center,FormatFlags=StringFormatFlags.NoWrap})g.DrawString(text,font,b,new RectangleF(x,y,w,h),f);}
    void LogoAt(Graphics g,float x,float y,float size,float alpha){
      if(logo==null){TextAt(g,"YX",titleFont,Blue,x,y,size,size,true,alpha);return;}
      var state=g.Save();using(var clip=new GraphicsPath()){clip.AddEllipse(x,y,size,size);g.SetClip(clip);using(var attributes=new System.Drawing.Imaging.ImageAttributes()){var matrix=new System.Drawing.Imaging.ColorMatrix();matrix.Matrix33=Clamp(alpha);attributes.SetColorMatrix(matrix);g.DrawImage(logo,new Rectangle((int)x,(int)y,(int)size,(int)size),0,0,logo.Width,logo.Height,GraphicsUnit.Pixel,attributes);}}g.Restore(state);
    }
    protected override void OnPaint(PaintEventArgs e){base.OnPaint(e);RenderFrame(e.Graphics,clock.Elapsed.TotalSeconds);}
    internal void RenderFrame(Graphics g,double t){
      var saved=g.Save();g.ScaleTransform(ClientSize.Width/1100f,ClientSize.Height/700f);g.SmoothingMode=SmoothingMode.AntiAlias;g.TextRenderingHint=System.Drawing.Text.TextRenderingHint.AntiAliasGridFit;
      using(var bg=new LinearGradientBrush(new Rectangle(0,0,1100,700),Color.White,Color.FromArgb(229,244,255),45))g.FillRectangle(bg,0,0,1100,700);
      using(var grid=new Pen(Color.FromArgb(16,21,131,207))){for(int x=0;x<1100;x+=40)g.DrawLine(grid,x,0,x,700);for(int y=0;y<700;y+=40)g.DrawLine(grid,0,y,1100,y);}
      using(var border=new Pen(Color.FromArgb(165,205,231)))g.DrawRectangle(border,0,0,1099,699);
      TextAt(g,"YUXUAN / PROGRAMMING STUDIO",brandFont,Ink,38,28,700,32);
      TextAt(g,"羽轩编程工作台   /   从积木到代码，让创作更简单。",smallFont,Muted,38,62,780,30);
      if(t<1.4){
        float p=Ease(t/.7),size=144+12*p;LogoAt(g,550-size/2,210-size/2,size,p);
        TextAt(g,"羽轩编程工作台",titleFont,Ink,100,320+18*(1-p),900,62,true,p);
        TextAt(g,"CREATE  /  CONNECT  /  EXPLORE",monoFont,Blue,100,389,900,30,true,p);
        if(t>1.1)using(var wash=new SolidBrush(Color.FromArgb((int)(Clamp((t-1.1)/.3)*190),Color.White)))g.FillRectangle(wash,0,110,1100,470);
      }else{
        double local=t-1.4;int phase=Math.Min(4,(int)(local/1.0));float p=Ease((local-phase)/.35);
        float rotation=(float)(local*13);var center=new PointF(550,292);
        using(var soft=new Pen(Color.FromArgb(37,21,131,207),1))g.DrawArc(soft,335,77,430,430,115,310);
        for(int i=0;i<96;i++){double a=(i*3.75+rotation)*Math.PI/180;if(Math.Sin(a)>.9)continue;float r=i%8==0?205:211;using(var pen=new Pen(i%8==0?Color.FromArgb(120,Blue):Color.FromArgb(45,Blue),i%8==0?2:1))g.DrawLine(pen,center.X+(float)Math.Cos(a)*r,center.Y+(float)Math.Sin(a)*r,center.X+(float)Math.Cos(a)*217,center.Y+(float)Math.Sin(a)*217);}
        using(var pen=new Pen(Blue,2)){g.DrawArc(pen,354,96,392,392,rotation+190,65);g.DrawArc(pen,365,107,370,370,100-rotation,34);}
        LogoAt(g,513,152,74,1);
        string[] zh={"让想法，成为作品","从积木开始创造","让代码连接世界","探索不止一种可能","欢迎进入创作空间"};
        string[] en={"IDEAS INTO REALITY","BUILD WITH BLOCKS","CONNECT THE PHYSICAL WORLD","EXPLORE WITH CODE","WELCOME TO YUXUAN STUDIO"};
        TextAt(g,zh[phase],titleFont,Ink,130,263+12*(1-p),840,65,true,p);
        int length=Math.Min(en[phase].Length,(int)(Math.Max(0,local-phase)*52));
        TextAt(g,en[phase].Substring(0,length)+(length<en[phase].Length?"_":""),monoFont,Blue,120,329,860,34,true);
        string[] details={"图形化编程  /  软件开发  /  智能硬件","App Inventor · 8 阶段 56 课教学项目","Mixly · AVR / ESP8266 / ESP32 / Python ESP32","Python 3.8.9 / 3.13.16 · C++ / Clang++","从积木到代码，让创作更简单。"};
        TextAt(g,details[phase],smallFont,Muted,90,385,920,35,true,p);
        TextAt(g,"0"+(phase+1)+" / 05",monoFont,Blue,475,442,150,30,true);
        if(t>6.4){float reveal=Ease((t-6.4)/.65);using(var b=new SolidBrush(Color.FromArgb((int)((1-reveal)*65),Blue)))g.FillRectangle(b,0,120,1100*(1-reveal),440);}
      }
      string[] tools={"APP INVENTOR","MIXLY","PYTHON","C++"};
      for(int i=0;i<4;i++){float x=114+i*224;bool active=t>1.5+i*.9;using(var b=new SolidBrush(active?Color.FromArgb(225,242,254):Color.FromArgb(247,251,254)))g.FillRectangle(b,x,541,200,45);using(var pen=new Pen(active?Color.FromArgb(151,204,239):Color.FromArgb(214,230,241)))g.DrawRectangle(pen,x,541,200,45);TextAt(g,tools[i],monoFont,active?Blue:Muted,x,541,200,45,true);}
      using(var pen=new Pen(Color.FromArgb(185,215,236)))g.DrawLine(pen,38,625,1062,625);
      using(var pen=new Pen(Blue,2))g.DrawLine(pen,38,625,38+1024*Clamp(t/Duration),625);
      TextAt(g,"YUXUAN  /  创作序章",monoFont,Muted,38,644,480,25);
      TextAt(g,"v"+Suite.ProductVersion+"   ·   Esc 跳过动画",smallFont,Muted,730,642,332,30);
      g.Restore(saved);
    }
  }
}
