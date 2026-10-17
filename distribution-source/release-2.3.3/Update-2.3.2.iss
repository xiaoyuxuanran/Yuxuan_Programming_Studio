#define AppName "Yuxuan Programming Studio"
[Setup]
AppId={{D394BCE3-729B-427F-A3EB-52885E97ED62}
AppName={#AppName}
AppVersion=2.3.3
UninstallLogMode=append
InfoBeforeFile=C:\Users\Yuxuan\Documents\Codex\2026-10-02\files-pasted-by-the-user-ap\work\release-2.3.3\before-install.txt
SetupArchitecture=x64
AppPublisher=Yuxuan Programming Studio
DefaultDirName={userpf}\AppInventorOffline
DefaultGroupName={#AppName}
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
MinVersion=10.0
OutputDir=package
OutputBaseFilename=Yuxuan-Programming-Studio-Update-2.3.2-to-2.3.3
Compression=lzma2/max
SolidCompression=yes
LZMANumBlockThreads=8
WizardStyle=modern
SetupIconFile=C:\Users\Yuxuan\Documents\Codex\2026-10-02\files-pasted-by-the-user-ap\work\native\resources\brand.ico
DisableProgramGroupPage=yes
UninstallDisplayIcon={app}\AppInventor.exe
CloseApplications=no
AppMutex=Local\AppInventorOfflineDesktop
SetupLogging=yes

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Shortcuts:"

[Files]
Source: "C:\Users\Yuxuan\Documents\Codex\2026-10-02\files-pasted-by-the-user-ap\work\native\AppInventor.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "C:\Users\Yuxuan\Documents\Codex\2026-10-02\files-pasted-by-the-user-ap\work\native\resources\build-version.txt"; DestDir: "{app}\resources"; Flags: ignoreversion
Source: "C:\Users\Yuxuan\Documents\Codex\2026-10-02\files-pasted-by-the-user-ap\work\native\resources\CHANGELOG.txt"; DestDir: "{app}\resources"; Flags: ignoreversion
Source: "C:\Users\Yuxuan\Documents\Codex\2026-10-02\files-pasted-by-the-user-ap\work\native\resources\使用说明.txt"; DestDir: "{app}\resources"; Flags: ignoreversion
Source: "C:\Users\Yuxuan\Documents\Codex\2026-10-02\files-pasted-by-the-user-ap\work\native\studio\index.html"; DestDir: "{app}\studio"; Flags: ignoreversion
Source: "C:\Users\Yuxuan\Documents\Codex\2026-10-02\files-pasted-by-the-user-ap\work\native\studio\server.py"; DestDir: "{app}\studio"; Flags: ignoreversion
Source: "C:\Users\Yuxuan\Documents\Codex\2026-10-02\files-pasted-by-the-user-ap\work\native\studio\studio.css"; DestDir: "{app}\studio"; Flags: ignoreversion
Source: "C:\Users\Yuxuan\Documents\Codex\2026-10-02\files-pasted-by-the-user-ap\work\native\studio\studio.js"; DestDir: "{app}\studio"; Flags: ignoreversion
Source: "C:\Users\Yuxuan\Documents\Codex\2026-10-02\files-pasted-by-the-user-ap\work\native\resources\distribution-source\Setup.iss"; DestDir: "{app}\resources\distribution-source"; Flags: ignoreversion
Source: "C:\Users\Yuxuan\Documents\Codex\2026-10-02\files-pasted-by-the-user-ap\work\native\resources\distribution-source\SuiteUpdates.cs"; DestDir: "{app}\resources\distribution-source"; Flags: ignoreversion
Source: "C:\Users\Yuxuan\Documents\Codex\2026-10-02\files-pasted-by-the-user-ap\work\native\resources\distribution-source\studio\index.html"; DestDir: "{app}\resources\distribution-source\studio"; Flags: ignoreversion
Source: "C:\Users\Yuxuan\Documents\Codex\2026-10-02\files-pasted-by-the-user-ap\work\native\resources\distribution-source\studio\server.py"; DestDir: "{app}\resources\distribution-source\studio"; Flags: ignoreversion
Source: "C:\Users\Yuxuan\Documents\Codex\2026-10-02\files-pasted-by-the-user-ap\work\native\resources\distribution-source\studio\studio.css"; DestDir: "{app}\resources\distribution-source\studio"; Flags: ignoreversion
Source: "C:\Users\Yuxuan\Documents\Codex\2026-10-02\files-pasted-by-the-user-ap\work\native\resources\distribution-source\studio\studio.js"; DestDir: "{app}\resources\distribution-source\studio"; Flags: ignoreversion
Source: "C:\Users\Yuxuan\Documents\Codex\2026-10-02\files-pasted-by-the-user-ap\work\native\使用说明.txt"; DestDir: "{app}"; Flags: ignoreversion
Source: "C:\Users\Yuxuan\Documents\Codex\2026-10-02\files-pasted-by-the-user-ap\work\native\resources\distribution-source\release-2.3.3\CHANGELOG.txt"; DestDir: "{app}\resources\distribution-source\release-2.3.3"; Flags: ignoreversion
Source: "C:\Users\Yuxuan\Documents\Codex\2026-10-02\files-pasted-by-the-user-ap\work\native\resources\distribution-source\release-2.3.3\prepare-package.py"; DestDir: "{app}\resources\distribution-source\release-2.3.3"; Flags: ignoreversion

[Icons]
Name: "{group}\{#AppName}"; Filename: "{app}\AppInventor.exe"; WorkingDir: "{app}"
Name: "{group}\Offline User Guide"; Filename: "{app}\resources\使用说明.txt"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\AppInventor.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\AppInventor.exe"; Description: "Launch Yuxuan Programming Studio"; Flags: nowait postinstall skipifsilent

[Code]
function CheckBaseFile(const Relative, BaseHash, NewHash: String): String;
var Digest: String;
begin
  Result := '';
  if not FileExists(AddBackslash(ExpandConstant('{app}')) + Relative) then begin
    Result := '基础文件缺失，请选择原安装目录：' + Relative; Exit;
  end;
  try Digest := Lowercase(GetSHA256OfFile(AddBackslash(ExpandConstant('{app}')) + Relative));
  except Result := '无法检查基础文件，请先退出软件：' + Relative; Exit; end;
  if (Digest <> BaseHash) and (Digest <> NewHash) then
    Result := '版本或文件不匹配，请下载与当前版本对应的更新包：' + Relative;
end;
function PrepareToInstall(var NeedsRestart: Boolean): String;
begin
  Result := '';
  if not FileExists(ExpandConstant('{app}\unins000.dat')) then begin
    Result := '请先安装完整基础版，并选择原安装目录。此文件是更新包。'; Exit;
  end;
  Result := CheckBaseFile('AppInventor.exe', '4a83a6f1f5da1dca60f97e517cc62cd8541c9d0f6764be3172077f292e3911f2', '5f4b68a95b9ff8ba331acba3da82fe833356c70841581726a12769d907ccfe58');
  if Result <> '' then Exit;
  Result := CheckBaseFile('resources\build-version.txt', 'ae609c9438dc0c6c08eabff9eb1eec5b2292c2597cf28778c4d7242c41b4b847', 'f4c803aea0c05f6e0694387a802d60c278e1626812cf52629a1686fbb41864a4');
  if Result <> '' then Exit;
  Result := CheckBaseFile('resources\CHANGELOG.txt', '552823f98afa01e33dd0881b7d522481f64adb575c618710453099dd734642b7', 'b9403a3e85c9e3945e3b3597e546b3084a068a4a95aac136fd158748e333ed78');
  if Result <> '' then Exit;
  Result := CheckBaseFile('resources\使用说明.txt', 'e045a2603d2075f8276d9e78aa52306dfeaa3de0976f8ed5d432d30963178249', 'd758c8a655c604c9ed08815578d78805630e3af383202e16148997b42baab3c4');
  if Result <> '' then Exit;
  Result := CheckBaseFile('studio\index.html', '3727b9e1cdaf39e62f52455b049ed609a89841197505313c7b0e04feb8e35cd7', 'ac0db5e6680210aa09875c41e5d29fdc89693fd8d2166516394116d5314ff284');
  if Result <> '' then Exit;
  Result := CheckBaseFile('studio\server.py', '6a79acd7e4e4c01f0b82dd572fd64ceddb239242554d0fd9d916901f6f9376a3', '4870a0a1b5951e7d8cee7b6041c0d146bc5f63e76a49df11f670312a7c1f4456');
  if Result <> '' then Exit;
  Result := CheckBaseFile('studio\studio.css', '5389b7e9fadef81bf4379c79cb623943f0c6fa258e599761b624f58f1f46e522', '3baba29f15f6381933896f2b8c203387950b5c04c8bf2ab6d3570ccfd4b2dea3');
  if Result <> '' then Exit;
  Result := CheckBaseFile('studio\studio.js', '6ba80072134fb98c99a9a4080d4aa9394c03ae48c196c8bb964341a9987cb899', 'f4d77649c3461d25e33f48c122a50fcc0571df7eb084e82f7356b124762daea3');
  if Result <> '' then Exit;
  Result := CheckBaseFile('resources\distribution-source\Setup.iss', '910c0a7163efbaa99cd86bccb495142fbd694e984ae599684a9cd31e736f23ba', 'a9f3d626a2d45b99e192e9dc89646b46f2b5f719a62228120d4f61e4da14462b');
  if Result <> '' then Exit;
  Result := CheckBaseFile('resources\distribution-source\SuiteUpdates.cs', 'feb3e2dbd6f8334671db53b9e211caf15b1bd8e153c815b67cb8d59cf23d2633', 'e009c792de161b022f383b352770db491acd2904a2acb59338acb53fd4a2ffa5');
  if Result <> '' then Exit;
  Result := CheckBaseFile('resources\distribution-source\studio\index.html', '3727b9e1cdaf39e62f52455b049ed609a89841197505313c7b0e04feb8e35cd7', 'ac0db5e6680210aa09875c41e5d29fdc89693fd8d2166516394116d5314ff284');
  if Result <> '' then Exit;
  Result := CheckBaseFile('resources\distribution-source\studio\server.py', '6a79acd7e4e4c01f0b82dd572fd64ceddb239242554d0fd9d916901f6f9376a3', '4870a0a1b5951e7d8cee7b6041c0d146bc5f63e76a49df11f670312a7c1f4456');
  if Result <> '' then Exit;
  Result := CheckBaseFile('resources\distribution-source\studio\studio.css', '5389b7e9fadef81bf4379c79cb623943f0c6fa258e599761b624f58f1f46e522', '3baba29f15f6381933896f2b8c203387950b5c04c8bf2ab6d3570ccfd4b2dea3');
  if Result <> '' then Exit;
  Result := CheckBaseFile('resources\distribution-source\studio\studio.js', '6ba80072134fb98c99a9a4080d4aa9394c03ae48c196c8bb964341a9987cb899', 'f4d77649c3461d25e33f48c122a50fcc0571df7eb084e82f7356b124762daea3');
  if Result <> '' then Exit;
  Result := CheckBaseFile('AppInventorCore.exe', 'cf8b3b25fd29c5c3f1c4da3d40d7cbb552e8fe89f44b9a9e95477aae1ee909e5', 'cf8b3b25fd29c5c3f1c4da3d40d7cbb552e8fe89f44b9a9e95477aae1ee909e5');
  if Result <> '' then Exit;
  Result := CheckBaseFile('runtime\python3.13.16\python.exe', '31fe10b4ed82a2f960af0ef9931f46a4b84ff286f8b6ffd9dee098cf4f10f17f', '31fe10b4ed82a2f960af0ef9931f46a4b84ff286f8b6ffd9dee098cf4f10f17f');
  if Result <> '' then Exit;
  Result := CheckBaseFile('mixly\arduino-cli\arduino-cli.exe', 'ace4df9b7780e6416f44a4132a748fc1963ee34373b43b42e7c049186b95d79c', 'ace4df9b7780e6416f44a4132a748fc1963ee34373b43b42e7c049186b95d79c');
  if Result <> '' then Exit;
end;
