using System;
using System.IO;
using System.Linq;
using System.Threading;
using System.Diagnostics;

// Isolation fixture: only a graceful-save handshake; no App Inventor, projects or sockets.
internal static class FakeCore {
  static int Main(string[] args) {
    string data=null;for(int i=0;i<args.Length-1;i++)if(args[i]=="--data-dir")data=args[i+1];
    Directory.CreateDirectory(data);
    if(args.Contains("--stop")){File.WriteAllText(Path.Combine(data,"stop.command"),"passed without authorization");return 0;}
    File.WriteAllText(Path.Combine(data,"core.started"),Process.GetCurrentProcess().Id.ToString());
    string mode=File.ReadAllText(Path.Combine(data,"core-mode")).Trim();
    if(mode=="natural"){Thread.Sleep(250);return 7;}
    if(mode=="startup-clear"){
      var startup=Stopwatch.StartNew();
      while(!File.Exists(Path.Combine(data,"stop.request"))&&startup.Elapsed.TotalSeconds<10)Thread.Sleep(20);
      if(!File.Exists(Path.Combine(data,"stop.request")))return 98;
      File.Delete(Path.Combine(data,"stop.request"));
      File.WriteAllText(Path.Combine(data,"core.discarded-startup-stop"),"initial stop request was removed during startup");
    }
    var watch=Stopwatch.StartNew();
    while(watch.Elapsed.TotalSeconds<120){
      if(File.Exists(Path.Combine(data,"stop.request"))){
        Thread.Sleep(400);File.WriteAllText(Path.Combine(data,"core.saved"),"saved before exiting");return 0;
      }
      Thread.Sleep(20);
    }
    return 99;
  }
}
