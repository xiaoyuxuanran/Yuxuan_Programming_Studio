using System;using System.IO;using System.Reflection;using System.Windows.Forms;
class ComponentProbe{
 [STAThread]static int Main(string[] args){try{
  Application.EnableVisualStyles();var flags=BindingFlags.Static|BindingFlags.NonPublic|BindingFlags.Public;
  var suite=Assembly.LoadFile(Path.GetFullPath(args[0]+"/AppInventor.exe")).GetType("Suite");
  suite.GetField("root",flags).SetValue(null,Path.GetFullPath(args[0]));
  suite.GetField("data",flags).SetValue(null,Path.GetFullPath(args[2]));
  var modes=new[]{"ai","mixly","python","cpp"};
  foreach(var mode in modes){bool actual=(bool)suite.GetMethod("ToolInstalled",flags).Invoke(null,new object[]{mode});if(actual!=(Array.IndexOf(args[1].Split(','),mode)>=0))throw new Exception("Wrong availability "+mode);}
  suite.GetMethod("BuildLauncherForm",flags).Invoke(null,null);
  suite.GetField("licensed",flags).SetValue(null,true);suite.GetMethod("EnableInstalledChoices",flags).Invoke(null,null);
  var buttons=(Button[])suite.GetField("choices",flags).GetValue(null);foreach(var b in buttons){bool expected=Array.IndexOf(args[1].Split(','),(string)b.Tag)>=0;if(b.Enabled!=expected||(!expected&&!b.Text.Contains("未安装")))throw new Exception("Wrong launcher entry "+b.Tag);}
  ((Form)suite.GetField("form",flags).GetValue(null)).Dispose();suite.GetField("form",flags).SetValue(null,null);
  var result=suite.GetMethod("LicenseRequest",flags).Invoke(null,new object[]{"check",null});if(result==null)throw new Exception("Missing license bridge response");suite.GetMethod("StopLicense",flags).Invoke(null,null);
  Console.WriteLine("PASS component discovery, launcher entries and shared authorization runtime: "+args[1]);return 0;
 }catch(Exception e){Console.Error.WriteLine(e.InnerException??e);return 1;}}
}
