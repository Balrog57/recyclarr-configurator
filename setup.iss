#ifndef MyAppVersion
#define MyAppVersion "2.2.0"
#endif

[Setup]
AppName=Recyclarr Configurator
AppVersion={#MyAppVersion}
AppPublisher=Antigravity
DefaultDirName={autopf}\RecyclarrConfigurator
DefaultGroupName=Recyclarr Configurator
OutputDir=Output
OutputBaseFilename=RecyclarrConfigurator_Setup_{#MyAppVersion}
Compression=lzma
SolidCompression=yes
PrivilegesRequired=lowest
ArchitecturesInstallIn64BitMode=x64

[Files]
Source: "dist\RecyclarrConfigurator\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\Recyclarr Configurator"; Filename: "{app}\RecyclarrConfigurator.exe"
Name: "{group}\Uninstall Recyclarr Configurator"; Filename: "{uninstallexe}"
