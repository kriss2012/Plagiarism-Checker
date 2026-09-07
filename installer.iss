; Inno Setup Script for ResearchGuard - Research Paper Plagiarism Checker
; Generates ResearchGuard_Setup.exe

#define MyAppName "ResearchGuard"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "Academic Systems"
#define MyAppURL "https://researchguard.local"
#define MyAppExeName "ResearchGuard.exe"

[Setup]
AppId={{D3F87B42-4A93-49F1-92D0-128BFA91845B}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DisableProgramGroupPage=yes
OutputBaseFilename=ResearchGuard_Setup
SetupIconFile=resources\app_icon.ico
Compression=lzma
SolidCompression=yes
WizardStyle=modern
ArchitecturesInstallIn64BitMode=x64compatible

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "dist\ResearchGuard\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion
Source: "dist\ResearchGuard\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent
