using System;
using System.IO;
using System.Drawing;
using System.Windows.Forms;
using System.Reflection;
using System.Collections.Generic;
using System.Web.Script.Serialization;
internal static class LayoutCheck {
  static List<object> results=new List<object>();
  static void Layout(Control c){foreach(Control child in c.Controls)Layout(child);c.PerformLayout();}
  static void Verify(Control control,List<string> errors){
    foreach(Control child in control.Controls){
      if(child is Label || child is Button){
        if(!control.ClientRectangle.Contains(child.Bounds))errors.Add(child.Text+" exceeds parent: "+child.Bounds+" / "+control.ClientRectangle);
        var label=child as Label;
        if(label!=null && label.AutoSize && label.Height<label.PreferredHeight)errors.Add(label.Text+" text height clipped");
      }
      Verify(child,errors);
    }
  }
  [STAThread] static void Main(string[] args){
    Application.EnableVisualStyles();Application.SetCompatibleTextRenderingDefault(false);
    var output=args[0];Directory.CreateDirectory(output);
    foreach(float scale in new[]{1f,1.25f,1.5f,2f})foreach(bool narrow in new[]{false,true}){
      Suite.BuildLauncherForm();
      var type=typeof(Suite);var form=(Form)type.GetField("form",BindingFlags.Static|BindingFlags.NonPublic).GetValue(null);
      var info=(Label)type.GetField("licenseInfo",BindingFlags.Static|BindingFlags.NonPublic).GetValue(null);
      info.Text="有效期至 2094-12-10 23:59 · 离线授权有效 · 在线验证暂不可用";
      form.Opacity=0;form.Show();Application.DoEvents();form.AutoScaleMode=AutoScaleMode.None;form.Scale(new SizeF(scale,scale));
      if(narrow)form.Size=form.MinimumSize;
      form.CreateControl();for(int i=0;i<4;i++)Layout(form);
      using(var bitmap=new Bitmap(form.Width,form.Height)){form.DrawToBitmap(bitmap,new Rectangle(0,0,bitmap.Width,bitmap.Height));bitmap.Save(Path.Combine(output,"layout-"+scale.ToString("0.00",System.Globalization.CultureInfo.InvariantCulture)+(narrow?"-minimum":"")+".png"));}
      var errors=new List<string>();Verify(form,errors);
      results.Add(new {scale=scale,minimum=narrow,width=form.Width,height=form.Height,errors=errors});form.Dispose();
    }
    File.WriteAllText(Path.Combine(output,"layout.json"),new JavaScriptSerializer().Serialize(results));
  }
}
