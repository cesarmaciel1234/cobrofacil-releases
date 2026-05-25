[Setup]
; Identidad Corporativa de la Aplicación
AppName=CajaFacil Pro Elite
AppVersion=1.0.0
AppPublisher=PunPro Software Systems
DefaultDirName={pf}\CajaFacil Pro
DefaultGroupName=CajaFacil Pro
OutputDir=.\Instalador_Final
OutputBaseFilename=Instalar_CajaFacil_Pro_Win7
Compression=lzma2/ultra64
SolidCompression=yes
; Habilitar compatibilidad estricta con kernel heredado (Windows 7 SP1 en adelante)
MinVersion=6.1

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; 1. Desplegar todo el árbol binario nativo en la subcarpeta de aislamiento bin/
Source: "dist\CajaFacil_Pro_Portable_Win7\bin\*"; DestDir: "{app}\bin"; Flags: ignoreversion recursesubdirs createallsubdirs
; 2. Inyectar plantillas de datos iniciales en la raíz de la instalación
Source: "dist\CajaFacil_Pro_Portable_Win7\punpro.db"; DestDir: "{app}"; Flags: ignoreversion skipifsourcedoesntexist
Source: "dist\CajaFacil_Pro_Portable_Win7\config.json"; DestDir: "{app}"; Flags: ignoreversion skipifsourcedoesntexist

[Icons]
; Crear accesos directos unificados apuntando al binario interno
Name: "{group}\CajaFacil Pro"; Filename: "{app}\bin\CajaFacil_Pro.exe"
Name: "{commondesktop}\CajaFacil Pro"; Filename: "{app}\bin\CajaFacil_Pro.exe"; Tasks: desktopicon

[Dirs]
; Garantizar que la base de datos tenga permisos de lectura y escritura para los cajeros
Name: "{app}"; Permissions: everyone-modify

[Run]
Filename: "{app}\bin\CajaFacil_Pro.exe"; Description: "{cm:LaunchProgram,CajaFacil Pro}"; Flags: nowait postinstall skipifsilent
