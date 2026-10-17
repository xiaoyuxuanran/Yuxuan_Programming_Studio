using System;using System.IO;using System.Reflection;
internal static class UpdateCompatibilityCheck {
 static int Main(string[] a){try{
  string json=File.ReadAllText(a[3]);var flags=BindingFlags.Static|BindingFlags.NonPublic;
  for(int i=0;i<2;i++){
   var suite=Assembly.LoadFile(Path.GetFullPath(a[i])).GetType("Suite");string version=(string)suite.GetField("ProductVersion",flags).GetRawConstantValue();
   var update=suite.GetMethod("ReadRelease",flags).Invoke(null,new object[]{json});if(update==null)throw new Exception("Old client did not offer update "+version);
   var type=update.GetType();string url=(string)type.GetField("Download").GetValue(update);
   if(!url.EndsWith("/Yuxuan-Programming-Studio-Update-"+version+"-to-2.3.3.exe")||!url.StartsWith("https://gitee.com/"))throw new Exception("Incorrect patch for "+version);
   if(!(bool)type.GetField("Incremental").GetValue(update))throw new Exception("Not incremental");
  }
  var current=Assembly.LoadFile(Path.GetFullPath(a[2])).GetType("Suite");if(current.GetMethod("ReadRelease",flags).Invoke(null,new object[]{json})!=null)throw new Exception("Same version offered itself");
  File.WriteAllText(a[4],"{\"ok\":true,\"actual231And232ClientsSelectMatchingPatch\":true,\"giteePreferred\":true,\"currentVersionRejected\":true}");return 0;
 }catch(Exception e){Console.Error.WriteLine(e.InnerException??e);return 1;}}
}
