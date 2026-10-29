using System;
using System.IO;
using System.Text;
using System.Threading;
using System.Drawing;
using System.Windows.Forms;
using System.Diagnostics;
using System.Collections.Generic;
using System.Web.Script.Serialization;
using System.Net.NetworkInformation;
using System.Runtime.InteropServices;

internal static partial class Suite {
  static volatile bool licensed;
  static volatile bool headlessMode;static int headlessLicenseLost;
  static Label licenseInfo;static Form licenseDialog;
  static Process licenseBridge;static readonly object licenseGate=new object();
  static System.Threading.Timer licenseTimer;static int licenseChecking;
  static bool networkSubscribed;
  static bool InternetConnected() {
    object manager=null;
    try{var type=Type.GetTypeFromCLSID(new Guid("DCB00C01-570F-4A9B-8D69-199FDBA5723B"));manager=Activator.CreateInstance(type);return (bool)type.InvokeMember("IsConnectedToInternet",System.Reflection.BindingFlags.GetProperty,null,manager,null);}
    catch{return NetworkInterface.GetIsNetworkAvailable();}
    finally{if(manager!=null&&Marshal.IsComObject(manager))Marshal.FinalReleaseComObject(manager);}
  }
  static Dictionary<string,object> LicenseRequest(string action,string code=null) {
    lock(licenseGate){
      if(closing)throw new OperationCanceledException("软件正在退出。");
      if(licenseBridge==null||licenseBridge.HasExited){
        var info=new ProcessStartInfo(Path.Combine(root,"runtime/python3.13.16/python.exe"),"-X utf8 "+Q(Path.Combine(root,"license/gate.py"))+" --state "+Q(Path.Combine(data,"license"))){UseShellExecute=false,CreateNoWindow=true,WindowStyle=ProcessWindowStyle.Hidden,WorkingDirectory=root,RedirectStandardInput=true,RedirectStandardOutput=true,RedirectStandardError=true,StandardOutputEncoding=Encoding.UTF8,StandardErrorEncoding=Encoding.UTF8};
        info.EnvironmentVariables.Remove("PYTHONHOME");info.EnvironmentVariables.Remove("PYTHONPATH");info.EnvironmentVariables["PYTHONIOENCODING"]="utf-8";
        licenseBridge=Process.Start(info);if(job!=IntPtr.Zero&&!AssignProcessToJobObject(job,licenseBridge.Handle)){licenseBridge.Kill();throw new Exception("无法管理授权验证进程。");}licenseBridge.ErrorDataReceived+=(s,e)=>{};licenseBridge.BeginErrorReadLine();
      }
      var request=new Dictionary<string,object>{{"action",action},{"online",InternetConnected()}};if(code!=null)request["code"]=code;
      licenseBridge.StandardInput.WriteLine(new JavaScriptSerializer().Serialize(request));licenseBridge.StandardInput.Flush();
      var read=licenseBridge.StandardOutput.ReadLineAsync();if(!read.Wait(45000)){licenseBridge.Kill();throw new Exception("授权服务响应超时，请检查网络后重试。");}
      string line=read.Result;if(String.IsNullOrEmpty(line))throw new Exception("授权验证进程未正常响应，请重新启动软件。");
      var response=new JavaScriptSerializer().DeserializeObject(line) as Dictionary<string,object>;if(response==null)throw new Exception("授权验证响应无效。");return response;
    }
  }
  static bool LicenseOK(Dictionary<string,object> result){return result.ContainsKey("ok")&&result["ok"] is bool&&(bool)result["ok"];}
  static string LicenseMessage(Dictionary<string,object> result){return result.ContainsKey("message")?Convert.ToString(result["message"]):"授权验证失败，请重试。";}
  static string ExpiryText(Dictionary<string,object> result){if(!result.ContainsKey("expires")||result["expires"]==null)return "永久授权";return "有效期至 "+new DateTime(1970,1,1,0,0,0,DateTimeKind.Utc).AddSeconds(Convert.ToDouble(result["expires"])).ToLocalTime().ToString("yyyy-MM-dd HH:mm");}
  static void ApplyLicense(Dictionary<string,object> result){
    bool lost;
    lock(licenseGate){
      if(closing)return;
      bool wasLicensed=licensed;licensed=LicenseOK(result);lost=wasLicensed&&!licensed;
      if(lost&&headlessMode)Interlocked.Exchange(ref headlessLicenseLost,1);
      if(form!=null&&form.IsHandleCreated&&!closing)form.BeginInvoke((Action)(()=>{
        licenseInfo.Text=licensed?ExpiryText(result)+" · "+LicenseMessage(result):"未通过授权验证";
        licenseInfo.ForeColor=licensed?Color.FromArgb(37,127,178):Color.FromArgb(185,94,63);
        EnableInstalledChoices();
        status.Text=licensed?"授权有效 · 选择任意工具开始":LicenseMessage(result);
      }));
      if(licensed&&licenseTimer==null){licenseTimer=new System.Threading.Timer(_=>QueueLicenseCheck(false),null,60000,60000);if(!networkSubscribed){NetworkChange.NetworkAvailabilityChanged+=NetworkRestored;NetworkChange.NetworkAddressChanged+=NetworkAddressChanged;networkSubscribed=true;}}
    }
    if(lost){ThreadPool.QueueUserWorkItem(_=>StopTools());}
  }
  static void NetworkRestored(object sender,NetworkAvailabilityEventArgs e){if(e.IsAvailable)QueueLicenseCheck(false);}
  static void NetworkAddressChanged(object sender,EventArgs e){QueueLicenseCheck(false);}
  static void QueueLicenseCheck(bool initial){
    if(closing||Interlocked.CompareExchange(ref licenseChecking,1,0)!=0)return;
    ThreadPool.QueueUserWorkItem(_=>{try{Dictionary<string,object> result;try{result=LicenseRequest("check");}catch(Exception error){result=new Dictionary<string,object>{{"ok",false},{"message",error.Message}};}if(closing)return;ApplyLicense(result);if(initial&&!LicenseOK(result)&&form!=null&&form.IsHandleCreated)form.BeginInvoke((Action)(()=>ShowActivation(LicenseMessage(result))));}finally{Interlocked.Exchange(ref licenseChecking,0);}});
  }
  static bool AuthorizeHeadless(){try{var result=LicenseRequest("check");ApplyLicense(result);if(!licensed)Console.Error.WriteLine(LicenseMessage(result));return licensed;}catch(Exception error){Console.Error.WriteLine(error.Message);return false;}}
  static void ShowActivation(string message){
    if(closing)return;if(licenseDialog!=null&&!licenseDialog.IsDisposed){licenseDialog.Activate();return;}
    using(var dialog=new Form{Text="羽轩编程工作台 · 软件激活",Icon=form.Icon,ClientSize=new Size(560,350),MinimumSize=new Size(570,389),MaximumSize=new Size(570,389),StartPosition=FormStartPosition.CenterParent,BackColor=Color.FromArgb(244,250,254),ShowInTaskbar=false,MaximizeBox=false,MinimizeBox=false}){
      licenseDialog=dialog;
      var layout=new TableLayoutPanel{Dock=DockStyle.Fill,ColumnCount=1,RowCount=6,Padding=new Padding(28)};layout.ColumnStyles.Add(new ColumnStyle(SizeType.Percent,100));layout.RowStyles.Add(new RowStyle(SizeType.Absolute,96));layout.RowStyles.Add(new RowStyle(SizeType.Absolute,28));layout.RowStyles.Add(new RowStyle(SizeType.Absolute,40));layout.RowStyles.Add(new RowStyle(SizeType.Percent,100));layout.RowStyles.Add(new RowStyle(SizeType.Absolute,44));layout.RowStyles.Add(new RowStyle(SizeType.Absolute,20));dialog.Controls.Add(layout);
      var heading=new Panel{Dock=DockStyle.Fill};heading.Controls.Add(new PictureBox{Width=64,Height=64,Location=new Point(0,4),SizeMode=PictureBoxSizeMode.Zoom,Image=Image.FromFile(Path.Combine(root,"resources/brand-logo.png"))});heading.Controls.Add(new Label{AutoSize=true,Text=licensed?"管理软件授权":"激活你的编程工作台",Location=new Point(80,6),Font=new Font("Microsoft YaHei UI",17,FontStyle.Bold),ForeColor=Color.FromArgb(25,81,118)});heading.Controls.Add(new Label{AutoSize=false,Width=410,Height=48,Text="首次使用需联网激活。激活后可离线使用，\r\n联网时会检查授权，有效期内畅享全部工具。",Location=new Point(82,41),Font=new Font("Microsoft YaHei UI",9),ForeColor=Color.FromArgb(94,128,151)});layout.Controls.Add(heading,0,0);
      layout.Controls.Add(new Label{AutoSize=true,Text="请输入激活码",Font=new Font("Microsoft YaHei UI",9),ForeColor=Color.FromArgb(53,91,118)},0,1);
      var input=new TextBox{Dock=DockStyle.Fill,Font=new Font("Consolas",13),CharacterCasing=CharacterCasing.Upper,MaxLength=60,Margin=new Padding(0,0,0,8)};layout.Controls.Add(input,0,2);
      var hint=new Label{Dock=DockStyle.Fill,Text=message??(licensed?licenseInfo.Text:"联网激活后，授权凭证会安全保存在此电脑。"),Font=new Font("Microsoft YaHei UI",9),ForeColor=Color.FromArgb(82,119,144),Padding=new Padding(0,8,0,4)};layout.Controls.Add(hint,0,3);
      var actions=new TableLayoutPanel{Dock=DockStyle.Fill,ColumnCount=2,RowCount=1};actions.ColumnStyles.Add(new ColumnStyle(SizeType.Percent,40));actions.ColumnStyles.Add(new ColumnStyle(SizeType.Percent,60));
      var retry=new Button{Dock=DockStyle.Fill,Text="重新验证",FlatStyle=FlatStyle.Flat,BackColor=Color.White,ForeColor=Color.FromArgb(31,120,174),Font=new Font("Microsoft YaHei UI",9),Margin=new Padding(0,0,12,0)};retry.FlatAppearance.BorderColor=Color.FromArgb(193,220,239);
      var activate=new Button{Dock=DockStyle.Fill,Text="激活并进入",FlatStyle=FlatStyle.Flat,BackColor=Color.FromArgb(22,136,208),ForeColor=Color.White,Font=new Font("Microsoft YaHei UI",10,FontStyle.Bold),Margin=new Padding(0)};activate.FlatAppearance.BorderSize=0;actions.Controls.Add(retry,0,0);actions.Controls.Add(activate,1,0);layout.Controls.Add(actions,0,4);
      bool busy=false;
      Action<string> submit=action=>{if(busy)return;if(action=="activate"&&String.IsNullOrWhiteSpace(input.Text)){hint.Text="请输入激活码。";input.Focus();return;}busy=true;activate.Enabled=false;retry.Enabled=false;input.Enabled=false;hint.Text="正在验证授权，请稍候……";string code=input.Text;ThreadPool.QueueUserWorkItem(_=>{Dictionary<string,object> result;try{result=LicenseRequest(action,action=="activate"?code:null);}catch(Exception error){result=new Dictionary<string,object>{{"ok",false},{"message",error.Message}};}if(closing)return;if(action=="check"||LicenseOK(result)||!licensed)ApplyLicense(result);if(dialog.IsHandleCreated)dialog.BeginInvoke((Action)(()=>{busy=false;activate.Enabled=true;retry.Enabled=true;input.Enabled=true;if(LicenseOK(result)){input.Clear();dialog.DialogResult=DialogResult.OK;dialog.Close();}else{hint.Text=LicenseMessage(result);hint.ForeColor=Color.FromArgb(187,90,57);}}));});};
      activate.Click+=(s,e)=>submit("activate");retry.Click+=(s,e)=>submit("check");dialog.AcceptButton=activate;dialog.FormClosing+=(s,e)=>{if(busy)e.Cancel=true;};dialog.Shown+=(s,e)=>input.Focus();dialog.ShowDialog(form);licenseDialog=null;
    }
  }
  static void StopLicense(){
    lock(licenseGate){
    if(licenseTimer!=null){licenseTimer.Dispose();licenseTimer=null;}
    if(networkSubscribed){NetworkChange.NetworkAvailabilityChanged-=NetworkRestored;NetworkChange.NetworkAddressChanged-=NetworkAddressChanged;networkSubscribed=false;}
    if(licenseBridge!=null){try{if(!licenseBridge.HasExited){licenseBridge.StandardInput.WriteLine("{\"action\":\"exit\"}");licenseBridge.StandardInput.Flush();if(!licenseBridge.WaitForExit(5000))licenseBridge.Kill();}}catch{}licenseBridge.Dispose();licenseBridge=null;}
    }
  }
}
