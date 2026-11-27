; Inno Setup 6 Script for SolarPulse ERP (7-Day Demo Evaluation)
; Produces a modern, professional Windows Setup Wizard with custom icons and shortcuts.

#define MyAppName "SolarPulse ERP"
#define MyAppVersion "2.0"
#define MyAppPublisher "SuryaTech Clean Energy Solutions"
#define MyAppURL "https://www.suryatechenergy.com"
#define MyAppExeName "SolarPulse_ERP.exe"

[Setup]
AppId={{5E4B2819-B129-4A7B-9E38-C1827A9F42A1}
AppName={#MyAppName} (7-Day Demo)
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\SolarPulse ERP
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
LicenseFile=trial_license_agreement.txt
OutputDir=dist_installer
OutputBaseFilename=SolarPulse_ERP_Setup_7Day_Demo
SetupIconFile=app_icon.ico
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
ArchitecturesInstallIn64BitMode=x64
UninstallDisplayIcon={app}\app_icon.ico
VersionInfoVersion=2.0.0.0
VersionInfoCompany=SuryaTech Clean Energy Solutions
VersionInfoDescription=SolarPulse ERP - 7-Day Demo Setup
VersionInfoProductTextVersion=2.0 Demo

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[Files]
Source: "dist\SolarPulse_ERP\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "app_icon.ico"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MyAppName} Demo"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\app_icon.ico"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName} Demo"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon; IconFilename: "{app}\app_icon.ico"

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}} (7-Day Demo)"; Flags: nowait postinstall
