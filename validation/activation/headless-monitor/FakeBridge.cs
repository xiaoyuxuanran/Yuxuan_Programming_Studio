using System;
using System.IO;
using System.Diagnostics;
using System.Collections.Generic;
using System.Web.Script.Serialization;

// Isolation fixture: implements the JSON-line transport, without a key or network service.
internal static class FakeBridge {
  static void Main(string[] args) {
    string state=null;for(int i=0;i<args.Length-1;i++)if(args[i]=="--state")state=args[i+1];
    string data=Directory.GetParent(state).FullName;var json=new JavaScriptSerializer();int checks=0;
    string line;
    while((line=Console.ReadLine())!=null){
      var request=json.DeserializeObject(line) as Dictionary<string,object>;
      if(Convert.ToString(request["action"])=="exit"){
        File.WriteAllText(Path.Combine(data,"bridge.exited"),Process.GetCurrentProcess().Id.ToString());return;
      }
      checks++;string mode=File.ReadAllText(Path.Combine(data,"license-mode")).Trim();
      bool valid=mode=="valid"||(mode=="after-first"&&checks==1);
      File.AppendAllText(Path.Combine(data,"checks.ndjson"),json.Serialize(new{check=checks,valid=valid,time=DateTime.UtcNow.ToString("o"),online=request["online"]})+Environment.NewLine);
      Console.WriteLine(json.Serialize(new{ok=valid,message=valid?"Isolated valid grant":"Isolated revoked or expired grant",expires=(object)null}));
      Console.Out.Flush();
    }
  }
}
