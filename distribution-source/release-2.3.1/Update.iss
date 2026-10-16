#define AppName "Yuxuan Programming Studio"
[Setup]
AppId={{D394BCE3-729B-427F-A3EB-52885E97ED62}
AppName={#AppName}
AppVersion=2.3.1
AppComments=Incremental upgrade from version 2.3.0
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
OutputBaseFilename=Yuxuan-Programming-Studio-Update-2.3.0-to-2.3.1
Compression=lzma2/normal
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
Source: "C:\Users\Yuxuan\Documents\Codex\2026-10-02\files-pasted-by-the-user-ap\work\native\resources\distribution-source\mixly4\fix-bluetooth.py"; DestDir: "{app}\resources\distribution-source\mixly4"; Flags: ignoreversion
Source: "C:\Users\Yuxuan\Documents\Codex\2026-10-02\files-pasted-by-the-user-ap\work\native\resources\distribution-source\mixly4\prepare-build.py"; DestDir: "{app}\resources\distribution-source\mixly4"; Flags: ignoreversion
Source: "C:\Users\Yuxuan\Documents\Codex\2026-10-02\files-pasted-by-the-user-ap\work\native\resources\distribution-source\mixly4\stage-web.py"; DestDir: "{app}\resources\distribution-source\mixly4"; Flags: ignoreversion
Source: "C:\Users\Yuxuan\Documents\Codex\2026-10-02\files-pasted-by-the-user-ap\work\native\resources\distribution-source\release-2.3.1\BundledExtensions.java"; DestDir: "{app}\resources\distribution-source\release-2.3.1"; Flags: ignoreversion
Source: "C:\Users\Yuxuan\Documents\Codex\2026-10-02\files-pasted-by-the-user-ap\work\native\resources\distribution-source\release-2.3.1\CHANGELOG.txt"; DestDir: "{app}\resources\distribution-source\release-2.3.1"; Flags: ignoreversion
Source: "C:\Users\Yuxuan\Documents\Codex\2026-10-02\files-pasted-by-the-user-ap\work\native\resources\distribution-source\release-2.3.1\patch-appinventor.py"; DestDir: "{app}\resources\distribution-source\release-2.3.1"; Flags: ignoreversion
Source: "C:\Users\Yuxuan\Documents\Codex\2026-10-02\files-pasted-by-the-user-ap\work\native\resources\distribution-source\release-2.3.1\prepare-extensions.py"; DestDir: "{app}\resources\distribution-source\release-2.3.1"; Flags: ignoreversion
Source: "C:\Users\Yuxuan\Documents\Codex\2026-10-02\files-pasted-by-the-user-ap\work\native\resources\distribution-source\release-2.3.1\prepare-package.py"; DestDir: "{app}\resources\distribution-source\release-2.3.1"; Flags: ignoreversion
Source: "C:\Users\Yuxuan\Documents\Codex\2026-10-02\files-pasted-by-the-user-ap\work\native\resources\distribution-source\release-2.3.1\stage-appinventor.py"; DestDir: "{app}\resources\distribution-source\release-2.3.1"; Flags: ignoreversion
Source: "C:\Users\Yuxuan\Documents\Codex\2026-10-02\files-pasted-by-the-user-ap\work\native\resources\distribution-source\release-2.3.1\appinventor-source\AbstractPalettePanel.java"; DestDir: "{app}\resources\distribution-source\release-2.3.1\appinventor-source"; Flags: ignoreversion
Source: "C:\Users\Yuxuan\Documents\Codex\2026-10-02\files-pasted-by-the-user-ap\work\native\resources\distribution-source\release-2.3.1\appinventor-source\BaseComponentFactory.java"; DestDir: "{app}\resources\distribution-source\release-2.3.1\appinventor-source"; Flags: ignoreversion
Source: "C:\Users\Yuxuan\Documents\Codex\2026-10-02\files-pasted-by-the-user-ap\work\native\resources\distribution-source\release-2.3.1\appinventor-source\BlockSelectorBox.java"; DestDir: "{app}\resources\distribution-source\release-2.3.1\appinventor-source"; Flags: ignoreversion
Source: "C:\Users\Yuxuan\Documents\Codex\2026-10-02\files-pasted-by-the-user-ap\work\native\resources\distribution-source\release-2.3.1\appinventor-source\workspace_svg.js"; DestDir: "{app}\resources\distribution-source\release-2.3.1\appinventor-source"; Flags: ignoreversion
Source: "C:\Users\Yuxuan\Documents\Codex\2026-10-02\files-pasted-by-the-user-ap\work\native\resources\distribution-source\release-2.3.1\appinventor-source\YoungAndroidProjectService.java"; DestDir: "{app}\resources\distribution-source\release-2.3.1\appinventor-source"; Flags: ignoreversion
Source: "C:\Users\Yuxuan\Documents\Codex\2026-10-02\files-pasted-by-the-user-ap\work\native\resources\distribution-source\release-2.3.1\bundled-extensions\BluetoothLE.aix"; DestDir: "{app}\resources\distribution-source\release-2.3.1\bundled-extensions"; Flags: ignoreversion
Source: "C:\Users\Yuxuan\Documents\Codex\2026-10-02\files-pasted-by-the-user-ap\work\native\resources\distribution-source\release-2.3.1\bundled-extensions\catalog.json"; DestDir: "{app}\resources\distribution-source\release-2.3.1\bundled-extensions"; Flags: ignoreversion
Source: "C:\Users\Yuxuan\Documents\Codex\2026-10-02\files-pasted-by-the-user-ap\work\native\resources\distribution-source\release-2.3.1\bundled-extensions\ClientSocketAI2Ext.aix"; DestDir: "{app}\resources\distribution-source\release-2.3.1\bundled-extensions"; Flags: ignoreversion
Source: "C:\Users\Yuxuan\Documents\Codex\2026-10-02\files-pasted-by-the-user-ap\work\native\resources\distribution-source\release-2.3.1\bundled-extensions\MqttTCP.aix"; DestDir: "{app}\resources\distribution-source\release-2.3.1\bundled-extensions"; Flags: ignoreversion
Source: "C:\Users\Yuxuan\Documents\Codex\2026-10-02\files-pasted-by-the-user-ap\work\native\mixly\web\site\editor\boards\index.html"; DestDir: "{app}\mixly\web\site\editor\boards"; Flags: ignoreversion
Source: "C:\Users\Yuxuan\Documents\Codex\2026-10-02\files-pasted-by-the-user-ap\work\native\mixly\web\site\editor\common\main.js"; DestDir: "{app}\mixly\web\site\editor\common"; Flags: ignoreversion
Source: "C:\Users\Yuxuan\Documents\Codex\2026-10-02\files-pasted-by-the-user-ap\work\native\mixly\web\site\editor\boards\default\arduino_esp32\index.xml"; DestDir: "{app}\mixly\web\site\editor\boards\default\arduino_esp32"; Flags: ignoreversion
Source: "C:\Users\Yuxuan\Documents\Codex\2026-10-02\files-pasted-by-the-user-ap\work\native\mixly\web\site\editor\boards\default\arduino_esp32\main.bundle.8e97eb3b.js"; DestDir: "{app}\mixly\web\site\editor\boards\default\arduino_esp32"; Flags: ignoreversion
Source: "C:\Users\Yuxuan\Documents\Codex\2026-10-02\files-pasted-by-the-user-ap\work\native\mixly\web\site\editor\boards\default\arduino_esp32\xml\esp32.xml"; DestDir: "{app}\mixly\web\site\editor\boards\default\arduino_esp32\xml"; Flags: ignoreversion

[Icons]
Name: "{group}\{#AppName}"; Filename: "{app}\AppInventor.exe"; WorkingDir: "{app}"
Name: "{group}\Offline User Guide"; Filename: "{app}\resources\使用说明.txt"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\AppInventor.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\AppInventor.exe"; Description: "Launch Yuxuan Programming Studio"; Flags: nowait postinstall skipifsilent

[Code]
function CheckBaseFile(const Relative, BaseHash, NewHash: String): String;
var Path, Digest: String;
begin
  Result := '';
  Path := AddBackslash(ExpandConstant('{app}')) + Relative;
  if not FileExists(Path) then begin
    Result := '缺少基础文件：' + Relative + '。请安装完整版本或选择正确目录。';
    Exit;
  end;
  try
    Digest := Lowercase(GetSHA256OfFile(Path));
  except
    Result := '无法检查文件：' + Relative + '。请先退出工作台。';
    Exit;
  end;
  if (Digest <> BaseHash) and (Digest <> NewHash) then
    Result := '版本或文件不匹配：' + Relative + '。此增量包只适用于完整的 2.3.0（或修复 2.3.1）。';
end;

function PrepareToInstall(var NeedsRestart: Boolean): String;
begin
  Result := '';
  if not FileExists(ExpandConstant('{app}\unins000.dat')) then begin
    Result := '请先安装羽轩编程工作台 2.3.0，并选择原安装目录。此文件是增量升级包。';
    Exit;
  end;
  Result := CheckBaseFile('AppInventor.exe', '3b91c510a0e7ed4c415c19137a7713652237036d0e12c1eac03d2eed3b5a044e', 'a1ba9f94a9cb92e89d31504ac60db23ed5d9aab7711d6038828e8cc0be847561');
  if Result <> '' then Exit;
  Result := CheckBaseFile('resources\build-version.txt', '42bb5c4420c6d42107baed61e687b7d394f398f6032e41bd04aa07c0c5be8e42', '87955d1974c510d21353d2a303730f1d8997900537c0da5bf32ec2bed041f4cb');
  if Result <> '' then Exit;
  Result := CheckBaseFile('resources\使用说明.txt', '37ca371a9258814dfe8d5846e33382ec0c9169ec193436c9464fce76dcf21d8f', '9c4acc88414bc402675b7d2d7ee2bbb283b2345611e265000a1ee80b7a0842f5');
  if Result <> '' then Exit;
  Result := CheckBaseFile('server\war\ode\aiblockly-0.nocache.js', '58a947677b6670cb57b24ccbb66f1b19d509330ea77d9841851ddcbb670000b7', '71f566a16ed17191b7bbacf400e9817a4f02326c7b8530487d3635d5c30aab8f');
  if Result <> '' then Exit;
  Result := CheckBaseFile('server\war\ode\ode.nocache.js', '50e6254ff9df8a596c83cadb1708e196996190bf8ad430a732dd75142bd94fb5', 'ec9ef624ac103080fc8b5e5f23c8db638b17675c645c5f23f46677e0744f8b57');
  if Result <> '' then Exit;
  Result := CheckBaseFile('server\war\WEB-INF\classes\com\google\appinventor\server\project\youngandroid\YoungAndroidProjectService$1.class', '49cfc3dad0719d965cfdebab1b9ba694da18e984f299671c58eaf15291df35d4', '5cc6b97cf7143f166e341e04365fb5f14d44ac40d816fa6028cb4ac4b0156618');
  if Result <> '' then Exit;
  Result := CheckBaseFile('server\war\WEB-INF\classes\com\google\appinventor\server\project\youngandroid\YoungAndroidProjectService.class', '19b13d7a076d27528eab9cb00b0cc1c5d14274d09d65f2183364bac290518d93', 'b1a748ce6481546c3fcd2515567c198a1e6f8db15b00f324c9630585c7f0ed6e');
  if Result <> '' then Exit;
  Result := CheckBaseFile('resources\distribution-source\Setup.iss', '0b1b665e3a44bae8aa030287f9f4a7d81940241fd86afbe2d14983637a896c66', 'b654dec263b0a426acb51846ebc5a16a3d17c1691abb44506eff675d56cbfebc');
  if Result <> '' then Exit;
  Result := CheckBaseFile('resources\distribution-source\SuiteLauncher.cs', '5b045bb47133a1bff74fa105d82737daaf71b162cae17f90cccd2af7b3bbd7a0', '5b9937b92b2afc318460b50808ab7f31914cba74933c53fe43906499b32310ed');
  if Result <> '' then Exit;
  Result := CheckBaseFile('mixly\web\site\editor\boards\index.html', '9e394c9a3821446105f9892c620aa50affb4f4520ad4467f1f35eed9573ba081', '7ee33c84379e24216ba7c0aac8b5fb52429f51917f5fb71ff3a88df61966502e');
  if Result <> '' then Exit;
  Result := CheckBaseFile('mixly\web\site\editor\common\main.js', '54b0c3b1fb52c7d9933a3f87171d79fd47d5aabc9616818fa0eaf839bb4c0c05', '1d0314a5a5d3655728c62f9efc3032d7a689e8bf074b06fa6bb48ff4a8e08add');
  if Result <> '' then Exit;
  Result := CheckBaseFile('mixly\web\site\editor\boards\default\arduino_esp32\index.xml', '2d5df0fa01b63eba989d33ba0214814c205432b6430f53a85ca02d7383e8098a', 'c4916c435599acf928d1770cb424c55992efd4cca3c98499f9f425cd862d4b3c');
  if Result <> '' then Exit;
  Result := CheckBaseFile('mixly\web\site\editor\boards\default\arduino_esp32\xml\esp32.xml', 'afeb6293a0799bf4a5288109875d479a87e75f4b4dc60c0d55f026b396a22bb7', '37398eb533aff8a01dc88641cefe7af4e0e7735e35ef9d19e41a6b0530a4f9b7');
  if Result <> '' then Exit;
  Result := CheckBaseFile('AppInventorCore.exe', 'cf8b3b25fd29c5c3f1c4da3d40d7cbb552e8fe89f44b9a9e95477aae1ee909e5', 'cf8b3b25fd29c5c3f1c4da3d40d7cbb552e8fe89f44b9a9e95477aae1ee909e5');
  if Result <> '' then Exit;
  Result := CheckBaseFile('runtime\python3.13.16\python.exe', '31fe10b4ed82a2f960af0ef9931f46a4b84ff286f8b6ffd9dee098cf4f10f17f', '31fe10b4ed82a2f960af0ef9931f46a4b84ff286f8b6ffd9dee098cf4f10f17f');
  if Result <> '' then Exit;
  Result := CheckBaseFile('mixly\web\server.py', 'fd33e04444809e63f5c4bfea022acb0a31be852fed0f0aa7445407a958544c3c', 'fd33e04444809e63f5c4bfea022acb0a31be852fed0f0aa7445407a958544c3c');
  if Result <> '' then Exit;
end;
