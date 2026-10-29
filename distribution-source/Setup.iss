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
OutputDir=..\outputs
OutputBaseFilename=AppInventor-Offline-Setup-x64
Compression=lzma2/normal
LZMADictionarySize=65536
SolidCompression=yes
LZMANumBlockThreads=4
WizardStyle=modern
SetupIconFile=native\resources\brand.ico
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
Source: "native\*"; DestDir: "{app}"; Excludes: "mixly\arduino-cli\Arduino15\inventory.yaml,server\war\WEB-INF\authkey\*,server\war\WEB-INF\keystore\*,server\war\WEB-INF\appengine-generated\*,mixly\web\*,AppInventor-2.*-*.exe,LayoutCheck.exe,*\__pycache__\*"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#AppName}"; Filename: "{app}\AppInventor.exe"; WorkingDir: "{app}"
Name: "{group}\Offline User Guide"; Filename: "{app}\resources\使用说明.txt"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\AppInventor.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\AppInventor.exe"; Description: "Launch Yuxuan Programming Studio"; Flags: nowait postinstall skipifsilent
