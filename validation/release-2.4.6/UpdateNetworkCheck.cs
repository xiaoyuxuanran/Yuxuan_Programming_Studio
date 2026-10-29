using System;using System.IO;using System.Reflection;using System.Collections.Generic;using System.Web.Script.Serialization;
internal static class UpdateNetworkCheck {
  static int Main(string[] args){try{if(args.Length<3)throw new Exception("Provide current client, report path, and 2.4.5 client.");
    var assembly=Assembly.LoadFile(Path.GetFullPath(args[0]));var suite=assembly.GetType("Suite");var flags=BindingFlags.NonPublic|BindingFlags.Static;
    var parse=suite.GetMethod("ReadRelease",flags);var fetch=suite.GetMethod("ReadUpdateText",flags);var download=suite.GetMethod("DownloadUpdate",flags);
    string gitee=(string)suite.GetField("GiteeReleasesPage",flags).GetRawConstantValue();
    string json=(string)suite.GetMethod("UpdateMetadata",flags).Invoke(null,null);
    string primary=(string)fetch.Invoke(null,new object[]{gitee.Replace("/releases","/raw/main/update.json")});
    if(json!=primary)throw new Exception("Gitee metadata was not preferred");
    if(parse.Invoke(null,new object[]{json})!=null)throw new Exception("Current release offered as an upgrade");
    var js=new JavaScriptSerializer();var release=(Dictionary<string,object>)js.DeserializeObject(json);
    Dictionary<string,object> asset=null;foreach(object item in (object[])release["assets"]){var candidate=(Dictionary<string,object>)item;if(Convert.ToString(candidate["name"])=="User-Guide.txt")asset=candidate;}
    if(asset==null)throw new Exception("Missing published small download fixture");
    // Exercise the production downloader with a small published fixture, not an installer execution.
    release["tag_name"]="v2.4.7";asset["name"]="Yuxuan-Programming-Studio-Update-2.4.6-to-2.4.7.exe";release["assets"]=new object[]{asset};
    string file=Path.Combine(Path.GetDirectoryName(Path.GetFullPath(args[1])),"download-check.partial");
    var update=parse.Invoke(null,new object[]{js.Serialize(release)});var type=update.GetType();
    string preferred=(string)type.GetField("Download").GetValue(update);if(!preferred.StartsWith(gitee+"/"))throw new Exception("Download did not prefer Gitee");
    download.Invoke(null,new object[]{file,update,(Func<bool>)(()=>false),(Action<string>)(_=>{})});File.Delete(file);
    string github=(string)asset["browser_download_url"];
    asset["mirrors"]=new object[]{gitee+"/download/v2.4.6/intentionally-missing-fallback-test.exe"};
    if(!github.StartsWith("https://github.com/"))throw new Exception("Expected canonical GitHub URL");
    update=parse.Invoke(null,new object[]{js.Serialize(release)});bool fellBack=false;
    download.Invoke(null,new object[]{file,update,(Func<bool>)(()=>false),(Action<string>)(message=>{if(message.Contains("备用"))fellBack=true;})});File.Delete(file);
    if(!fellBack)throw new Exception("Unavailable source did not trigger fallback");
    bool cancelled=false;try{download.Invoke(null,new object[]{file,update,(Func<bool>)(()=>true),(Action<string>)(_=>{})});}catch(TargetInvocationException ex){cancelled=ex.InnerException is OperationCanceledException;}
    if(!cancelled)throw new Exception("Download cancellation ignored");
    if(args.Length>2){
      var old=Assembly.LoadFile(Path.GetFullPath(args[2])).GetType("Suite");
      var oldUpdate=old.GetMethod("ReadRelease",flags).Invoke(null,new object[]{json});
      if(oldUpdate==null||!(bool)oldUpdate.GetType().GetField("Incremental").GetValue(oldUpdate))throw new Exception("Old 2.4.5 client missed actual delta");
      old.GetMethod("DownloadUpdate",flags).Invoke(null,new object[]{file,oldUpdate,(Func<bool>)(()=>false),(Action<string>)(_=>{})});File.Delete(file);
    }
    File.WriteAllText(args[1],"{\"ok\":true,\"giteeMetadataPreferred\":true,\"publishedGuideFixtureDownloadVerified\":true,\"githubFallbackVerified\":true,\"cancelVerified\":true,\"old245ActualDeltaDownloadVerified\":true,\"installerExecuted\":false}");
    Console.WriteLine("PASS live Gitee metadata/download, SHA256, GitHub fallback and cancellation");return 0;
  }catch(Exception ex){Console.Error.WriteLine(ex.InnerException??ex);return 1;}}
}
