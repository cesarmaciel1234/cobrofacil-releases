[Setup]
; Identidad Corporativa de la Aplicación
AppName=Cobro Fácil POS Elite
AppVersion=1.0.0
AppPublisher=PunPro Software Systems
DefaultDirName={pf}\Cobro Fácil POS
DefaultGroupName=Cobro Fácil POS
OutputDir=.\Instalador_Final
OutputBaseFilename=Instalar_CobroFacil_POS_Win8_Win11
Compression=lzma2/ultra64
SolidCompression=yes
; Configurado para núcleos modernos (Windows 8, 10 y 11)
MinVersion=6.2

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; 1. Desplegar el árbol binario compilado de última generación
Source: "dist\CobroFacil_POS_Portable_Win8_Win11\bin\*"; DestDir: "{app}\bin"; Flags: ignoreversion recursesubdirs createallsubdirs
; 2. Inyectar plantillas base operativas
Source: "dist\CobroFacil_POS_Portable_Win8_Win11\punpro.db"; DestDir: "{app}"; Flags: ignoreversion skipifsourcedoesntexist
Source: "dist\CobroFacil_POS_Portable_Win8_Win11\config.json"; DestDir: "{app}"; Flags: ignoreversion skipifsourcedoesntexist

[Icons]
Name: "{group}\Cobro Fácil POS"; Filename: "{app}\bin\CobroFacil_POS.exe"
Name: "{commondesktop}\Cobro Fácil POS"; Filename: "{app}\bin\CobroFacil_POS.exe"; Tasks: desktopicon

[Dirs]
; Blindaje de permisos para acceso concurrente de base de datos en UAC moderno
Name: "{app}"; Permissions: everyone-modify

[Run]
Filename: "{app}\bin\CobroFacil_POS.exe"; Description: "{cm:LaunchProgram,Cobro Fácil POS}"; Flags: nowait postinstall skipifsilent
