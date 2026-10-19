using System;
using System.IO;
using System.Net;
using System.Linq;
using System.Text;
using System.Drawing;
using System.Windows.Forms;
using System.Threading;
using System.Diagnostics;
using System.Security.Cryptography;
using System.Collections.Generic;
using System.Web.Script.Serialization;

[assembly:System.Reflection.AssemblyVersion("2.4.5.0")]
[assembly:System.Reflection.AssemblyFileVersion("2.4.5.0")]

internal static partial class Suite {
  internal const string ProductVersion="2.4.5";
  internal const string ReleasesPage="https://github.com/xiaoyuxuanran/Yuxuan_Programming_Studio/releases";
  internal const string GiteeReleasesPage="https://gitee.com/studentcodeone/yuxuan_-programming_-studio/releases";
  static string pendingInstaller;
  internal sealed class ReleaseUpdate {public string Version,Notes,Download,SHA256;public string[] Downloads;public long Bytes;public bool Incremental;}
  static bool TrustedUpdateUrl(string url) {
    return url!=null&&(url.StartsWith(GiteeReleasesPage+"/download/",StringComparison.Ordinal)||url.StartsWith(ReleasesPage+"/download/",StringComparison.Ordinal));
  }
  internal static ReleaseUpdate ReadRelease(string json) {
    var release=(Dictionary<string,object>)new JavaScriptSerializer{MaxJsonLength=1048576}.DeserializeObject(json);
    Version next,current;
    if(!Version.TryParse(Convert.ToString(release["tag_name"]).TrimStart('v'),out next)||!Version.TryParse(ProductVersion,out current))throw new Exception("无法识别发布版本。");
    if(next<=current||Convert.ToBoolean(release["draft"])||Convert.ToBoolean(release["prerelease"]))return null;
    var assets=((object[])release["assets"]).Cast<Dictionary<string,object>>();
    string patch="Yuxuan-Programming-Studio-Update-"+ProductVersion+"-to-"+next+".exe";
    var asset=assets.FirstOrDefault(a=>Convert.ToString(a["name"])==patch)??assets.FirstOrDefault(a=>Convert.ToString(a["name"])=="AppInventor-Offline-Setup-x64.exe");
    if(asset==null)throw new Exception("新版本尚未提供适用的 Windows 安装包。");
    string url=Convert.ToString(asset["browser_download_url"]),digest=Convert.ToString(asset.ContainsKey("digest")?asset["digest"]:null);
    if(!TrustedUpdateUrl(url)||!digest.StartsWith("sha256:")||!System.Text.RegularExpressions.Regex.IsMatch(digest.Substring(7),"\\A[0-9a-fA-F]{64}\\z"))throw new Exception("发布附件缺少可信的 SHA256 信息。");
    var downloads=new List<string>{url};object mirrors;
    if(asset.TryGetValue("mirrors",out mirrors))foreach(var mirror in (object[])mirrors){string candidate=Convert.ToString(mirror);if(!TrustedUpdateUrl(candidate))throw new Exception("发布附件包含不可信的镜像地址。");if(!downloads.Contains(candidate))downloads.Add(candidate);}
    downloads=downloads.OrderBy(candidate=>candidate.StartsWith(GiteeReleasesPage+"/",StringComparison.Ordinal)?0:1).ToList();
    long bytes=Convert.ToInt64(asset["size"]);if(bytes<=0||bytes>3L*1024*1024*1024)throw new Exception("安装包大小无效。");
    return new ReleaseUpdate{Version=next.ToString(),Notes=Convert.ToString(release["body"]),Download=downloads[0],Downloads=downloads.ToArray(),SHA256=digest.Substring(7),Bytes=bytes,Incremental=Convert.ToString(asset["name"])==patch};
  }
  static HttpWebRequest UpdateRequest(string url) {
    ServicePointManager.SecurityProtocol|=SecurityProtocolType.Tls12;
    var request=(HttpWebRequest)WebRequest.Create(url);request.UserAgent="Yuxuan-Programming-Studio/"+ProductVersion;request.Timeout=20000;request.ReadWriteTimeout=45000;request.AutomaticDecompression=DecompressionMethods.GZip|DecompressionMethods.Deflate;return request;
  }
  static string ReadUpdateText(string url) {
    using(var response=UpdateRequest(url).GetResponse())
    using(var stream=response.GetResponseStream())using(var buffer=new MemoryStream()) {
      byte[] chunk=new byte[16384];int count;while((count=stream.Read(chunk,0,chunk.Length))>0){if(buffer.Length+count>1048576)throw new Exception("发布信息过大。");buffer.Write(chunk,0,count);}return Encoding.UTF8.GetString(buffer.ToArray());
    }
  }
  static string UpdateMetadata() {
    // Validate each source before accepting it, so an HTML error page also falls back.
    Exception last=null;
    foreach(string url in new[]{GiteeReleasesPage.Replace("/releases","/raw/main/update.json"),ReleasesPage+"/latest/download/update.json","https://api.github.com/repos/xiaoyuxuanran/Yuxuan_Programming_Studio/releases/latest"}){
      try{string json=ReadUpdateText(url);ReadRelease(json);return json;}catch(Exception error){last=error;}
    }
    throw new Exception("Gitee 和 GitHub 均暂时不可用。",last);
  }
  internal static void VerifyUpdate(string path,ReleaseUpdate update) {
    if(new FileInfo(path).Length!=update.Bytes)throw new Exception("安装包长度不匹配。");
    string hash;using(var stream=File.OpenRead(path))using(var sha=SHA256.Create())hash=BitConverter.ToString(sha.ComputeHash(stream)).Replace("-","");
    if(!hash.Equals(update.SHA256,StringComparison.OrdinalIgnoreCase))throw new Exception("安装包 SHA256 校验失败，已禁止运行。");
  }
  internal static void DownloadUpdate(string path,ReleaseUpdate update,Func<bool> cancelled,Action<string> report) {
    bool downloaded=false;Exception downloadError=null;
    foreach(string download in update.Downloads){
    try{
    if(cancelled())throw new OperationCanceledException();
    using(var response=UpdateRequest(download).GetResponse())using(var input=response.GetResponseStream())using(var output=new FileStream(path,FileMode.Create,FileAccess.Write,FileShare.None)){
      byte[] chunk=new byte[65536];int count;long received=0;var watch=Stopwatch.StartNew();while((count=input.Read(chunk,0,chunk.Length))>0){if(cancelled())throw new OperationCanceledException();received+=count;if(received>update.Bytes)throw new Exception("下载长度超过发布信息。");output.Write(chunk,0,count);if(watch.ElapsedMilliseconds>300){string progress="正在下载 "+(received*100.0/update.Bytes).ToString("F0")+"% · "+(received/1048576.0).ToString("F1")+" MB";report(progress);watch.Restart();}}
    }
    if(cancelled())throw new OperationCanceledException();report("正在校验 SHA256……");VerifyUpdate(path,update);downloaded=true;break;
    }catch(OperationCanceledException){throw;}catch(Exception error){downloadError=error;report("当前来源不可用，正在尝试备用下载来源……");}
    }
    if(!downloaded)throw new Exception("所有下载来源均失败。",downloadError);
  }
  sealed class UpdateCancellation {public volatile bool Value;}
  static void ShowUpdates(bool check) {
    var dialog=new Form{Text="更新日志与检查更新 · 当前 "+ProductVersion,ClientSize=new Size(700,530),MinimumSize=new Size(520,400),StartPosition=FormStartPosition.CenterParent,BackColor=Color.FromArgb(241,248,253),Font=new Font("Microsoft YaHei UI",9),AutoScaleMode=AutoScaleMode.Dpi};
    var layout=new TableLayoutPanel{Dock=DockStyle.Fill,Padding=new Padding(18),ColumnCount=1,RowCount=3};layout.RowStyles.Add(new RowStyle(SizeType.AutoSize));layout.RowStyles.Add(new RowStyle(SizeType.Percent,100));layout.RowStyles.Add(new RowStyle(SizeType.AutoSize));dialog.Controls.Add(layout);
    var state=new Label{AutoSize=true,Text="当前版本 "+ProductVersion,Margin=new Padding(0,0,0,12),ForeColor=Color.FromArgb(24,69,103)};layout.Controls.Add(state,0,0);
    layout.SizeChanged+=(s,e)=>state.MaximumSize=new Size(Math.Max(1,layout.ClientSize.Width-layout.Padding.Horizontal),0);
    var notes=new TextBox{Multiline=true,ReadOnly=true,ScrollBars=ScrollBars.Vertical,Dock=DockStyle.Fill,BackColor=Color.White};layout.Controls.Add(notes,0,1);
    try{notes.Text=File.ReadAllText(Path.Combine(root,"resources/CHANGELOG.txt"),Encoding.UTF8).Replace("\n","\r\n").Replace("\r\r\n","\r\n");}catch{notes.Text="当前版本 "+ProductVersion;}
    var buttons=new FlowLayoutPanel{Dock=DockStyle.Fill,AutoSize=true,WrapContents=true,Margin=new Padding(0,12,0,0)};layout.Controls.Add(buttons,0,2);
    var refresh=new Button{Text="检查更新",AutoSize=true,Height=36};var install=new Button{Text="下载并更新",AutoSize=true,Height=36,Enabled=false};var browse=new Button{Text="历史版本 / 下载页面",AutoSize=true,Height=36};buttons.Controls.Add(refresh);buttons.Controls.Add(install);buttons.Controls.Add(browse);
    browse.Click+=(s,e)=>Process.Start(new ProcessStartInfo(GiteeReleasesPage){UseShellExecute=true});
    ReleaseUpdate available=null;bool busy=false;var cancelled=new UpdateCancellation();
    Action<Action> ui=action=>{if(!dialog.IsDisposed&&dialog.IsHandleCreated)try{dialog.BeginInvoke(action);}catch(InvalidOperationException){}};
    Action beginCheck=()=>{if(busy)return;busy=true;refresh.Enabled=false;install.Enabled=false;state.Text="正在检查更新（优先 Gitee）……";
      ThreadPool.QueueUserWorkItem(_=>{try{var found=ReadRelease(UpdateMetadata());ui(()=>{available=found;state.Text=found==null?"当前已是最新正式版本 "+ProductVersion:"发现 "+found.Version+" · "+(found.Incremental?"增量升级":"完整安装包")+" · "+(found.Bytes/1048576.0).ToString("F1")+" MB";if(found!=null)notes.Text=found.Notes.Replace("\n","\r\n");install.Enabled=found!=null;});}
      catch(Exception ex){ui(()=>state.Text="检查失败："+ex.Message+" 可打开发布页面手动下载。");}finally{busy=false;ui(()=>refresh.Enabled=true);}});
    };
    refresh.Click+=(s,e)=>beginCheck();
    install.Click+=(s,e)=>{if(busy||available==null)return;busy=true;cancelled.Value=false;refresh.Enabled=false;install.Enabled=false;var update=available;
      ThreadPool.QueueUserWorkItem(_=>{string partial=null;try{
        string folder=Path.Combine(data,"updates");Directory.CreateDirectory(folder);string target=Path.Combine(folder,"Yuxuan-"+update.Version+"-"+update.SHA256.Substring(0,12)+".exe");partial=target+"."+Guid.NewGuid().ToString("N")+".partial";
        DownloadUpdate(partial,update,()=>cancelled.Value,message=>ui(()=>state.Text=message));
        if(File.Exists(target))File.Delete(target);File.Move(partial,target);partial=null;
        ui(()=>{busy=false;state.Text="校验通过，已下载 "+update.Version;refresh.Enabled=true;install.Enabled=true;if(MessageBox.Show(dialog,"安装包已通过 SHA256 校验。现在保存并退出工作台，开始升级吗？\r\n项目和激活数据将保留。","准备安装 "+update.Version,MessageBoxButtons.YesNo,MessageBoxIcon.Information)==DialogResult.Yes){pendingInstaller=target;dialog.Close();form.Close();}});
      }catch(OperationCanceledException){}catch(Exception ex){ui(()=>{state.Text="更新失败："+ex.Message;refresh.Enabled=true;install.Enabled=true;});}finally{busy=false;if(partial!=null)try{File.Delete(partial);}catch{}}});
    };
    dialog.FormClosing+=(s,e)=>cancelled.Value=true;if(check)dialog.Shown+=(s,e)=>beginCheck();dialog.ShowDialog(form);dialog.Dispose();
  }
}
