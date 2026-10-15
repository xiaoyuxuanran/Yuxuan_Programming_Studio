using System;
using System.IO;
using System.Linq;
using System.Reflection;
using System.Threading;
using System.Diagnostics;

// Calls production entry/event methods. The private gate hold forces the pre-spawn race.
internal static class NetworkFixture {
  static readonly BindingFlags flags=BindingFlags.Static|BindingFlags.NonPublic;
  static object Field(string name){return typeof(Suite).GetField(name,flags).GetValue(null);}
  static void Wait(Func<bool> predicate){var clock=Stopwatch.StartNew();while(!predicate()){if(clock.Elapsed.TotalSeconds>15)throw new Exception("Fixture wait timed out");Thread.Sleep(20);}}
  static void Changed(){typeof(Suite).GetMethod("NetworkAddressChanged",flags).Invoke(null,new object[]{null,EventArgs.Empty});}
  static void Launch(string[] args){typeof(Suite).GetMethod("Main",flags).Invoke(null,new object[]{args});}
  [STAThread] static int Main(string[] args){
    bool race=args.Contains("--fixture-race");string data=args[Array.IndexOf(args,"--data-dir")+1];
    args=args.Where(x=>!x.StartsWith("--fixture-")).ToArray();Exception failed=null;
    if(race){
      object gate=Field("gate");Monitor.Enter(gate);
      var launch=new Thread(()=>{try{Launch(args);}catch(Exception e){failed=e;}});launch.Start();
      try{
        Wait(()=>Convert.ToBoolean(Field("licensed")));
        File.WriteAllText(Path.Combine(data,"license-mode"),"deny");Changed();
        Wait(()=>Convert.ToInt32(Field("headlessLicenseLost"))==1);
      }finally{Monitor.Exit(gate);}
      if(!launch.Join(15000))throw new Exception("Headless race did not exit");
    }else{
      var change=new Thread(()=>{try{Wait(()=>File.Exists(Path.Combine(data,"core.started")));Changed();}catch(Exception e){failed=e;}});change.Start();
      Launch(args);if(!change.Join(15000))throw new Exception("Network fixture did not finish");
    }
    if(failed!=null)throw failed;
    if(Field("core")!=null||Field("licenseBridge")!=null||Field("licenseTimer")!=null||Convert.ToBoolean(Field("networkSubscribed")))throw new Exception("Headless resources were not cleaned up");
    File.WriteAllText(Path.Combine(data,"resources.cleaned"),"Core reference, bridge, timer and events released");
    return Environment.ExitCode;
  }
}
