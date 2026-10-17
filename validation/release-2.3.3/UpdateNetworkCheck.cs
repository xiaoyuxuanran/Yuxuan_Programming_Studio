using System;using System.IO;using System.Reflection;using System.Collections.Generic;using System.Web.Script.Serialization;
internal static class UpdateNetworkCheck {
  static int Main(string[] args){try{
    var assembly=Assembly.LoadFile(Path.GetFullPath(args[0]));var suite=assembly.GetType("Suite");var flags=BindingFlags.NonPublic|BindingFlags.Static;
    var parse=suite.GetMethod("ReadRelease",flags);var fetch=suite.GetMethod("ReadUpdateText",flags);var download=suite.GetMethod("DownloadUpdate",flags);
    string gitee=(string)suite.GetField("GiteeReleasesPage",flags).GetRawConstantValue();
    string json=(string)suite.GetMethod("UpdateMetadata",flags).Invoke(null,null);
    string primary=(string)fetch.Invoke(null,new object[]{gitee.Replace("/releases","/raw/main/update.json")});
    if(json!=primary)throw new Exception("Gitee metadata was not preferred");
    if(parse.Invoke(null,new object[]{json})!=null)throw new Exception("Current release offered as an upgrade");
    var js=new JavaScriptSerializer();var release=(Dictionary<string,object>)js.DeserializeObject(json);
    var asset=(Dictionary<string,object>)((object[])release["assets"])[0];
    // Exercise the published bytes as a future fixture; never execute the installer.
    release["tag_name"]="v2.3.4";asset["name"]="Yuxuan-Programming-Studio-Update-2.3.3-to-2.3.4.exe";release["assets"]=new object[]{asset};
    string file=Path.Combine(Path.GetDirectoryName(Path.GetFullPath(args[1])),"download-check.partial");
    var update=parse.Invoke(null,new object[]{js.Serialize(release)});var type=update.GetType();
    string preferred=(string)type.GetField("Download").GetValue(update);if(!preferred.StartsWith(gitee+"/"))throw new Exception("Download did not prefer Gitee");
    download.Invoke(null,new object[]{file,update,(Func<bool>)(()=>false),(Action<string>)(_=>{})});File.Delete(file);
    string github=(string)asset["browser_download_url"];
    asset["mirrors"]=new object[]{gitee+"/download/v2.3.3/intentionally-missing-fallback-test.exe"};
    if(!github.StartsWith("https://github.com/"))throw new Exception("Expected canonical GitHub URL");
    update=parse.Invoke(null,new object[]{js.Serialize(release)});bool fellBack=false;
    download.Invoke(null,new object[]{file,update,(Func<bool>)(()=>false),(Action<string>)(message=>{if(message.Contains("备用"))fellBack=true;})});File.Delete(file);
    if(!fellBack)throw new Exception("Unavailable source did not trigger fallback");
    bool cancelled=false;try{download.Invoke(null,new object[]{file,update,(Func<bool>)(()=>true),(Action<string>)(_=>{})});}catch(TargetInvocationException ex){cancelled=ex.InnerException is OperationCanceledException;}
    if(!cancelled)throw new Exception("Download cancellation ignored");
    File.WriteAllText(args[1],"{\"ok\":true,\"giteeMetadataPreferred\":true,\"giteeDownloadVerified\":true,\"githubFallbackVerified\":true,\"cancelVerified\":true,\"installerExecuted\":false}");
    Console.WriteLine("PASS live Gitee metadata/download, SHA256, GitHub fallback and cancellation");return 0;
  }catch(Exception ex){Console.Error.WriteLine(ex.InnerException??ex);return 1;}}
}
