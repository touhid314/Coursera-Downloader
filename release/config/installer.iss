#define AppName "Coursera Full Course Downloader"
#define AppVersion "4.0.0"
#define AppPublisher "Touhidul Islam"
#define AppExeName "CourseraDownloader.exe"

[Setup]
; Paths are relative to release\config\.
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#AppPublisher}
DefaultDirName={autopf}\Touhidul Islam\Coursera Full Course Downloader
DefaultGroupName=Coursera Full Course Downloader
OutputDir=..\artifacts\installers
OutputBaseFilename=CourseraDownloaderInstallerV{#AppVersion}
Compression=lzma
SolidCompression=yes
PrivilegesRequired=admin
AllowNoIcons=yes
DisableProgramGroupPage=yes
SetupIconFile="..\..\assets\icon\icon.ico"
Uninstallable=yes
CloseApplications=yes
CloseApplicationsFilter={#AppExeName}

[Files]
Source: "..\artifacts\app\CourseraDownloader\*"; \
    DestDir: "{app}"; Flags: recursesubdirs createallsubdirs ignoreversion overwritereadonly

[Icons]
Name: "{group}\{#AppName}"; Filename: "{app}\{#AppExeName}"; WorkingDir: "{app}"
Name: "{commondesktop}\{#AppName}"; Filename: "{app}\{#AppExeName}"; \
    WorkingDir: "{app}"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop icon"; GroupDescription: "Additional icons:"

[Registry]
Root: "HKCU"; Subkey: "SOFTWARE\Microsoft\Windows NT\CurrentVersion\AppCompatFlags\Layers"; \
    ValueType: string; ValueName: "{app}\{#AppExeName}"; ValueData: "RUNASADMIN"; Flags: uninsdeletevalue

[UninstallDelete]
Type: dirifempty; Name: "{app}"
