#define AppName "Yuxuan Programming Studio"
[Setup]
AppId={{D394BCE3-729B-427F-A3EB-52885E97ED62}
AppName={#AppName}
AppVersion=2.4.6
UninstallLogMode=append
SetupArchitecture=x64
AppPublisher=Yuxuan Programming Studio
DefaultDirName={userpf}\AppInventorOffline
DefaultGroupName={#AppName}
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
MinVersion=10.0
OutputDir=package
OutputBaseFilename=Yuxuan-Programming-Studio-Update-2.4.5-to-2.4.6
Compression=lzma2/normal
LZMADictionarySize=65536
SolidCompression=yes
LZMANumBlockThreads=4
WizardStyle=modern
SetupIconFile=C:\Users\Yuxuan\Documents\Codex\2026-10-02\files-pasted-by-the-user-ap\work\native\resources\brand.ico
DisableProgramGroupPage=yes
UninstallDisplayIcon={app}\AppInventor.exe
CloseApplications=no
AppMutex=Local\AppInventorOfflineDesktop
SetupLogging=yes
InfoBeforeFile=C:\Users\Yuxuan\Documents\Codex\2026-10-02\files-pasted-by-the-user-ap\work\release-2.4.6\before-install.txt

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Shortcuts:"

[Files]
Source: "C:\Users\Yuxuan\Documents\Codex\2026-10-02\files-pasted-by-the-user-ap\work\native\AppInventor.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "C:\Users\Yuxuan\Documents\Codex\2026-10-02\files-pasted-by-the-user-ap\work\native\resources\CHANGELOG.txt"; DestDir: "{app}\resources"; Flags: ignoreversion
Source: "C:\Users\Yuxuan\Documents\Codex\2026-10-02\files-pasted-by-the-user-ap\work\native\resources\build-version.txt"; DestDir: "{app}\resources"; Flags: ignoreversion
Source: "C:\Users\Yuxuan\Documents\Codex\2026-10-02\files-pasted-by-the-user-ap\work\native\resources\distribution-source\Setup.iss"; DestDir: "{app}\resources\distribution-source"; Flags: ignoreversion
Source: "C:\Users\Yuxuan\Documents\Codex\2026-10-02\files-pasted-by-the-user-ap\work\native\resources\distribution-source\SuiteLauncher.cs"; DestDir: "{app}\resources\distribution-source"; Flags: ignoreversion
Source: "C:\Users\Yuxuan\Documents\Codex\2026-10-02\files-pasted-by-the-user-ap\work\native\resources\distribution-source\SuiteLicense.cs"; DestDir: "{app}\resources\distribution-source"; Flags: ignoreversion
Source: "C:\Users\Yuxuan\Documents\Codex\2026-10-02\files-pasted-by-the-user-ap\work\native\resources\distribution-source\SuiteUpdates.cs"; DestDir: "{app}\resources\distribution-source"; Flags: ignoreversion
Source: "C:\Users\Yuxuan\Documents\Codex\2026-10-02\files-pasted-by-the-user-ap\work\native\resources\distribution-source\release-2.4.6\CHANGELOG.txt"; DestDir: "{app}\resources\distribution-source\release-2.4.6"; Flags: ignoreversion
Source: "C:\Users\Yuxuan\Documents\Codex\2026-10-02\files-pasted-by-the-user-ap\work\native\resources\distribution-source\release-2.4.6\UPGRADE.md"; DestDir: "{app}\resources\distribution-source\release-2.4.6"; Flags: ignoreversion
Source: "C:\Users\Yuxuan\Documents\Codex\2026-10-02\files-pasted-by-the-user-ap\work\native\resources\distribution-source\release-2.4.6\User-Guide.txt"; DestDir: "{app}\resources\distribution-source\release-2.4.6"; Flags: ignoreversion
Source: "C:\Users\Yuxuan\Documents\Codex\2026-10-02\files-pasted-by-the-user-ap\work\native\resources\distribution-source\release-2.4.6\prepare.py"; DestDir: "{app}\resources\distribution-source\release-2.4.6"; Flags: ignoreversion
Source: "C:\Users\Yuxuan\Documents\Codex\2026-10-02\files-pasted-by-the-user-ap\work\native\resources\distribution-source\studio\server.py"; DestDir: "{app}\resources\distribution-source\studio"; Flags: ignoreversion
Source: "C:\Users\Yuxuan\Documents\Codex\2026-10-02\files-pasted-by-the-user-ap\work\native\resources\distribution-source\studio\studio.js"; DestDir: "{app}\resources\distribution-source\studio"; Flags: ignoreversion
Source: "C:\Users\Yuxuan\Documents\Codex\2026-10-02\files-pasted-by-the-user-ap\work\native\resources\使用说明.txt"; DestDir: "{app}\resources"; Flags: ignoreversion
Source: "C:\Users\Yuxuan\Documents\Codex\2026-10-02\files-pasted-by-the-user-ap\work\native\studio\server.py"; DestDir: "{app}\studio"; Flags: ignoreversion
Source: "C:\Users\Yuxuan\Documents\Codex\2026-10-02\files-pasted-by-the-user-ap\work\native\studio\studio.js"; DestDir: "{app}\studio"; Flags: ignoreversion
Source: "C:\Users\Yuxuan\Documents\Codex\2026-10-02\files-pasted-by-the-user-ap\work\native\使用说明.txt"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#AppName}"; Filename: "{app}\AppInventor.exe"; WorkingDir: "{app}"
Name: "{group}\Offline User Guide"; Filename: "{app}\resources\使用说明.txt"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\AppInventor.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\AppInventor.exe"; Description: "Launch Yuxuan Programming Studio"; Flags: nowait postinstall skipifsilent

[Code]
function PrepareToInstall(var NeedsRestart: Boolean): String;
var Digest: String;
begin
  Result := '';
  if not FileExists(ExpandConstant('{app}\unins000.dat')) then begin Result := 'Select the existing 2.4.5 installation folder; this is an update package.'; Exit; end;
  if not FileExists(ExpandConstant('{app}\AppInventor.exe')) then begin Result := 'Missing base file: AppInventor.exe'; Exit; end;
  try Digest := Lowercase(GetSHA256OfFile(ExpandConstant('{app}\AppInventor.exe'))); except Result := 'Close the workbench before updating.'; Exit; end;
  if (Digest <> 'c5009d0201c1c49294cff7b0d9bb8bd3f0c70bfaa69359bb515412398dc61bd0') and (Digest <> 'df249afa60758f9f867a2c39bb29ee31dedcf1e07d07270029418cf7deea612c') and (Digest <> 'fc9bcfd3d1601cd0f5dca10de1dbbbda2529c8c8e3e6a11935ae67b4e2583fe7') then begin Result := 'Incompatible base; use the complete installer. File: AppInventor.exe'; Exit; end;
  if not FileExists(ExpandConstant('{app}\resources\CHANGELOG.txt')) then begin Result := 'Missing base file: resources\CHANGELOG.txt'; Exit; end;
  try Digest := Lowercase(GetSHA256OfFile(ExpandConstant('{app}\resources\CHANGELOG.txt'))); except Result := 'Close the workbench before updating.'; Exit; end;
  if (Digest <> '96b7b1ce64c461b6d5bd69df4d95a73f02dd5c42da34d50385a70c88abece590') and (Digest <> 'e8082b93aed1ea821fefdf19998a46550dc72d1e6a6384d07f1a50195478765f') then begin Result := 'Incompatible base; use the complete installer. File: resources\CHANGELOG.txt'; Exit; end;
  if not FileExists(ExpandConstant('{app}\resources\build-version.txt')) then begin Result := 'Missing base file: resources\build-version.txt'; Exit; end;
  try Digest := Lowercase(GetSHA256OfFile(ExpandConstant('{app}\resources\build-version.txt'))); except Result := 'Close the workbench before updating.'; Exit; end;
  if (Digest <> '8650ed03e06fd0e575c573944e0a74cf693da092f30b0c22803330dd59ceca01') and (Digest <> 'e71b05884d02206ecedc38f303b0401e167f726167881b4a0ed69a09c6fa6275') then begin Result := 'Incompatible base; use the complete installer. File: resources\build-version.txt'; Exit; end;
  if not FileExists(ExpandConstant('{app}\resources\distribution-source\Setup.iss')) then begin Result := 'Missing base file: resources\distribution-source\Setup.iss'; Exit; end;
  try Digest := Lowercase(GetSHA256OfFile(ExpandConstant('{app}\resources\distribution-source\Setup.iss'))); except Result := 'Close the workbench before updating.'; Exit; end;
  if (Digest <> 'a96e9795f203494bf31befbe84c95eb2e76db23f9790c7c1b6634c2c3c430539') and (Digest <> 'bb320d391994624470c8d25f3f2e4be437a9918d8404630235a5c46df986ca60') then begin Result := 'Incompatible base; use the complete installer. File: resources\distribution-source\Setup.iss'; Exit; end;
  if not FileExists(ExpandConstant('{app}\resources\distribution-source\SuiteLauncher.cs')) then begin Result := 'Missing base file: resources\distribution-source\SuiteLauncher.cs'; Exit; end;
  try Digest := Lowercase(GetSHA256OfFile(ExpandConstant('{app}\resources\distribution-source\SuiteLauncher.cs'))); except Result := 'Close the workbench before updating.'; Exit; end;
  if (Digest <> '1e3792cdbb3edb3a1c3b6cdaa75c050b25d62dbe2e5598af6d335b3b0866b4f2') and (Digest <> '612656535f6eb818dee8905de193a546e0f67e0c16c187608d6921d324c5c252') and (Digest <> 'be5bfa494ea38cb86e5c7638148a5690ba552e81b8e2b552156bcfe7cb381bdb') then begin Result := 'Incompatible base; use the complete installer. File: resources\distribution-source\SuiteLauncher.cs'; Exit; end;
  if not FileExists(ExpandConstant('{app}\resources\distribution-source\SuiteLicense.cs')) then begin Result := 'Missing base file: resources\distribution-source\SuiteLicense.cs'; Exit; end;
  try Digest := Lowercase(GetSHA256OfFile(ExpandConstant('{app}\resources\distribution-source\SuiteLicense.cs'))); except Result := 'Close the workbench before updating.'; Exit; end;
  if (Digest <> '7ba36c694671973815680738eb3e067855cbbf8bc6311a62e5a98a474f95b673') and (Digest <> 'e1604e067ff695ad95149f8eaabb03d184784239b19322bca9496d91d0c6cb77') then begin Result := 'Incompatible base; use the complete installer. File: resources\distribution-source\SuiteLicense.cs'; Exit; end;
  if not FileExists(ExpandConstant('{app}\resources\distribution-source\SuiteUpdates.cs')) then begin Result := 'Missing base file: resources\distribution-source\SuiteUpdates.cs'; Exit; end;
  try Digest := Lowercase(GetSHA256OfFile(ExpandConstant('{app}\resources\distribution-source\SuiteUpdates.cs'))); except Result := 'Close the workbench before updating.'; Exit; end;
  if (Digest <> '2d5361b79cca4281fe7532df89c686155a271e830d1047f3312cd131cb733c40') and (Digest <> '8b11c176b4a9387ef5e35f05dc56110435a7df101442ffc06bba0d1b631dd56c') then begin Result := 'Incompatible base; use the complete installer. File: resources\distribution-source\SuiteUpdates.cs'; Exit; end;
  if not FileExists(ExpandConstant('{app}\resources\distribution-source\studio\server.py')) then begin Result := 'Missing base file: resources\distribution-source\studio\server.py'; Exit; end;
  try Digest := Lowercase(GetSHA256OfFile(ExpandConstant('{app}\resources\distribution-source\studio\server.py'))); except Result := 'Close the workbench before updating.'; Exit; end;
  if (Digest <> '4870a0a1b5951e7d8cee7b6041c0d146bc5f63e76a49df11f670312a7c1f4456') and (Digest <> 'ba6173c19706cc10a362a9afd0a365589fa48028579e1e9423518013a437921d') then begin Result := 'Incompatible base; use the complete installer. File: resources\distribution-source\studio\server.py'; Exit; end;
  if not FileExists(ExpandConstant('{app}\resources\distribution-source\studio\studio.js')) then begin Result := 'Missing base file: resources\distribution-source\studio\studio.js'; Exit; end;
  try Digest := Lowercase(GetSHA256OfFile(ExpandConstant('{app}\resources\distribution-source\studio\studio.js'))); except Result := 'Close the workbench before updating.'; Exit; end;
  if (Digest <> '384a1ba9e8a5a82e8ee3f4e5cb822149160da62ae3f78bd7df6672f975e89368') and (Digest <> 'f4d77649c3461d25e33f48c122a50fcc0571df7eb084e82f7356b124762daea3') then begin Result := 'Incompatible base; use the complete installer. File: resources\distribution-source\studio\studio.js'; Exit; end;
  if not FileExists(ExpandConstant('{app}\resources\使用说明.txt')) then begin Result := 'Missing base file: resources\使用说明.txt'; Exit; end;
  try Digest := Lowercase(GetSHA256OfFile(ExpandConstant('{app}\resources\使用说明.txt'))); except Result := 'Close the workbench before updating.'; Exit; end;
  if (Digest <> '142b5dc1297fa8ead6a6a477dd4ed2666ea78c06caeace0ec9adf1e741b3487d') and (Digest <> '30f5c6670b044e307cc53293f2b0f4ccf70aa18abd9037ae1d0710b729609a1a') then begin Result := 'Incompatible base; use the complete installer. File: resources\使用说明.txt'; Exit; end;
  if not FileExists(ExpandConstant('{app}\studio\server.py')) then begin Result := 'Missing base file: studio\server.py'; Exit; end;
  try Digest := Lowercase(GetSHA256OfFile(ExpandConstant('{app}\studio\server.py'))); except Result := 'Close the workbench before updating.'; Exit; end;
  if (Digest <> '4870a0a1b5951e7d8cee7b6041c0d146bc5f63e76a49df11f670312a7c1f4456') and (Digest <> 'ba6173c19706cc10a362a9afd0a365589fa48028579e1e9423518013a437921d') then begin Result := 'Incompatible base; use the complete installer. File: studio\server.py'; Exit; end;
  if not FileExists(ExpandConstant('{app}\studio\studio.js')) then begin Result := 'Missing base file: studio\studio.js'; Exit; end;
  try Digest := Lowercase(GetSHA256OfFile(ExpandConstant('{app}\studio\studio.js'))); except Result := 'Close the workbench before updating.'; Exit; end;
  if (Digest <> '384a1ba9e8a5a82e8ee3f4e5cb822149160da62ae3f78bd7df6672f975e89368') and (Digest <> 'f4d77649c3461d25e33f48c122a50fcc0571df7eb084e82f7356b124762daea3') then begin Result := 'Incompatible base; use the complete installer. File: studio\studio.js'; Exit; end;
  if not FileExists(ExpandConstant('{app}\使用说明.txt')) then begin Result := 'Missing base file: 使用说明.txt'; Exit; end;
  try Digest := Lowercase(GetSHA256OfFile(ExpandConstant('{app}\使用说明.txt'))); except Result := 'Close the workbench before updating.'; Exit; end;
  if (Digest <> '142b5dc1297fa8ead6a6a477dd4ed2666ea78c06caeace0ec9adf1e741b3487d') and (Digest <> '30f5c6670b044e307cc53293f2b0f4ccf70aa18abd9037ae1d0710b729609a1a') then begin Result := 'Incompatible base; use the complete installer. File: 使用说明.txt'; Exit; end;
  if not FileExists(ExpandConstant('{app}\AppInventorCore.exe')) then begin Result := 'Missing base file: AppInventorCore.exe'; Exit; end;
  try Digest := Lowercase(GetSHA256OfFile(ExpandConstant('{app}\AppInventorCore.exe'))); except Result := 'Close the workbench before updating.'; Exit; end;
  if (Digest <> 'cf8b3b25fd29c5c3f1c4da3d40d7cbb552e8fe89f44b9a9e95477aae1ee909e5') then begin Result := 'Incompatible base; use the complete installer. File: AppInventorCore.exe'; Exit; end;
  if not FileExists(ExpandConstant('{app}\runtime\python3.13.16\python.exe')) then begin Result := 'Missing base file: runtime\python3.13.16\python.exe'; Exit; end;
  try Digest := Lowercase(GetSHA256OfFile(ExpandConstant('{app}\runtime\python3.13.16\python.exe'))); except Result := 'Close the workbench before updating.'; Exit; end;
  if (Digest <> '31fe10b4ed82a2f960af0ef9931f46a4b84ff286f8b6ffd9dee098cf4f10f17f') then begin Result := 'Incompatible base; use the complete installer. File: runtime\python3.13.16\python.exe'; Exit; end;
  if not FileExists(ExpandConstant('{app}\mixly\arduino-cli\arduino-cli.exe')) then begin Result := 'Missing base file: mixly\arduino-cli\arduino-cli.exe'; Exit; end;
  try Digest := Lowercase(GetSHA256OfFile(ExpandConstant('{app}\mixly\arduino-cli\arduino-cli.exe'))); except Result := 'Close the workbench before updating.'; Exit; end;
  if (Digest <> 'ace4df9b7780e6416f44a4132a748fc1963ee34373b43b42e7c049186b95d79c') then begin Result := 'Incompatible base; use the complete installer. File: mixly\arduino-cli\arduino-cli.exe'; Exit; end;
end;
