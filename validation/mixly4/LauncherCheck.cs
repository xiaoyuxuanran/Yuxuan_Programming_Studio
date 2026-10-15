using System;
using System.IO;
using System.Diagnostics;
internal static partial class Suite {
  internal static void CheckMixlyLaunch(string testData) {
    data=Path.GetFullPath(testData);noBrowser=true;
    var watch=Stopwatch.StartNew();
    try {
      StartMixly();
      if(mixly==null||mixly.HasExited||mixlyUrl==null)throw new Exception("No running Mixly service");
      var url=mixlyUrl;
      if(!Get(url+"health").Contains("YuxuanMixlyWeb"))throw new Exception("Wrong service");
      int pid=mixly.Id;
      StartMixly();
      if(mixly.Id!=pid)throw new Exception("Duplicate service");
      StopTools();
      bool reachable=true;try{Get(url+"health");}catch{reachable=false;}
      if(reachable)throw new Exception("Service survived stop");
      File.WriteAllText(Path.Combine(data,"launcher-result.json"),"{\"ok\":true,\"serviceReused\":true,\"serviceStopped\":true,\"seconds\":"+watch.Elapsed.TotalSeconds.ToString(System.Globalization.CultureInfo.InvariantCulture)+"}");
    } finally {StopTools();}
  }
}
internal static class FixtureMain {
  static int Main(string[] args) {try{Suite.CheckMixlyLaunch(args[0]);return 0;}catch(Exception error){Console.Error.WriteLine(error);return 1;}}
}
