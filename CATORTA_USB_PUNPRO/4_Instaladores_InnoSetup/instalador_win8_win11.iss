[Setup]
; Identidad Corporativa de la Aplicación
AppName=CajaFacil Pro Elite
AppVersion=1.0.0
AppPublisher=PunPro Software Systems
DefaultDirName={pf}\CajaFacil Pro
DefaultGroupName=CajaFacil Pro
OutputDir=.\Instalador_Final
OutputBaseFilename=Instalar_CajaFacil_Pro_Win8_Win11
Compression=lzma2/ultra64
SolidCompression=yes
; Configurado para núcleos modernos (Windows 8, 10 y 11)
MinVersion=6.2

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; 1. Desplegar el árbol binario compilado de última generación
Source: "dist\CajaFacil_Pro_Portable_Win8_Win11\bin\*"; DestDir: "{app}\bin"; Flags: ignoreversion recursesubdirs createallsubdirs
; 2. Inyectar plantillas base operativas
Source: "dist\CajaFacil_Pro_Portable_Win8_Win11\punpro.db"; DestDir: "{app}"; Flags: ignoreversion skipifsourcedoesntexist
Source: "dist\CajaFacil_Pro_Portable_Win8_Win11\config.json"; DestDir: "{app}"; Flags: ignoreversion skipifsourcedoesntexist

[Icons]
Name: "{group}\CajaFacil Pro"; Filename: "{app}\bin\CajaFacil_Pro.exe"
Name: "{commondesktop}\CajaFacil Pro"; Filename: "{app}\bin\CajaFacil_Pro.exe"; Tasks: desktopicon

[Dirs]
; Blindaje de permisos para acceso concurrente de base de datos en UAC moderno
Name: "{app}"; Permissions: everyone-modify

[Run]
Filename: "{app}\bin\CajaFacil_Pro.exe"; Description: "{cm:LaunchProgram,CajaFacil Pro}"; Flags: nowait postinstall skipifsilent
