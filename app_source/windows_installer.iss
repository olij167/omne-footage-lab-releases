#define MyAppName "OmN-e Retrospector"
#ifndef MyAppVersion
#define MyAppVersion "0.4.0"
#endif
#ifndef MyAppArch
#define MyAppArch "x64"
#endif
#define MyAppPublisher "OmN-e / Pungent Funk"
#define MyAppURL "https://omne.space/"
#define MyAppExeName "OmN-e Retrospector.exe"

[Setup]
AppId={{D4423B8B-E250-4B30-B516-0DDBFCF09DA0}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL=https://omne.space/support
DefaultDirName={localappdata}\Programs\OmN-e Retrospector
DefaultGroupName=OmN-e Retrospector
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
OutputDir=dist-installer
OutputBaseFilename=OmN-e_Retrospector_v{#MyAppVersion}_Windows_{#MyAppArch}_Setup
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
UninstallDisplayIcon={app}\{#MyAppExeName}
VersionInfoVersion={#MyAppVersion}.0
VersionInfoCompany={#MyAppPublisher}
VersionInfoDescription={#MyAppName}
VersionInfoProductName={#MyAppName}
VersionInfoProductVersion={#MyAppVersion}

#if MyAppArch == "x64"
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
#endif

[Files]
Source: "dist\OmN-e Retrospector\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\OmN-e Retrospector"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\OmN-e Retrospector"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop shortcut"; GroupDescription: "Additional icons:"; Flags: unchecked

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Launch OmN-e Retrospector"; Flags: nowait postinstall skipifsilent

[InstallDelete]
Type: files; Name: "{app}\OmN-e Footage Lab.exe"
Type: files; Name: "{autoprograms}\OmN-e Footage Lab.lnk"
Type: files; Name: "{autodesktop}\OmN-e Footage Lab.lnk"
