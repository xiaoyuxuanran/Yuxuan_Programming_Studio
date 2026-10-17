#define AppName "Yuxuan Programming Studio"
[Setup]
AppId={{D394BCE3-729B-427F-A3EB-52885E97ED62}
AppName={#AppName}
AppVersion=2.3.2
UninstallLogMode=append
InfoBeforeFile=C:\Users\Yuxuan\Documents\Codex\2026-10-02\files-pasted-by-the-user-ap\work\release-2.3.2\before-install.txt
SetupArchitecture=x64
AppPublisher=Yuxuan Programming Studio
DefaultDirName={userpf}\AppInventorOffline
DefaultGroupName={#AppName}
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
MinVersion=10.0
OutputDir=package
OutputBaseFilename=Yuxuan-Programming-Studio-Update-2.2.0-to-2.3.2
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
Source: "C:\Users\Yuxuan\Documents\Codex\2026-10-02\files-pasted-by-the-user-ap\work\native\mixly\UPSTREAM.json"; DestDir: "{app}\mixly"; Flags: ignoreversion
Source: "C:\Users\Yuxuan\Documents\Codex\2026-10-02\files-pasted-by-the-user-ap\work\native\resources\build-version.txt"; DestDir: "{app}\resources"; Flags: ignoreversion
Source: "C:\Users\Yuxuan\Documents\Codex\2026-10-02\files-pasted-by-the-user-ap\work\native\resources\CHANGELOG.txt"; DestDir: "{app}\resources"; Flags: ignoreversion
Source: "C:\Users\Yuxuan\Documents\Codex\2026-10-02\files-pasted-by-the-user-ap\work\native\resources\使用说明.txt"; DestDir: "{app}\resources"; Flags: ignoreversion
Source: "C:\Users\Yuxuan\Documents\Codex\2026-10-02\files-pasted-by-the-user-ap\work\native\server\war\ode\aiblockly-0.nocache.js"; DestDir: "{app}\server\war\ode"; Flags: ignoreversion
Source: "C:\Users\Yuxuan\Documents\Codex\2026-10-02\files-pasted-by-the-user-ap\work\native\server\war\ode\E97340308F1F48B574240B7028CF9424.cache.js"; DestDir: "{app}\server\war\ode"; Flags: ignoreversion
Source: "C:\Users\Yuxuan\Documents\Codex\2026-10-02\files-pasted-by-the-user-ap\work\native\server\war\ode\ode.nocache.js"; DestDir: "{app}\server\war\ode"; Flags: ignoreversion
Source: "C:\Users\Yuxuan\Documents\Codex\2026-10-02\files-pasted-by-the-user-ap\work\native\server\war\WEB-INF\classes\bundled-extensions\BluetoothLE.aix"; DestDir: "{app}\server\war\WEB-INF\classes\bundled-extensions"; Flags: ignoreversion
Source: "C:\Users\Yuxuan\Documents\Codex\2026-10-02\files-pasted-by-the-user-ap\work\native\server\war\WEB-INF\classes\bundled-extensions\ClientSocketAI2Ext.aix"; DestDir: "{app}\server\war\WEB-INF\classes\bundled-extensions"; Flags: ignoreversion
Source: "C:\Users\Yuxuan\Documents\Codex\2026-10-02\files-pasted-by-the-user-ap\work\native\server\war\WEB-INF\classes\bundled-extensions\MqttTCP.aix"; DestDir: "{app}\server\war\WEB-INF\classes\bundled-extensions"; Flags: ignoreversion
Source: "C:\Users\Yuxuan\Documents\Codex\2026-10-02\files-pasted-by-the-user-ap\work\native\server\war\WEB-INF\classes\com\google\appinventor\server\BundledExtensions.class"; DestDir: "{app}\server\war\WEB-INF\classes\com\google\appinventor\server"; Flags: ignoreversion
Source: "C:\Users\Yuxuan\Documents\Codex\2026-10-02\files-pasted-by-the-user-ap\work\native\server\war\WEB-INF\classes\com\google\appinventor\server\project\youngandroid\YoungAndroidProjectService$1.class"; DestDir: "{app}\server\war\WEB-INF\classes\com\google\appinventor\server\project\youngandroid"; Flags: ignoreversion
Source: "C:\Users\Yuxuan\Documents\Codex\2026-10-02\files-pasted-by-the-user-ap\work\native\server\war\WEB-INF\classes\com\google\appinventor\server\project\youngandroid\YoungAndroidProjectService.class"; DestDir: "{app}\server\war\WEB-INF\classes\com\google\appinventor\server\project\youngandroid"; Flags: ignoreversion
Source: "C:\Users\Yuxuan\Documents\Codex\2026-10-02\files-pasted-by-the-user-ap\work\native\server\war\static\images\quality\BluetoothLE.png"; DestDir: "{app}\server\war\static\images\quality"; Flags: ignoreversion
Source: "C:\Users\Yuxuan\Documents\Codex\2026-10-02\files-pasted-by-the-user-ap\work\native\server\war\static\images\quality\ClientSocketAI2Ext.png"; DestDir: "{app}\server\war\static\images\quality"; Flags: ignoreversion
Source: "C:\Users\Yuxuan\Documents\Codex\2026-10-02\files-pasted-by-the-user-ap\work\native\server\war\static\images\quality\MqttTCP.png"; DestDir: "{app}\server\war\static\images\quality"; Flags: ignoreversion
Source: "C:\Users\Yuxuan\Documents\Codex\2026-10-02\files-pasted-by-the-user-ap\work\native\server\war\ode\deferredjs\E97340308F1F48B574240B7028CF9424\1.cache.js"; DestDir: "{app}\server\war\ode\deferredjs\E97340308F1F48B574240B7028CF9424"; Flags: ignoreversion
Source: "C:\Users\Yuxuan\Documents\Codex\2026-10-02\files-pasted-by-the-user-ap\work\native\server\war\ode\deferredjs\E97340308F1F48B574240B7028CF9424\2.cache.js"; DestDir: "{app}\server\war\ode\deferredjs\E97340308F1F48B574240B7028CF9424"; Flags: ignoreversion
Source: "C:\Users\Yuxuan\Documents\Codex\2026-10-02\files-pasted-by-the-user-ap\work\native\server\war\ode\deferredjs\E97340308F1F48B574240B7028CF9424\3.cache.js"; DestDir: "{app}\server\war\ode\deferredjs\E97340308F1F48B574240B7028CF9424"; Flags: ignoreversion
Source: "C:\Users\Yuxuan\Documents\Codex\2026-10-02\files-pasted-by-the-user-ap\work\native\resources\distribution-source\Setup.iss"; DestDir: "{app}\resources\distribution-source"; Flags: ignoreversion
Source: "C:\Users\Yuxuan\Documents\Codex\2026-10-02\files-pasted-by-the-user-ap\work\native\resources\distribution-source\SuiteLauncher.cs"; DestDir: "{app}\resources\distribution-source"; Flags: ignoreversion
Source: "C:\Users\Yuxuan\Documents\Codex\2026-10-02\files-pasted-by-the-user-ap\work\native\resources\distribution-source\SuiteUpdates.cs"; DestDir: "{app}\resources\distribution-source"; Flags: ignoreversion
Source: "C:\Users\Yuxuan\Documents\Codex\2026-10-02\files-pasted-by-the-user-ap\work\native\resources\distribution-source\mixly-adaptation\cloud-fallback.js"; DestDir: "{app}\resources\distribution-source\mixly-adaptation"; Flags: ignoreversion
Source: "C:\Users\Yuxuan\Documents\Codex\2026-10-02\files-pasted-by-the-user-ap\work\native\resources\distribution-source\mixly-adaptation\compiler-paths.py"; DestDir: "{app}\resources\distribution-source\mixly-adaptation"; Flags: ignoreversion
Source: "C:\Users\Yuxuan\Documents\Codex\2026-10-02\files-pasted-by-the-user-ap\work\native\resources\distribution-source\mixly-adaptation\fix-desktop.py"; DestDir: "{app}\resources\distribution-source\mixly-adaptation"; Flags: ignoreversion
Source: "C:\Users\Yuxuan\Documents\Codex\2026-10-02\files-pasted-by-the-user-ap\work\native\resources\distribution-source\mixly-adaptation\prepare-mixly.py"; DestDir: "{app}\resources\distribution-source\mixly-adaptation"; Flags: ignoreversion
Source: "C:\Users\Yuxuan\Documents\Codex\2026-10-02\files-pasted-by-the-user-ap\work\native\resources\distribution-source\mixly-adaptation\sdk-junction.ps1"; DestDir: "{app}\resources\distribution-source\mixly-adaptation"; Flags: ignoreversion
Source: "C:\Users\Yuxuan\Documents\Codex\2026-10-02\files-pasted-by-the-user-ap\work\native\resources\distribution-source\mixly-adaptation\suite-main.js"; DestDir: "{app}\resources\distribution-source\mixly-adaptation"; Flags: ignoreversion
Source: "C:\Users\Yuxuan\Documents\Codex\2026-10-02\files-pasted-by-the-user-ap\work\native\resources\distribution-source\mixly-adaptation\workspace-recovery.js"; DestDir: "{app}\resources\distribution-source\mixly-adaptation"; Flags: ignoreversion
Source: "C:\Users\Yuxuan\Documents\Codex\2026-10-02\files-pasted-by-the-user-ap\work\native\resources\distribution-source\mixly-adaptation\workspace-theme.css"; DestDir: "{app}\resources\distribution-source\mixly-adaptation"; Flags: ignoreversion
Source: "C:\Users\Yuxuan\Documents\Codex\2026-10-02\files-pasted-by-the-user-ap\work\native\resources\distribution-source\mixly4\fix-bluetooth.py"; DestDir: "{app}\resources\distribution-source\mixly4"; Flags: ignoreversion
Source: "C:\Users\Yuxuan\Documents\Codex\2026-10-02\files-pasted-by-the-user-ap\work\native\resources\distribution-source\mixly4\prepare-build.py"; DestDir: "{app}\resources\distribution-source\mixly4"; Flags: ignoreversion
Source: "C:\Users\Yuxuan\Documents\Codex\2026-10-02\files-pasted-by-the-user-ap\work\native\resources\distribution-source\mixly4\stage-web.py"; DestDir: "{app}\resources\distribution-source\mixly4"; Flags: ignoreversion
Source: "C:\Users\Yuxuan\Documents\Codex\2026-10-02\files-pasted-by-the-user-ap\work\native\resources\distribution-source\release-2.3.1\BundledExtensions.java"; DestDir: "{app}\resources\distribution-source\release-2.3.1"; Flags: ignoreversion
Source: "C:\Users\Yuxuan\Documents\Codex\2026-10-02\files-pasted-by-the-user-ap\work\native\resources\distribution-source\release-2.3.1\CHANGELOG.txt"; DestDir: "{app}\resources\distribution-source\release-2.3.1"; Flags: ignoreversion
Source: "C:\Users\Yuxuan\Documents\Codex\2026-10-02\files-pasted-by-the-user-ap\work\native\resources\distribution-source\release-2.3.1\patch-appinventor.py"; DestDir: "{app}\resources\distribution-source\release-2.3.1"; Flags: ignoreversion
Source: "C:\Users\Yuxuan\Documents\Codex\2026-10-02\files-pasted-by-the-user-ap\work\native\resources\distribution-source\release-2.3.1\prepare-extensions.py"; DestDir: "{app}\resources\distribution-source\release-2.3.1"; Flags: ignoreversion
Source: "C:\Users\Yuxuan\Documents\Codex\2026-10-02\files-pasted-by-the-user-ap\work\native\resources\distribution-source\release-2.3.1\prepare-package.py"; DestDir: "{app}\resources\distribution-source\release-2.3.1"; Flags: ignoreversion
Source: "C:\Users\Yuxuan\Documents\Codex\2026-10-02\files-pasted-by-the-user-ap\work\native\resources\distribution-source\release-2.3.1\stage-appinventor.py"; DestDir: "{app}\resources\distribution-source\release-2.3.1"; Flags: ignoreversion
Source: "C:\Users\Yuxuan\Documents\Codex\2026-10-02\files-pasted-by-the-user-ap\work\native\resources\distribution-source\release-2.3.2\CHANGELOG.txt"; DestDir: "{app}\resources\distribution-source\release-2.3.2"; Flags: ignoreversion
Source: "C:\Users\Yuxuan\Documents\Codex\2026-10-02\files-pasted-by-the-user-ap\work\native\resources\distribution-source\release-2.3.2\prepare-package.py"; DestDir: "{app}\resources\distribution-source\release-2.3.2"; Flags: ignoreversion
Source: "C:\Users\Yuxuan\Documents\Codex\2026-10-02\files-pasted-by-the-user-ap\work\native\resources\distribution-source\release-2.3.2\snapshot-installed.py"; DestDir: "{app}\resources\distribution-source\release-2.3.2"; Flags: ignoreversion
Source: "C:\Users\Yuxuan\Documents\Codex\2026-10-02\files-pasted-by-the-user-ap\work\native\resources\distribution-source\release-2.3.1\appinventor-source\AbstractPalettePanel.java"; DestDir: "{app}\resources\distribution-source\release-2.3.1\appinventor-source"; Flags: ignoreversion
Source: "C:\Users\Yuxuan\Documents\Codex\2026-10-02\files-pasted-by-the-user-ap\work\native\resources\distribution-source\release-2.3.1\appinventor-source\BaseComponentFactory.java"; DestDir: "{app}\resources\distribution-source\release-2.3.1\appinventor-source"; Flags: ignoreversion
Source: "C:\Users\Yuxuan\Documents\Codex\2026-10-02\files-pasted-by-the-user-ap\work\native\resources\distribution-source\release-2.3.1\appinventor-source\BlockSelectorBox.java"; DestDir: "{app}\resources\distribution-source\release-2.3.1\appinventor-source"; Flags: ignoreversion
Source: "C:\Users\Yuxuan\Documents\Codex\2026-10-02\files-pasted-by-the-user-ap\work\native\resources\distribution-source\release-2.3.1\appinventor-source\workspace_svg.js"; DestDir: "{app}\resources\distribution-source\release-2.3.1\appinventor-source"; Flags: ignoreversion
Source: "C:\Users\Yuxuan\Documents\Codex\2026-10-02\files-pasted-by-the-user-ap\work\native\resources\distribution-source\release-2.3.1\appinventor-source\YoungAndroidProjectService.java"; DestDir: "{app}\resources\distribution-source\release-2.3.1\appinventor-source"; Flags: ignoreversion
Source: "C:\Users\Yuxuan\Documents\Codex\2026-10-02\files-pasted-by-the-user-ap\work\native\resources\distribution-source\release-2.3.1\bundled-extensions\BluetoothLE.aix"; DestDir: "{app}\resources\distribution-source\release-2.3.1\bundled-extensions"; Flags: ignoreversion
Source: "C:\Users\Yuxuan\Documents\Codex\2026-10-02\files-pasted-by-the-user-ap\work\native\resources\distribution-source\release-2.3.1\bundled-extensions\catalog.json"; DestDir: "{app}\resources\distribution-source\release-2.3.1\bundled-extensions"; Flags: ignoreversion
Source: "C:\Users\Yuxuan\Documents\Codex\2026-10-02\files-pasted-by-the-user-ap\work\native\resources\distribution-source\release-2.3.1\bundled-extensions\ClientSocketAI2Ext.aix"; DestDir: "{app}\resources\distribution-source\release-2.3.1\bundled-extensions"; Flags: ignoreversion
Source: "C:\Users\Yuxuan\Documents\Codex\2026-10-02\files-pasted-by-the-user-ap\work\native\resources\distribution-source\release-2.3.1\bundled-extensions\MqttTCP.aix"; DestDir: "{app}\resources\distribution-source\release-2.3.1\bundled-extensions"; Flags: ignoreversion
Source: "C:\Users\Yuxuan\Documents\Codex\2026-10-02\files-pasted-by-the-user-ap\work\native\resources\distribution-source\mixly-adaptation\bluetooth\blocks.js"; DestDir: "{app}\resources\distribution-source\mixly-adaptation\bluetooth"; Flags: ignoreversion
Source: "C:\Users\Yuxuan\Documents\Codex\2026-10-02\files-pasted-by-the-user-ap\work\native\resources\distribution-source\mixly-adaptation\bluetooth\generators.js"; DestDir: "{app}\resources\distribution-source\mixly-adaptation\bluetooth"; Flags: ignoreversion
Source: "C:\Users\Yuxuan\Documents\Codex\2026-10-02\files-pasted-by-the-user-ap\work\native\resources\distribution-source\mixly-adaptation\bluetooth\toolbox.xml"; DestDir: "{app}\resources\distribution-source\mixly-adaptation\bluetooth"; Flags: ignoreversion
Source: "C:\Users\Yuxuan\Documents\Codex\2026-10-02\files-pasted-by-the-user-ap\work\native\mixly\src\yuxuan-recovery.js"; DestDir: "{app}\mixly\src"; Flags: ignoreversion
Source: "C:\Users\Yuxuan\Documents\Codex\2026-10-02\files-pasted-by-the-user-ap\work\native\mixly\src\yuxuan-workspace.css"; DestDir: "{app}\mixly\src"; Flags: ignoreversion
Source: "C:\Users\Yuxuan\Documents\Codex\2026-10-02\files-pasted-by-the-user-ap\work\native\mixly\src\common\js\blockly_helper.js"; DestDir: "{app}\mixly\src\common\js"; Flags: ignoreversion
Source: "C:\Users\Yuxuan\Documents\Codex\2026-10-02\files-pasted-by-the-user-ap\work\native\mixly\src\common\template\serial-tool.html"; DestDir: "{app}\mixly\src\common\template"; Flags: ignoreversion
Source: "C:\Users\Yuxuan\Documents\Codex\2026-10-02\files-pasted-by-the-user-ap\work\native\mixly\src\common\modules\mixly-modules\common\dom-operator.js"; DestDir: "{app}\mixly\src\common\modules\mixly-modules\common"; Flags: ignoreversion
Source: "C:\Users\Yuxuan\Documents\Codex\2026-10-02\files-pasted-by-the-user-ap\work\native\mixly\src\common\modules\mixly-modules\electron\cloud-download.js"; DestDir: "{app}\mixly\src\common\modules\mixly-modules\electron"; Flags: ignoreversion
Source: "C:\Users\Yuxuan\Documents\Codex\2026-10-02\files-pasted-by-the-user-ap\work\native\mixly\src\boards\default\arduino_esp32\blocks\communicate.js"; DestDir: "{app}\mixly\src\boards\default\arduino_esp32\blocks"; Flags: ignoreversion
Source: "C:\Users\Yuxuan\Documents\Codex\2026-10-02\files-pasted-by-the-user-ap\work\native\mixly\src\boards\default\arduino_esp32\generators\communicate.js"; DestDir: "{app}\mixly\src\boards\default\arduino_esp32\generators"; Flags: ignoreversion
Source: "C:\Users\Yuxuan\Documents\Codex\2026-10-02\files-pasted-by-the-user-ap\work\native\mixly\src\boards\default\arduino_esp32\xml\esp32.xml"; DestDir: "{app}\mixly\src\boards\default\arduino_esp32\xml"; Flags: ignoreversion
Source: "C:\Users\Yuxuan\Documents\Codex\2026-10-02\files-pasted-by-the-user-ap\work\native\mixly\runtime\resources\app\compiler-paths.py"; DestDir: "{app}\mixly\runtime\resources\app"; Flags: ignoreversion
Source: "C:\Users\Yuxuan\Documents\Codex\2026-10-02\files-pasted-by-the-user-ap\work\native\mixly\runtime\resources\app\package.json"; DestDir: "{app}\mixly\runtime\resources\app"; Flags: ignoreversion
Source: "C:\Users\Yuxuan\Documents\Codex\2026-10-02\files-pasted-by-the-user-ap\work\native\mixly\runtime\resources\app\sdk-junction.ps1"; DestDir: "{app}\mixly\runtime\resources\app"; Flags: ignoreversion
Source: "C:\Users\Yuxuan\Documents\Codex\2026-10-02\files-pasted-by-the-user-ap\work\native\mixly\runtime\resources\app\suite-main.js"; DestDir: "{app}\mixly\runtime\resources\app"; Flags: ignoreversion

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
  Result := CheckBaseFile('AppInventor.exe', '853235b85ae6666e4e8518136ac099768d634f74780ced3095f5f1e438cc0021', '4a83a6f1f5da1dca60f97e517cc62cd8541c9d0f6764be3172077f292e3911f2');
  if Result <> '' then Exit;
  Result := CheckBaseFile('mixly\UPSTREAM.json', '0b837c034653213483ecea5983d61cc5fc75925d4788ec07b2d1dbc713834d53', 'da0025cb8c75a78cd52432280958d03f1ff1449f6fcaa5d09bcd9ad4ecf18590');
  if Result <> '' then Exit;
  Result := CheckBaseFile('resources\build-version.txt', '899042bd0cd05e1a330a09b57d145d46009517560646de783c26279905cd0107', 'ae609c9438dc0c6c08eabff9eb1eec5b2292c2597cf28778c4d7242c41b4b847');
  if Result <> '' then Exit;
  Result := CheckBaseFile('resources\使用说明.txt', '1833264b065fbf90e1766e5d00ef23bf5ad924e0ae35b21cf132411f1fd2ee0c', 'e045a2603d2075f8276d9e78aa52306dfeaa3de0976f8ed5d432d30963178249');
  if Result <> '' then Exit;
  Result := CheckBaseFile('server\war\ode\aiblockly-0.nocache.js', '58a947677b6670cb57b24ccbb66f1b19d509330ea77d9841851ddcbb670000b7', '71f566a16ed17191b7bbacf400e9817a4f02326c7b8530487d3635d5c30aab8f');
  if Result <> '' then Exit;
  Result := CheckBaseFile('server\war\ode\ode.nocache.js', '50e6254ff9df8a596c83cadb1708e196996190bf8ad430a732dd75142bd94fb5', 'ec9ef624ac103080fc8b5e5f23c8db638b17675c645c5f23f46677e0744f8b57');
  if Result <> '' then Exit;
  Result := CheckBaseFile('server\war\WEB-INF\classes\com\google\appinventor\server\project\youngandroid\YoungAndroidProjectService$1.class', '49cfc3dad0719d965cfdebab1b9ba694da18e984f299671c58eaf15291df35d4', '5cc6b97cf7143f166e341e04365fb5f14d44ac40d816fa6028cb4ac4b0156618');
  if Result <> '' then Exit;
  Result := CheckBaseFile('server\war\WEB-INF\classes\com\google\appinventor\server\project\youngandroid\YoungAndroidProjectService.class', '19b13d7a076d27528eab9cb00b0cc1c5d14274d09d65f2183364bac290518d93', 'b1a748ce6481546c3fcd2515567c198a1e6f8db15b00f324c9630585c7f0ed6e');
  if Result <> '' then Exit;
  Result := CheckBaseFile('resources\distribution-source\Setup.iss', '0523196157d1d9dacf3d154265072eda5b1a50501ae4f6935f57c8b6e7041ea9', '910c0a7163efbaa99cd86bccb495142fbd694e984ae599684a9cd31e736f23ba');
  if Result <> '' then Exit;
  Result := CheckBaseFile('resources\distribution-source\SuiteLauncher.cs', '90db2d82e6a370e83457f07a89c9d200c627d7b8444769ebf4eeef948efbbe83', 'be5bfa494ea38cb86e5c7638148a5690ba552e81b8e2b552156bcfe7cb381bdb');
  if Result <> '' then Exit;
  Result := CheckBaseFile('resources\distribution-source\mixly-adaptation\compiler-paths.py', '3aa95b6907c0b6753776a37e120c2dab659c898f963197ddef1926c3c7093b8a', '0316c2ad7a251dc2243610fcdac2b608cca6ae18cff782bbe83c4ab80c768402');
  if Result <> '' then Exit;
  Result := CheckBaseFile('resources\distribution-source\mixly-adaptation\prepare-mixly.py', '35d65b5bea90fcdad1e1159452dc4ba85073d9a066f6358c4183d004266c9554', '166bab5b84321227bc25460955e57a780f34a929c6e14aa99462a03a0453f246');
  if Result <> '' then Exit;
  Result := CheckBaseFile('resources\distribution-source\mixly-adaptation\sdk-junction.ps1', 'dfc6cd0bd70caa996a639aba48fc7f6189029ce7d4e0bdd71c1e6fbcab825912', '234bdff84ae905b5f02ccbc328ca1cd8d0c805b8b4c77b9c9a5316bbb3d41855');
  if Result <> '' then Exit;
  Result := CheckBaseFile('resources\distribution-source\mixly-adaptation\suite-main.js', '8d6f9c6efded6b1af6aceaa4cb2b2a68d6a0cda8b225e64cc99189a3defaf212', '39cf5bd3a9311446dee454a15afaab39287f6cef5334fd69f84437ddb13e1eb5');
  if Result <> '' then Exit;
  Result := CheckBaseFile('resources\distribution-source\mixly-adaptation\workspace-recovery.js', '87f979fd3ff70f29ac462f4544aa1d2dda700c4a2be8fb0aaa1dd4e8123c0ee9', 'e1b6ae50d0c8016a69abe5e0824196f8988f0475083ba98e3a9e592a5cf09786');
  if Result <> '' then Exit;
  Result := CheckBaseFile('resources\distribution-source\mixly-adaptation\workspace-theme.css', '4ea43e0b69ca052ae182377839578902e3d4020bf290a97a486da23b3b8abfde', 'ea0cf12bab4b0a44f91166ec40d6a770200386cf660dd621bf74150cbc27a9df');
  if Result <> '' then Exit;
  Result := CheckBaseFile('mixly\src\yuxuan-recovery.js', '87f979fd3ff70f29ac462f4544aa1d2dda700c4a2be8fb0aaa1dd4e8123c0ee9', 'e1b6ae50d0c8016a69abe5e0824196f8988f0475083ba98e3a9e592a5cf09786');
  if Result <> '' then Exit;
  Result := CheckBaseFile('mixly\src\yuxuan-workspace.css', '4ea43e0b69ca052ae182377839578902e3d4020bf290a97a486da23b3b8abfde', 'ea0cf12bab4b0a44f91166ec40d6a770200386cf660dd621bf74150cbc27a9df');
  if Result <> '' then Exit;
  Result := CheckBaseFile('mixly\src\common\js\blockly_helper.js', 'ff4ee241ca8289e889e5e5db0c8b0aa780e466eac6f2ee708db9d155bd44e094', 'eb06140a2248fc56078aad1c2847ae8ee0346d0fcb6ce4cfd8fbf6803fd8da0d');
  if Result <> '' then Exit;
  Result := CheckBaseFile('mixly\src\common\template\serial-tool.html', '2d0a9fbf3b06515fa00583e5c4afa2a42414de1849cfcd06fd1e983d77a4380a', 'abbc41ebe8c1ddc64f5fa26e41af6c7d6cd381a2ad00fcf009852a69aa1d59c5');
  if Result <> '' then Exit;
  Result := CheckBaseFile('mixly\src\common\modules\mixly-modules\common\dom-operator.js', 'c5f683a37b51928cec97e7d48f70c5e9d439ac1dddda0713d22a73d13dda5e55', 'abe39d5da46a70d9dce4edf836e3b4390b576b096374b84d69e2934116b1d7e1');
  if Result <> '' then Exit;
  Result := CheckBaseFile('mixly\src\common\modules\mixly-modules\electron\cloud-download.js', '719f9f5af916a31793263f276e73e6fa9b41d09102438af3da32eb90f483fabe', '0ecbc0f6da88c67ac2a40f6d17fef9ba3b24eafa93e769bc799b709fec0a9b53');
  if Result <> '' then Exit;
  Result := CheckBaseFile('mixly\src\boards\default\arduino_esp32\blocks\communicate.js', '1918c36e70c8ec06435951f0095800c6c9652ce75d24d427a5cec440df926fa6', '98cfe1d912991e56d0fe568df7af4d13055b5feadc60b6e96f543a658c2cc087');
  if Result <> '' then Exit;
  Result := CheckBaseFile('mixly\src\boards\default\arduino_esp32\generators\communicate.js', '5ec34583a67074b5190f2bc9abd92616d0e5e107584746d87079d69de2439932', 'b686d6a1860e43f028ecdc62717ea639ec7fa1db26b078209c55eb3fe28d3ea3');
  if Result <> '' then Exit;
  Result := CheckBaseFile('mixly\src\boards\default\arduino_esp32\xml\esp32.xml', 'ad431a2067ae3b132c90d4c88e96b8d5d39fc7a74cf85830b9da06efef82034a', '08542858edbb3fc3fdc83b7aa1852ed6d2d7b895c7f344ba88ebc5be75dee9f7');
  if Result <> '' then Exit;
  Result := CheckBaseFile('mixly\runtime\resources\app\compiler-paths.py', '3aa95b6907c0b6753776a37e120c2dab659c898f963197ddef1926c3c7093b8a', '0316c2ad7a251dc2243610fcdac2b608cca6ae18cff782bbe83c4ab80c768402');
  if Result <> '' then Exit;
  Result := CheckBaseFile('mixly\runtime\resources\app\package.json', 'b577e91c1c9a7acf508a033214716b42ec62bcd4ee9fa39c3ba8ec0ce07bf64f', '899a02a73f1ad833cfe550059485c975e32fca9e5989f1ed7d6f43b6dae421de');
  if Result <> '' then Exit;
  Result := CheckBaseFile('mixly\runtime\resources\app\sdk-junction.ps1', 'dfc6cd0bd70caa996a639aba48fc7f6189029ce7d4e0bdd71c1e6fbcab825912', '234bdff84ae905b5f02ccbc328ca1cd8d0c805b8b4c77b9c9a5316bbb3d41855');
  if Result <> '' then Exit;
  Result := CheckBaseFile('mixly\runtime\resources\app\suite-main.js', '8d6f9c6efded6b1af6aceaa4cb2b2a68d6a0cda8b225e64cc99189a3defaf212', '39cf5bd3a9311446dee454a15afaab39287f6cef5334fd69f84437ddb13e1eb5');
  if Result <> '' then Exit;
  Result := CheckBaseFile('AppInventorCore.exe', 'cf8b3b25fd29c5c3f1c4da3d40d7cbb552e8fe89f44b9a9e95477aae1ee909e5', 'cf8b3b25fd29c5c3f1c4da3d40d7cbb552e8fe89f44b9a9e95477aae1ee909e5');
  if Result <> '' then Exit;
  Result := CheckBaseFile('runtime\python3.13.16\python.exe', '31fe10b4ed82a2f960af0ef9931f46a4b84ff286f8b6ffd9dee098cf4f10f17f', '31fe10b4ed82a2f960af0ef9931f46a4b84ff286f8b6ffd9dee098cf4f10f17f');
  if Result <> '' then Exit;
  Result := CheckBaseFile('mixly\arduino-cli\arduino-cli.exe', 'ace4df9b7780e6416f44a4132a748fc1963ee34373b43b42e7c049186b95d79c', 'ace4df9b7780e6416f44a4132a748fc1963ee34373b43b42e7c049186b95d79c');
  if Result <> '' then Exit;
end;
