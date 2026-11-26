; Crescent Islamic High School - Seat Management System Installer
; Target OS: Windows 10/11 64-bit

#define MyAppName "Crescent Islamic High School - Seat Management"
#define MyAppShortName "Crescent Islamic High School"
#define MyAppVersion "2.1.0"
#define MyAppPublisher "Crescent Islamic High School"
#define MyAppURL "http://127.0.0.1:5000"
#define MyAppExeName "CrescentIslamicHighSchool.exe"

[Setup]
AppId={{C8E19B1A-5477-4D6F-9C8E-7863A71A1234}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} v{#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppShortName}
UninstallDisplayIcon={app}\{#MyAppExeName}
DefaultGroupName={#MyAppShortName}
AllowNoIcons=yes
OutputDir=installer_output
OutputBaseFilename=Crescent_Islamic_High_School_Setup
SetupIconFile=app_icon.ico
SolidCompression=yes
Compression=lzma2/ultra64
WizardStyle=modern
PrivilegesRequiredOverridesAllowed=dialog
ArchitecturesInstallIn64BitMode=x64compatible
DisableProgramGroupPage=auto
CloseApplications=force

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[Files]
Source: "dist\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion
Source: "app_icon.ico"; DestDir: "{app}"; Flags: ignoreversion
Source: "consoliataed sheet PA 2.xlsx"; DestDir: "{app}"; Flags: ignoreversion
Source: "PA2_Seating_Simple.xlsx"; DestDir: "{app}"; Flags: ignoreversion
Source: "uploads\Dynamic_Report.xlsx"; DestDir: "{app}"; Flags: ignoreversion; DestName: "Dynamic_Report_Sample.xlsx"

[Icons]
Name: "{group}\{#MyAppShortName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\app_icon.ico"
Name: "{group}\{cm:UninstallProgram,{#MyAppShortName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppShortName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon; IconFilename: "{app}\app_icon.ico"

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppShortName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent
