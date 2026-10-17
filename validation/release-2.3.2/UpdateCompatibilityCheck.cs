using System;using System.IO;using System.Reflection;
internal static class UpdateCompatibilityCheck {
 static int Main(string[] a){try{
  string json=File.ReadAllText(a[2]);var flags=BindingFlags.Static|BindingFlags.NonPublic;
  var old=Assembly.LoadFile(Path.GetFullPath(a[0])).GetType("Suite");
  var update=old.GetMethod("ReadRelease",flags).Invoke(null,new object[]{json});
  if(update==null)throw new Exception("2.3.1 did not offer 2.3.2");
  var type=update.GetType();string url=(string)type.GetField("Download").GetValue(update);
  if(!url.EndsWith("/Yuxuan-Programming-Studio-Update-2.3.1-to-2.3.2.exe")||!url.StartsWith("https://gitee.com/"))throw new Exception("Old updater selected the wrong patch/source");
  if(!(bool)type.GetField("Incremental").GetValue(update))throw new Exception("Old updater did not select an incremental update");
  var current=Assembly.LoadFile(Path.GetFullPath(a[1])).GetType("Suite");
  if(current.GetMethod("ReadRelease",flags).Invoke(null,new object[]{json})!=null)throw new Exception("Current version offered itself");
  File.WriteAllText(a[3],"{\"ok\":true,\"actual231ClientSelectsMatchingPatch\":true,\"giteePreferred\":true,\"currentVersionRejected\":true}");return 0;
 }catch(Exception e){Console.Error.WriteLine(e.InnerException??e);return 1;}}
}
