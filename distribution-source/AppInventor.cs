using System;
using System.IO;
using System.Net;
using System.Net.Sockets;
using System.Diagnostics;
using System.Linq;
using System.Text;
using System.Threading;
using System.Windows.Forms;
using System.Drawing;
using System.Xml;
using System.Security.Cryptography;
using System.Runtime.InteropServices;

internal static class App {
  static string root=AppDomain.CurrentDomain.BaseDirectory, data, url, token, buildUrl;
  static Process web, build, usb;
  static StreamWriter log;
  static readonly object logLock=new object();
  static volatile bool stopping, ready;
  static bool headless, noBrowser;
  static IntPtr job;
  static Mutex desktopMutex;
  static string buildDrive, buildDriveTarget;
  static volatile bool finished;
  static Form form;
  static Label status;
  static string Q(string s) { return "\""+s.Replace("\"","\\\"")+"\""; }
  static string Join(params string[] args) { return String.Join(" ", args.Select(Q)); }
  static void Write(string s) { lock(logLock) { if(log!=null) log.WriteLine(DateTime.Now.ToString("s")+" "+s); } }
  static void Status(string s) { Write(s); if(form!=null && form.IsHandleCreated) form.BeginInvoke((Action)(()=>status.Text=s)); }
  static string RandomToken() { var b=new byte[32]; using(var rng=RandomNumberGenerator.Create()) rng.GetBytes(b); return BitConverter.ToString(b).Replace("-","").ToLowerInvariant(); }
  static int FreePort(int preferred) { var l=new TcpListener(IPAddress.Loopback,preferred); try { l.Start(); return ((IPEndPoint)l.LocalEndpoint).Port; } catch(SocketException) { return FreePort(0); } finally { l.Stop(); } }
  static string BuildPath() {
    if(data.All(c=>c<128) && data.Length<80)return data;
    // Legacy AAPT expects ANSI paths. A per-session DOS alias keeps all data in the user's directory.
    string target="\\??\\"+data; var existing=new StringBuilder(32768);
    for(char drive='Z';drive>='D';drive--) {
      string name=drive+":"; existing.Clear(); uint count=QueryDosDevice(name,existing,existing.Capacity);
      if(count>0) { if(existing.ToString()==target) {buildDrive=name;buildDriveTarget=target;return name+"\\";} continue; }
      if(Marshal.GetLastWin32Error()!=2)continue;
      if(DefineDosDevice(0x1|0x8,name,target)) {buildDrive=name;buildDriveTarget=target;return name+"\\";}
    }
    throw new Exception("没有可用的临时盘符供 Android 编译工具使用。请释放一个盘符后重试。");
  }
  static string Fetch(string address, bool post=false) {
    var r=(HttpWebRequest)WebRequest.Create(address); r.Proxy=null; r.Timeout=3000; r.ReadWriteTimeout=3000;
    if(post) { r.Method="POST"; r.Headers["X-Offline-Control"]=token; r.ContentLength=0; }
    using(var res=r.GetResponse()) using(var sr=new StreamReader(res.GetResponseStream())) return sr.ReadToEnd();
  }
  static void Browse() { if(url!=null) Process.Start(new ProcessStartInfo(url){UseShellExecute=true}); }
  static void CopyTree(string source,string dest) {
    Directory.CreateDirectory(dest);
    foreach(var f in Directory.GetFiles(source)) File.Copy(f,Path.Combine(dest,Path.GetFileName(f)),true);
    foreach(var d in Directory.GetDirectories(source)) { string n=Path.GetFileName(d); if(n!="authkey" && n!="keystore" && n!="appengine-generated") CopyTree(d,Path.Combine(dest,n)); }
  }
  static Process Run(string exe,string args,string cwd,string name,bool buildJava=false) {
    var p=new Process(); p.StartInfo=new ProcessStartInfo(exe,args){WorkingDirectory=cwd,UseShellExecute=false,CreateNoWindow=true,RedirectStandardOutput=true,RedirectStandardError=true,StandardOutputEncoding=Encoding.UTF8,StandardErrorEncoding=Encoding.UTF8};
    string j=Path.Combine(root,"runtime",buildJava?"java11":"java17");
    p.StartInfo.EnvironmentVariables["JAVA_HOME"]=j; p.StartInfo.EnvironmentVariables["PATH"]=Path.Combine(j,"bin")+";"+Environment.GetEnvironmentVariable("PATH");
    p.StartInfo.EnvironmentVariables.Remove("JAVA_TOOL_OPTIONS"); p.StartInfo.EnvironmentVariables.Remove("_JAVA_OPTIONS"); p.StartInfo.EnvironmentVariables.Remove("JDK_JAVA_OPTIONS");
    if(name=="usb") {
      p.StartInfo.EnvironmentVariables["YX_USB_TOKEN"]=token;
      p.StartInfo.EnvironmentVariables.Remove("PYTHONHOME"); p.StartInfo.EnvironmentVariables.Remove("PYTHONPATH");
    }
    p.OutputDataReceived+=(s,e)=>{if(e.Data!=null)Write("["+name+"] "+e.Data);}; p.ErrorDataReceived+=(s,e)=>{if(e.Data!=null)Write("["+name+"] "+e.Data);};
    p.Start(); if(!AssignProcessToJobObject(job,p.Handle)) { p.Kill(); throw new Exception("Cannot isolate child process ("+Marshal.GetLastWin32Error()+")."); }
    p.BeginOutputReadLine(); p.BeginErrorReadLine(); return p;
  }
  static void Key(string command,string auth) {
    var p=Run(Path.Combine(root,"runtime/java11/bin/java.exe"),Join("-Dfile.encoding=UTF-8","-jar",Path.Combine(root,"resources/KeyczarTool.jar"),command,"--location="+auth)+(command=="create"?" --purpose=crypt":command=="promote"?" --version=1":""),root,"key",true);
    p.WaitForExit(); if(p.ExitCode!=0) throw new Exception("Cannot initialize local encryption key."); p.Dispose();
  }
  static void Configure(string war,int wp,int bp) {
    var doc=new XmlDocument(); doc.PreserveWhitespace=true; string file=Path.Combine(war,"WEB-INF/appengine-web.xml"); doc.Load(file);
    var ns=new XmlNamespaceManager(doc.NameTable); ns.AddNamespace("a",doc.DocumentElement.NamespaceURI);
    Action<string,string> set=(n,v)=>{var node=doc.SelectSingleNode("//a:system-properties/a:property[@name='"+n+"']",ns); if(node==null)throw new Exception("Missing setting "+n); node.Attributes["value"].Value=v;};
    set("auth.usegoogle","false"); set("auth.uselocal","true"); set("require.tos","false"); set("localauth.mailserver",""); set("localauth.mailserver.password","");
    set("build.server.host","127.0.0.1:"+bp); set("build.server.password",token); set("appengine.host","localhost:"+wp); set("ios.build.server.host","");
    doc.SelectSingleNode("//a:sessions-enabled",ns).InnerText="true"; doc.Save(file);
  }
  static void Start() {
    Status("正在准备本地工作区……");
    string war=Path.Combine(data,"war"), marker=Path.Combine(data,"runtime-version.txt");
    string version=File.ReadAllText(Path.Combine(root,"resources/build-version.txt"));
    if(!File.Exists(marker)||File.ReadAllText(marker)!=version) { CopyTree(Path.Combine(root,"server/war"),war); File.WriteAllText(marker,version); }
    foreach(string n in new[]{"config","cache","temp"})Directory.CreateDirectory(Path.Combine(data,n));
    foreach(string keyName in new[]{"authkey","keystore"}) {
      string auth=Path.Combine(war,"WEB-INF",keyName);
      if(!File.Exists(Path.Combine(auth,"meta"))) { Directory.CreateDirectory(auth); Key("create",auth); Key("addkey",auth); Key("promote",auth); }
    }
    int wp=FreePort(8888),bp=FreePort(9990),up=FreePort(0); token=RandomToken(); url="http://127.0.0.1:"+wp+"/"; buildUrl="http://127.0.0.1:"+bp+"/buildserver/";
    Configure(war,wp,bp);
    File.WriteAllText(Path.Combine(data,"running.ini"),"url="+url+"\nbuildPort="+bp+"\nlauncherPid="+Process.GetCurrentProcess().Id+"\n");
    usb=Run(Path.Combine(root,"runtime/python3.13.16/python.exe"),Join("-I","-u",Path.Combine(root,"usb/server.py"),"--port",up.ToString(),"--app-port",wp.ToString(),"--data",Path.Combine(data,"usb")),root,"usb");
    Status("正在启动 APK 编译服务……"); string buildData=BuildPath();
    string lib=Path.Combine(root,"buildserver/lib");
    build=Run(Path.Combine(root,"runtime/java11/bin/java.exe"),Join("-Xmx3g","-Djava.net.preferIPv4Stack=true","-Dfile.encoding=UTF-8","-Dkeystore.pkcs12.legacy=true","-Djava.awt.headless=true","-Dappinventor.dexSeedDir="+Path.Combine(root,"buildserver/dex-seed"),"-Dappinventor.resourceSeedDir="+Path.Combine(root,"buildserver/resource-seed"),"-Djava.io.tmpdir="+Path.Combine(buildData,"temp"),"-cp",Path.Combine(root,"buildserver/classes")+";"+Path.Combine(lib,"*"),"com.google.appinventor.buildserver.BuildServer","--port",bp.ToString(),"--dexCacheDir",Path.Combine(buildData,"cache"),"--shutdownToken",token,"--buildserverPassword",token,"--requiredHosts","localhost"),lib,"build",true);
    Status("正在启动 App Inventor……"); string sdk=Path.Combine(root,"server/sdk");
    web=Run(Path.Combine(root,"runtime/java17/bin/java.exe"),Join("-Xmx2g","-Djava.net.preferIPv4Stack=true","-Dfile.encoding=UTF-8","-Dappengine.sdk.root="+sdk,"-Doffline.data="+data,"-Doffline.control.token="+token,"-Doffline.usb.port="+up,"--add-opens","java.base/java.net=ALL-UNNAMED","--add-opens","java.base/sun.net.www.protocol.http=ALL-UNNAMED","--add-opens","java.base/sun.net.www.protocol.https=ALL-UNNAMED","-cp",Path.Combine(sdk,"lib/appengine-tools-api.jar"),"com.google.appengine.tools.development.DevAppServerMain","--sdk_root="+sdk,"--disable_update_check","--port="+wp,"--address=127.0.0.1","."),war,"web");
    WaitReady(build,"http://127.0.0.1:"+bp+"/buildserver/health",null,90);
    WaitReady(usb,"http://127.0.0.1:"+up+"/health","YuxuanUsb/1",30);
    WaitReady(web,url+"login/_health","AppInventorOffline/1",120); ready=true;
    Status("已启动："+url+"\r\n关闭此窗口将保存数据并停止服务。"); if(!noBrowser)Browse();
    while(!stopping) { if(File.Exists(Path.Combine(data,"stop.request")))stopping=true; if(web.HasExited||build.HasExited||usb.HasExited)throw new Exception("本地服务意外停止，请检查日志。"); Thread.Sleep(500); }
  }
  static void WaitReady(Process p,string address,string expected,int seconds) {
    var timer=Stopwatch.StartNew(); while(timer.Elapsed.TotalSeconds<seconds) { if(stopping)throw new OperationCanceledException(); if(p.HasExited)throw new Exception("Service exited with code "+p.ExitCode); try { string s=Fetch(address); if(expected==null||s.Contains(expected))return; }catch(WebException){} Thread.Sleep(500); } throw new Exception("启动超时："+address);
  }
  static void Stop() {
    stopping=true; Status("正在保存项目并停止服务……");
    // Refuse new builds, then keep the callback server alive until active builds finish.
    if(build!=null&&!build.HasExited) {
      try {
        Fetch(buildUrl+"shutdown?token="+token);
        while(!build.HasExited) {
          string vars=Fetch(buildUrl+"vars");
          if(vars.Contains("<b>active-build-tasks</b> 0<br>"))break;
          Status("正在等待 APK 构建完成后退出……"); Thread.Sleep(2000);
        }
      }catch(Exception e){Write("Build shutdown: "+e.Message);}
    }
    if(web!=null&&!web.HasExited) { try { Fetch(url+"login/_shutdown",true); if(!web.WaitForExit(30000))Write("Web shutdown timed out."); } catch(Exception e){Write("Shutdown: "+e.Message);} }
    if(build!=null&&!build.HasExited) { try { build.Kill(); build.WaitForExit(5000); }catch(Exception e){Write(e.Message);} }
    if(job!=IntPtr.Zero) { CloseHandle(job); job=IntPtr.Zero; }
    if(buildDrive!=null) { DefineDosDevice(0x1|0x2|0x4|0x8,buildDrive,buildDriveTarget); buildDrive=null; }
    foreach(string n in new[]{"running.ini","stop.request"}) { string p=Path.Combine(data,n); if(File.Exists(p))File.Delete(p); }
    Write("Stopped.");
  }
  static void Work() { try { Start(); } catch(OperationCanceledException){} catch(Exception e) { Write(e.ToString()); if(!headless)MessageBox.Show(e.Message+"\n\n日志："+Path.Combine(data,"logs"),"App Inventor Offline",MessageBoxButtons.OK,MessageBoxIcon.Error); Environment.ExitCode=1; } finally { Stop(); finished=true; if(form!=null&&form.IsHandleCreated)form.BeginInvoke((Action)(()=>form.Close())); } }
  [STAThread] static void Main(string[] args) {
    data=Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData),"AppInventorOffline");
    for(int i=0;i<args.Length;i++) { if(args[i]=="--data-dir"&&i+1<args.Length)data=Path.GetFullPath(args[++i]); if(args[i]=="--headless")headless=true; if(args[i]=="--no-browser")noBrowser=true; }
    Directory.CreateDirectory(data);
    if(args.Contains("--stop")) { File.WriteAllText(Path.Combine(data,"stop.request"),""); return; }
    string hash; using(var sha=SHA256.Create()) hash=BitConverter.ToString(sha.ComputeHash(Encoding.UTF8.GetBytes(data.ToUpperInvariant()))).Replace("-","");
    bool created; using(var mutex=new Mutex(true,"Local\\AppInventorOffline-"+hash,out created)) {
      if(!created) { try { var line=File.ReadAllLines(Path.Combine(data,"running.ini")).First(x=>x.StartsWith("url=")); url=line.Substring(4); if(!noBrowser)Browse(); }catch{} return; }
      try {
        desktopMutex=new Mutex(false,"Local\\AppInventorOfflineDesktop");
        Directory.CreateDirectory(Path.Combine(data,"logs")); log=new StreamWriter(Path.Combine(data,"logs","launcher-"+DateTime.Now.ToString("yyyyMMdd-HHmmss")+".log"),false,Encoding.UTF8){AutoFlush=true};
        if(File.Exists(Path.Combine(data,"stop.request")))File.Delete(Path.Combine(data,"stop.request"));
        job=CreateJobObject(IntPtr.Zero,null); var info=new JOBOBJECT_EXTENDED_LIMIT_INFORMATION(); info.BasicLimitInformation.LimitFlags=0x2000;
        int size=Marshal.SizeOf(info); IntPtr ptr=Marshal.AllocHGlobal(size); try{Marshal.StructureToPtr(info,ptr,false); if(!SetInformationJobObject(job,9,ptr,(uint)size))throw new Exception("Cannot create process group.");}finally{Marshal.FreeHGlobal(ptr);}
        if(headless)Work(); else {
          Application.EnableVisualStyles(); form=new Form{Text="羽轩 · App Inventor",Icon=new Icon(Path.Combine(root,"resources/brand.ico")),BackColor=Color.White,ForeColor=Color.FromArgb(18,52,74),Width=580,Height=280,StartPosition=FormStartPosition.CenterScreen,FormBorderStyle=FormBorderStyle.FixedDialog,MaximizeBox=false};
          var brand=new PictureBox{Left=24,Top=20,Width=84,Height=84,SizeMode=PictureBoxSizeMode.Zoom,Image=Image.FromFile(Path.Combine(root,"resources/brand-logo.png"))};form.Controls.Add(brand);
          status=new Label{Left=126,Top=34,Width=404,Height=80,Text="正在启动……"}; form.Controls.Add(status);
          var open=new Button{Left=24,Top=160,Width=145,Height=32,Text="打开 App Inventor"}; open.Click+=(s,e)=>{if(ready)Browse();};form.Controls.Add(open);
          var exit=new Button{Left=344,Top=160,Width=145,Height=32,Text="保存并退出"};exit.Click+=(s,e)=>form.Close();form.Controls.Add(exit);
          foreach(var button in new[]{open,exit}){button.BackColor=Color.FromArgb(2,132,199);button.ForeColor=Color.White;button.FlatStyle=FlatStyle.Flat;button.FlatAppearance.BorderSize=0;button.Height=38;}
          var worker=new Thread(Work); worker.IsBackground=false;
          form.Shown+=(s,e)=>worker.Start(); form.FormClosing+=(s,e)=>{if(!finished){stopping=true;e.Cancel=true; status.Text="正在保存并退出，请稍候……";}};
          Application.Run(form); worker.Join();
        }
      }catch(Exception e){if(!headless)MessageBox.Show(e.Message,"App Inventor Offline");Environment.ExitCode=1;}finally{if(job!=IntPtr.Zero)CloseHandle(job); if(log!=null)log.Dispose();if(desktopMutex!=null)desktopMutex.Dispose();mutex.ReleaseMutex();}
    }
  }
  [StructLayout(LayoutKind.Sequential)] struct JOBOBJECT_BASIC_LIMIT_INFORMATION {public long PerProcessUserTimeLimit,PerJobUserTimeLimit;public uint LimitFlags;public UIntPtr MinimumWorkingSetSize,MaximumWorkingSetSize;public uint ActiveProcessLimit;public UIntPtr Affinity;public uint PriorityClass,SchedulingClass;}
  [StructLayout(LayoutKind.Sequential)] struct IO_COUNTERS {public ulong ReadOperationCount,WriteOperationCount,OtherOperationCount,ReadTransferCount,WriteTransferCount,OtherTransferCount;}
  [StructLayout(LayoutKind.Sequential)] struct JOBOBJECT_EXTENDED_LIMIT_INFORMATION {public JOBOBJECT_BASIC_LIMIT_INFORMATION BasicLimitInformation;public IO_COUNTERS IoInfo;public UIntPtr ProcessMemoryLimit,JobMemoryLimit,PeakProcessMemoryUsed,PeakJobMemoryUsed;}
  [DllImport("kernel32.dll",CharSet=CharSet.Unicode,SetLastError=true)] static extern IntPtr CreateJobObject(IntPtr a,string n);
  [DllImport("kernel32.dll",SetLastError=true)] static extern bool SetInformationJobObject(IntPtr h,int c,IntPtr p,uint n);
  [DllImport("kernel32.dll",SetLastError=true)] static extern bool AssignProcessToJobObject(IntPtr j,IntPtr p);
  [DllImport("kernel32.dll")] static extern bool CloseHandle(IntPtr h);
  [DllImport("kernel32.dll",CharSet=CharSet.Unicode,SetLastError=true)] static extern uint QueryDosDevice(string name,StringBuilder target,int size);
  [DllImport("kernel32.dll",CharSet=CharSet.Unicode,SetLastError=true)] static extern bool DefineDosDevice(uint flags,string name,string target);
}
