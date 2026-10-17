using System;
using System.IO;
using System.Collections.Generic;
using System.Reflection;
using System.Web.Script.Serialization;
internal static class UpdateCheck {
  [STAThread] static int Main(string[] args) {
    try {
      var js=new JavaScriptSerializer();var release=new Dictionary<string,object>{{"tag_name","v2.3.3"},{"draft",false},{"prerelease",false},{"body","Future release fixture"}};
      var patch=new Dictionary<string,object>{{"name","Yuxuan-Programming-Studio-Update-2.3.2-to-2.3.3.exe"},{"size",3},{"digest","sha256:ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"},{"browser_download_url",Suite.ReleasesPage+"/download/v2.3.3/patch.exe"}};
      var full=new Dictionary<string,object>(patch);full["name"]="AppInventor-Offline-Setup-x64.exe";full["size"]=99;
      release["assets"]=new object[]{full,patch};var parsed=Suite.ReadRelease(js.Serialize(release));if(!parsed.Incremental||parsed.Bytes!=3)throw new Exception("Patch selection failed");
      patch["mirrors"]=new object[]{Suite.GiteeReleasesPage+"/download/v2.3.3/patch.exe"};parsed=Suite.ReadRelease(js.Serialize(release));if(parsed.Downloads.Length!=2||!parsed.Download.StartsWith(Suite.GiteeReleasesPage+"/"))throw new Exception("Gitee mirror not preferred");
      patch["mirrors"]=new object[]{"https://example.com/evil.exe"};bool mirrorDenied=false;try{Suite.ReadRelease(js.Serialize(release));}catch{mirrorDenied=true;}if(!mirrorDenied)throw new Exception("Foreign mirror accepted");patch.Remove("mirrors");
      string p=Path.Combine(args[0],"hash-fixture.bin");Directory.CreateDirectory(args[0]);File.WriteAllText(p,"abc");Suite.VerifyUpdate(p,parsed);File.WriteAllText(p,"abd");bool denied=false;try{Suite.VerifyUpdate(p,parsed);}catch{denied=true;}if(!denied)throw new Exception("Tampered file accepted");File.Delete(p);
      patch["browser_download_url"]="https://example.com/evil.exe";denied=false;try{Suite.ReadRelease(js.Serialize(release));}catch{denied=true;}if(!denied)throw new Exception("Foreign asset accepted");patch["browser_download_url"]=Suite.ReleasesPage+"/download/v2.3.3/patch.exe";
      release["tag_name"]="v2.3.2";if(Suite.ReadRelease(js.Serialize(release))!=null)throw new Exception("Same version offered");release["tag_name"]="v2.3.0";if(Suite.ReadRelease(js.Serialize(release))!=null)throw new Exception("Downgrade offered");release["tag_name"]="v2.3.3";release["prerelease"]=true;if(Suite.ReadRelease(js.Serialize(release))!=null)throw new Exception("Preview offered");
      File.WriteAllText(Path.Combine(args[0],"updater.json"),"{\"ok\":true,\"patchPreferred\":true,\"giteePreferred\":true,\"foreignMirrorRejected\":true,\"tamperingRejected\":true,\"foreignDownloadRejected\":true,\"downgradeRejected\":true,\"prereleaseRejected\":true}");
      typeof(LayoutCheck).GetMethod("Main",BindingFlags.Static|BindingFlags.NonPublic).Invoke(null,new object[]{args});return 0;
    }catch(Exception error){Console.Error.WriteLine(error);return 1;}
  }
}
