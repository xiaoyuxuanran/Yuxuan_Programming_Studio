using System;using System.IO;using System.Reflection;using System.Diagnostics;
internal static class SuiteIntegrationCheck {
  [STAThread]static int Main(string[] args){var type=typeof(Suite);var flags=BindingFlags.NonPublic|BindingFlags.Static;Process child=null;
    try{
      Directory.CreateDirectory(args[0]);type.GetField("data",flags).SetValue(null,Path.GetFullPath(args[0]));
      type.GetMethod("StartMixly",flags).Invoke(null,null);child=(Process)type.GetField("mixly",flags).GetValue(null);
      if(child==null||child.HasExited||Path.GetFileName(child.MainModule.FileName)!="Mixly.exe")throw new Exception("Launcher did not start the desktop client");
      int pid=child.Id;type.GetMethod("StartMixly",flags).Invoke(null,null);if(((Process)type.GetField("mixly",flags).GetValue(null)).Id!=pid)throw new Exception("Second launch created a duplicate client");
      type.GetMethod("StopTools",flags).Invoke(null,null);if(!child.WaitForExit(5000))throw new Exception("Desktop client did not stop cleanly");
      File.WriteAllText(args[1],"{\"ok\":true,\"desktopStarted\":true,\"sameProcessFocused\":true,\"gracefulStop\":true}");return 0;
    }catch(Exception error){File.WriteAllText(args[1],(error.InnerException??error).ToString());return 1;}
    finally{if(child!=null&&!child.HasExited)try{type.GetMethod("StopTools",flags).Invoke(null,null);}catch{} }
  }
}
