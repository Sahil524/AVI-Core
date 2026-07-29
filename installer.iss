; ============================================================
; INNO SETUP CONFIGURATION FOR AVI CORE
; ============================================================

[Setup]
AppName=AVI Core
AppVersion=2.0.0
DefaultDirName={commonpf}\AVI Core
DefaultGroupName=AVI Core
UninstallDisplayIcon={app}\logo.ico
Compression=lzma2
SolidCompression=yes
OutputDir=dist
OutputBaseFilename=AVI-Core-Setup-v2.0.0
ArchitecturesInstallIn64BitMode=x64compatible
PrivilegesRequired=admin
DisableWelcomePage=no
DisableDirPage=no
DisableProgramGroupPage=yes
CloseApplications=yes
AppMutex=Global\AvicoreProcessingMutex
SetupIconFile=logo.ico

[Dirs]
Name: "{localappdata}\AVICore\logs"
Name: "{localappdata}\AVICore\runtime"

[Files]
Source: "logo.ico"; DestDir: "{app}"; Flags: ignoreversion
Source: "dist\context_menu.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "dist\avicore\*"; DestDir: "{app}\avicore"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\AVI Core"; Filename: "{app}\avicore\avicore.exe"; Parameters: "--help"; IconFilename: "{app}\logo.ico"
Name: "{group}\Uninstall AVI Core"; Filename: "{uninstallexe}"; IconFilename: "{app}\logo.ico"

[Registry]
; ============================================================
; PERCEIVED TYPE KEYS — set as a baseline so Windows knows the
; media category for each extension. The actual context menu
; shell entries are registered by context_menu.exe in [Run].
; ============================================================

; Image perceived types
Root: HKLM; Subkey: "SOFTWARE\Classes\.jpg";  ValueType: string; ValueName: "PerceivedType"; ValueData: "image"
Root: HKLM; Subkey: "SOFTWARE\Classes\.jpeg"; ValueType: string; ValueName: "PerceivedType"; ValueData: "image"
Root: HKLM; Subkey: "SOFTWARE\Classes\.png";  ValueType: string; ValueName: "PerceivedType"; ValueData: "image"
Root: HKLM; Subkey: "SOFTWARE\Classes\.webp"; ValueType: string; ValueName: "PerceivedType"; ValueData: "image"
Root: HKLM; Subkey: "SOFTWARE\Classes\.bmp";  ValueType: string; ValueName: "PerceivedType"; ValueData: "image"

; Video perceived types
Root: HKLM; Subkey: "SOFTWARE\Classes\.mp4";  ValueType: string; ValueName: "PerceivedType"; ValueData: "video"
Root: HKLM; Subkey: "SOFTWARE\Classes\.mkv";  ValueType: string; ValueName: "PerceivedType"; ValueData: "video"
Root: HKLM; Subkey: "SOFTWARE\Classes\.mov";  ValueType: string; ValueName: "PerceivedType"; ValueData: "video"
Root: HKLM; Subkey: "SOFTWARE\Classes\.avi";  ValueType: string; ValueName: "PerceivedType"; ValueData: "video"
Root: HKLM; Subkey: "SOFTWARE\Classes\.webm"; ValueType: string; ValueName: "PerceivedType"; ValueData: "video"
Root: HKLM; Subkey: "SOFTWARE\Classes\.m4v";  ValueType: string; ValueName: "PerceivedType"; ValueData: "video"
Root: HKLM; Subkey: "SOFTWARE\Classes\.flv";  ValueType: string; ValueName: "PerceivedType"; ValueData: "video"
Root: HKLM; Subkey: "SOFTWARE\Classes\.ts";   ValueType: string; ValueName: "PerceivedType"; ValueData: "video"

; Audio perceived types
Root: HKLM; Subkey: "SOFTWARE\Classes\.mp3";  ValueType: string; ValueName: "PerceivedType"; ValueData: "audio"
Root: HKLM; Subkey: "SOFTWARE\Classes\.wav";  ValueType: string; ValueName: "PerceivedType"; ValueData: "audio"
Root: HKLM; Subkey: "SOFTWARE\Classes\.aac";  ValueType: string; ValueName: "PerceivedType"; ValueData: "audio"
Root: HKLM; Subkey: "SOFTWARE\Classes\.flac"; ValueType: string; ValueName: "PerceivedType"; ValueData: "audio"
Root: HKLM; Subkey: "SOFTWARE\Classes\.ogg";  ValueType: string; ValueName: "PerceivedType"; ValueData: "audio"
Root: HKLM; Subkey: "SOFTWARE\Classes\.m4a";  ValueType: string; ValueName: "PerceivedType"; ValueData: "audio"

[Run]
; Register per-extension context menu entries after install.
Filename: "{app}\context_menu.exe"; Parameters: "register"; Flags: runhidden waituntilterminated; StatusMsg: "Registering AVI Core context menu..."

[UninstallRun]
; Clean up all per-extension registry entries on uninstall
Filename: "{app}\context_menu.exe"; Parameters: "unregister"; Flags: runhidden waituntilterminated

[UninstallDelete]
Type: filesandordirs; Name: "{localappdata}\AVICore"

[Code]
const
  SHCNE_ASSOCCHANGED = $08000000;
  SHCNF_IDLIST = $0000;

procedure SHChangeNotify(wEventId: Integer; uFlags: Cardinal; dwItem1, dwItem2: Integer);
  external 'SHChangeNotify@shell32.dll stdcall';

procedure RefreshExplorerShell;
begin
  try
    SHChangeNotify(SHCNE_ASSOCCHANGED, SHCNF_IDLIST, 0, 0);
  except
    // Silent catch to prevent installation block
  end;
end;

procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then
  begin
    RefreshExplorerShell;
  end;
end;

procedure CurUninstallStepChanged(JustAfterAnUninstallStep: TUninstallStep);
begin
  if JustAfterAnUninstallStep = usPostUninstall then
  begin
    RefreshExplorerShell;
  end;
end;
