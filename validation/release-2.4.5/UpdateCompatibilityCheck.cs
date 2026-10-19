using System;using System.IO;using System.Reflection;
internal static class UpdateCompatibilityCheck {
 static int Main(string[] a){try{
  string json=File.ReadAllText(a[0]);var flags=BindingFlags.Static|BindingFlags.NonPublic;
  for(int i=3;i<a.Length;i++){
   var suite=Assembly.LoadFile(Path.GetFullPath(a[i])).GetType("Suite");string version=(string)suite.GetField("ProductVersion",flags).GetRawConstantValue();
   var update=suite.GetMethod("ReadRelease",flags).Invoke(null,new object[]{json});if(update==null)throw new Exception("Missing full upgrade for "+version);
   var type=update.GetType();string url=(string)type.GetField("Download").GetValue(update);
   if(!url.EndsWith("/AppInventor-Offline-Setup-x64.exe")||(bool)type.GetField("Incremental").GetValue(update))throw new Exception("Incorrect full installer for "+version);
  }
  var current=Assembly.LoadFile(Path.GetFullPath(a[2])).GetType("Suite");if(current.GetMethod("ReadRelease",flags).Invoke(null,new object[]{json})!=null)throw new Exception("Current version offered itself");
  File.WriteAllText(a[1],"{\"ok\":true,\"oldClientsSelectFullInstaller\":true,\"currentVersionRejected\":true,\"oldClientCount\":"+(a.Length-3)+"}");return 0;
 }catch(Exception e){Console.Error.WriteLine(e.InnerException??e);return 1;}}
}
