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
    if(!licensed){ShowActivation("请先激活软件。");return;}
    foreach(var b in choices)b.Enabled=false;
    ThreadPool.QueueUserWorkItem(_=>{try{lock(gate){if(!closing&&licensed){if(mode=="ai")StartAI();else if(mode=="mixly")StartMixly();else StartStudio(mode);}}}catch(Exception e){Update(e.Message);if(!closing)form.BeginInvoke((Action)(()=>MessageBox.Show(form,e.Message,"羽轩编程工作台",MessageBoxButtons.OK,MessageBoxIcon.Error)));}finally{if(!closing&&form.IsHandleCreated)form.BeginInvoke((Action)(()=>{foreach(var b in choices)b.Enabled=licensed;}));}});
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
    var button=new Button{Dock=DockStyle.Fill,Text="启动 "+name,BackColor=Color.FromArgb(21,131,207),ForeColor=Color.White,FlatStyle=FlatStyle.Flat,Font=new Font("Microsoft YaHei UI",9,FontStyle.Bold),Margin=new Padding(0,4,0,0)};button.FlatAppearance.BorderSize=0;button.Click+=(s,e)=>Launch(mode);stack.Controls.Add(button,0,5);panel.Controls.Add(stack);parent.Controls.Add(panel,column,row);return button;
  }
  internal static Button BuildLauncherForm() {
        form=new Form{Text="羽轩编程工作台",Icon=new Icon(Path.Combine(root,"resources/brand.ico")),ClientSize=new Size(940,730),MinimumSize=new Size(900,750),BackColor=Color.FromArgb(241,248,253),StartPosition=FormStartPosition.CenterScreen,AutoScaleDimensions=new SizeF(96,96),AutoScaleMode=AutoScaleMode.Dpi};
        var layout=new TableLayoutPanel{Dock=DockStyle.Fill,ColumnCount=1,RowCount=3,Padding=new Padding(24)};layout.ColumnStyles.Add(new ColumnStyle(SizeType.Percent,100));layout.RowStyles.Add(new RowStyle(SizeType.AutoSize));layout.RowStyles.Add(new RowStyle(SizeType.Percent,100));layout.RowStyles.Add(new RowStyle(SizeType.AutoSize));form.Controls.Add(layout);
        var header=new TableLayoutPanel{Dock=DockStyle.Top,AutoSize=true,AutoSizeMode=AutoSizeMode.GrowAndShrink,ColumnCount=2,RowCount=1,Margin=new Padding(7,0,7,15)};header.ColumnStyles.Add(new ColumnStyle(SizeType.Absolute,120));header.ColumnStyles.Add(new ColumnStyle(SizeType.Percent,100));header.RowStyles.Add(new RowStyle(SizeType.AutoSize));
        header.Controls.Add(new PictureBox{Width=96,Height=96,Anchor=AnchorStyles.Top|AnchorStyles.Left,SizeMode=PictureBoxSizeMode.Zoom,Margin=new Padding(0,8,0,8),Image=Image.FromFile(Path.Combine(root,"resources/brand-logo.png"))},0,0);
        var headings=new TableLayoutPanel{Dock=DockStyle.Top,AutoSize=true,AutoSizeMode=AutoSizeMode.GrowAndShrink,ColumnCount=1,RowCount=3,Margin=new Padding(0),Padding=new Padding(0,8,0,8)};headings.ColumnStyles.Add(new ColumnStyle(SizeType.Percent,100));for(int i=0;i<3;i++)headings.RowStyles.Add(new RowStyle(SizeType.AutoSize));
        var headingTitle=TextLabel("羽轩编程工作台",22,Color.FromArgb(24,69,103),true);headingTitle.Margin=new Padding(0,0,0,8);headings.Controls.Add(headingTitle,0,0);var tagline=TextLabel("从积木到代码，让创作更简单。",10,Color.FromArgb(73,111,142));tagline.Margin=new Padding(0,0,0,6);headings.Controls.Add(tagline,0,1);licenseInfo=TextLabel("正在检查授权……",8,Color.FromArgb(96,138,168));licenseInfo.Margin=new Padding(0);headings.Controls.Add(licenseInfo,0,2);
        headings.SizeChanged+=(s,e)=>{int width=Math.Max(1,headings.ClientSize.Width-headings.Padding.Horizontal);foreach(var label in new[]{headingTitle,tagline,licenseInfo})if(label.MaximumSize.Width!=width)label.MaximumSize=new Size(width,0);};header.Controls.Add(headings,1,0);layout.Controls.Add(header,0,0);
        var cards=new TableLayoutPanel{Dock=DockStyle.Fill,ColumnCount=2,RowCount=2,Margin=new Padding(0)};for(int i=0;i<2;i++){cards.ColumnStyles.Add(new ColumnStyle(SizeType.Percent,50));cards.RowStyles.Add(new RowStyle(SizeType.Percent,50));}layout.Controls.Add(cards,0,1);
        choices=new[]{Card(cards,"App Inventor","可视化 Android 应用开发","经典布局 · 蓝白主题 · 本机 APK 构建",0,0,"ai"),Card(cards,"Mixly 硬件编程","AVR / ESP8266 / ESP32 / Python ESP32","云端扩展库 · 串口调试 · 驱动下载",1,0,"mixly"),Card(cards,"Python","脚本、绘图与图形窗口","3.8.9 / 3.13.16 · 清华源 pip · 图形库",0,1,"python"),Card(cards,"C++","编辑、编译与运行一键完成","内置 Clang++ · 项目文件树 · Light / Dark",1,1,"cpp")};
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
    data=Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData),"AppInventorOffline");for(int i=0;i<args.Length;i++)if(args[i]=="--data-dir"&&i+1<args.Length)data=Path.GetFullPath(args[++i]);
    // Retain the existing automation and graceful-stop command line.
    if(args.Contains("--headless")||args.Contains("--stop")){RunHeadless(args);return;}
    noBrowser=args.Contains("--no-browser");Directory.CreateDirectory(data);string hash;using(var sha=SHA256.Create())hash=BitConverter.ToString(sha.ComputeHash(Encoding.UTF8.GetBytes(data.ToUpperInvariant()))).Replace("-","");
    bool created;using(var mutex=new Mutex(true,"Local\\YuxuanStudioSuite-"+hash,out created)){
      if(!created){MessageBox.Show("羽轩编程工作台已运行，请在任务栏中打开启动器。","羽轩编程工作台");return;}
      using(var installerMutex=new Mutex(false,"Local\\AppInventorOfflineDesktop"))try {
        job=CreateJobObject(IntPtr.Zero,null);var info=new JOB_LIMIT();info.Basic.LimitFlags=0x2000;int size=Marshal.SizeOf(info);var ptr=Marshal.AllocHGlobal(size);try{Marshal.StructureToPtr(info,ptr,false);if(!SetInformationJobObject(job,9,ptr,(uint)size))throw new Exception("无法创建服务进程组。");}finally{Marshal.FreeHGlobal(ptr);}
        Application.EnableVisualStyles();Application.SetCompatibleTextRenderingDefault(false);
        var exit=BuildLauncherForm();
        form.Shown+=(s,e)=>QueueLicenseCheck(true);
        bool done=false;form.FormClosing+=(s,e)=>{if(!done){e.Cancel=true;if(!closing){closing=true;foreach(var b in choices)b.Enabled=false;exit.Enabled=false;Update("正在停止运行任务并保存项目……");ThreadPool.QueueUserWorkItem(_=>{Shutdown();done=true;if(form.IsHandleCreated)form.BeginInvoke((Action)(()=>form.Close()));});}}};Application.Run(form);
      }catch(Exception e){MessageBox.Show(e.Message,"羽轩编程工作台");Environment.ExitCode=1;}finally{Shutdown();mutex.ReleaseMutex();}
    }
  }
  [StructLayout(LayoutKind.Sequential)] struct BASIC {public long Time1,Time2;public uint LimitFlags;public UIntPtr Working1,Working2;public uint Active;public UIntPtr Affinity;public uint Priority,Schedule;}
  [StructLayout(LayoutKind.Sequential)] struct COUNTERS {public ulong A,B,C,D,E,F;}
  [StructLayout(LayoutKind.Sequential)] struct JOB_LIMIT {public BASIC Basic;public COUNTERS Io;public UIntPtr ProcessMemory,JobMemory,PeakProcess,PeakJob;}
  [DllImport("kernel32.dll",CharSet=CharSet.Unicode,SetLastError=true)]static extern IntPtr CreateJobObject(IntPtr a,string n);
  [DllImport("kernel32.dll",SetLastError=true)]static extern bool SetInformationJobObject(IntPtr h,int c,IntPtr p,uint n);
  [DllImport("kernel32.dll",SetLastError=true)]static extern bool AssignProcessToJobObject(IntPtr j,IntPtr p);
  [DllImport("kernel32.dll")]static extern bool CloseHandle(IntPtr h);
}
