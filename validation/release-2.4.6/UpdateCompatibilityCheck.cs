using System;using System.IO;using System.Reflection;
class UpdateCompatibilityCheck {
 static int Main(string[] a){try{
  var json=File.ReadAllText(a[0]);var flags=BindingFlags.Static|BindingFlags.NonPublic|BindingFlags.Public;int deltas=0,full=0;
  for(int i=2;i<a.Length;i++){
   var suite=Assembly.LoadFile(Path.GetFullPath(a[i])).GetType("Suite");var version=(string)suite.GetField("ProductVersion",flags).GetRawConstantValue();
   var update=suite.GetMethod("ReadRelease",flags).Invoke(null,new object[]{json});
   if(version=="2.4.6"){if(update!=null)throw new Exception("Current version offered itself");continue;}
   if(update==null)throw new Exception("No update offered: "+version);var type=update.GetType();bool delta=(bool)type.GetField("Incremental").GetValue(update);
   if(delta!=(version=="2.4.5"))throw new Exception("Wrong update kind: "+version);
   string url=(string)type.GetField("Download").GetValue(update);if(!url.EndsWith(delta?"/Yuxuan-Programming-Studio-Update-2.4.5-to-2.4.6.exe":"/AppInventor-Offline-Setup-x64.exe"))throw new Exception("Wrong filename: "+version);
   if(delta)deltas++;else full++;
  }
  if(deltas<2||full<2)throw new Exception("Insufficient starting versions");
  File.WriteAllText(a[1],"{\"ok\":true,\"currentRejected\":true,\"delta245Clients\":"+deltas+",\"olderFullClients\":"+full+"}");Console.WriteLine("PASS version-specific delta/full update selection");return 0;
 }catch(Exception e){Console.Error.WriteLine(e.InnerException??e);return 1;}}
}
