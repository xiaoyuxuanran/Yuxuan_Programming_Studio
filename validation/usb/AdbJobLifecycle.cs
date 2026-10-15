// Isolated acceptance fixture. Creates an ADB server on a private random port.
// Only enumerates devices; never installs, launches, or modifies a phone.
using System;
using System.Diagnostics;
using System.IO;
using System.Net;
using System.Net.Sockets;
using System.Runtime.InteropServices;
using System.Threading;

internal static class AdbJobLifecycle {
  [StructLayout(LayoutKind.Sequential)] struct Basic { public long PerProcessUserTimeLimit,PerJobUserTimeLimit; public uint LimitFlags; public UIntPtr MinimumWorkingSetSize,MaximumWorkingSetSize; public uint ActiveProcessLimit; public UIntPtr Affinity; public uint PriorityClass,SchedulingClass; }
  [StructLayout(LayoutKind.Sequential)] struct Io { public ulong ReadOperationCount,WriteOperationCount,OtherOperationCount,ReadTransferCount,WriteTransferCount,OtherTransferCount; }
  [StructLayout(LayoutKind.Sequential)] struct Extended { public Basic BasicLimitInformation; public Io IoInfo; public UIntPtr ProcessMemoryLimit,JobMemoryLimit,PeakProcessMemoryUsed,PeakJobMemoryUsed; }
  [DllImport("kernel32.dll",CharSet=CharSet.Unicode,SetLastError=true)] static extern IntPtr CreateJobObject(IntPtr a,string n);
  [DllImport("kernel32.dll",SetLastError=true)] static extern bool SetInformationJobObject(IntPtr h,int c,IntPtr p,uint n);
  [DllImport("kernel32.dll",SetLastError=true)] static extern bool AssignProcessToJobObject(IntPtr j,IntPtr p);
  [DllImport("kernel32.dll")] static extern bool CloseHandle(IntPtr h);
  static bool Open(int port) { try { using(var client=new TcpClient()) { var result=client.BeginConnect(IPAddress.Loopback,port,null,null); if(!result.AsyncWaitHandle.WaitOne(500)) return false; client.EndConnect(result); return true; } } catch(SocketException) { return false; } }
  static Process Run(string exe,string args,IntPtr job) {
    var process=new Process(); process.StartInfo=new ProcessStartInfo(exe,args) { UseShellExecute=false,CreateNoWindow=true,RedirectStandardOutput=true,RedirectStandardError=true };
    process.Start();
    if(job!=IntPtr.Zero && !AssignProcessToJobObject(job,process.Handle)) throw new Exception("Job assignment failed: "+Marshal.GetLastWin32Error());
    return process;
  }
  static int Main(string[] args) {
    int port; var listener=new TcpListener(IPAddress.Loopback,0); listener.Start(); port=((IPEndPoint)listener.LocalEndpoint).Port; listener.Stop();
    IntPtr job=IntPtr.Zero;
    string adb=Path.GetFullPath(args[0]);
    bool serverStarted=false,serverStopped=false;
    try {
      job=CreateJobObject(IntPtr.Zero,null); var info=new Extended(); info.BasicLimitInformation.LimitFlags=0x2000;
      int size=Marshal.SizeOf(info); IntPtr pointer=Marshal.AllocHGlobal(size);
      try { Marshal.StructureToPtr(info,pointer,false); if(!SetInformationJobObject(job,9,pointer,(uint)size)) throw new Exception("Job setup failed"); }
      finally { Marshal.FreeHGlobal(pointer); }
      using(var process=Run(adb,"-P "+port+" devices -l",job)) {
        string stdout=process.StandardOutput.ReadToEnd(); string stderr=process.StandardError.ReadToEnd();
        process.WaitForExit(); if(process.ExitCode!=0) throw new Exception("Private ADB failed: "+stderr);
      }
      serverStarted=Open(port);
      CloseHandle(job); job=IntPtr.Zero;
      for(int i=0;i<40;i++) { if(!Open(port)) { serverStopped=true; break; } Thread.Sleep(100); }
      string result="{\"privatePort\":"+port+",\"serverStarted\":"+serverStarted.ToString().ToLowerInvariant()+",\"serverStoppedWithCoreJob\":"+serverStopped.ToString().ToLowerInvariant()+",\"physicalInstallationTested\":false}";
      File.WriteAllText(args[1],result+Environment.NewLine);
      Console.WriteLine(result);
      return serverStarted&&serverStopped?0:1;
    } catch(Exception error) {
      Console.WriteLine("Lifecycle fixture failed: "+error.GetType().FullName+"; "+error.Message);
      return 2;
    } finally {
      if(job!=IntPtr.Zero)CloseHandle(job);
      if(Open(port)) { using(var process=Run(adb,"-P "+port+" kill-server",IntPtr.Zero)) { process.WaitForExit(5000); } }
    }
  }
}
