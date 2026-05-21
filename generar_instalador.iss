[Setup]
; Nombre y detalles de tu aplicación
AppName=CajaFacil Pro
AppVersion=1.0
AppPublisher=PunPro
DefaultDirName={pf}\CajaFacil Pro
DefaultGroupName=CajaFacil Pro
OutputDir=.\Instalador_Final
OutputBaseFilename=Instalar_PunPro_Elite
Compression=lzma
SolidCompression=yes
; Permitir que funcione correctamente en Windows 7 a 11
MinVersion=6.1

[Tasks]
; Casilla para crear icono en el escritorio
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; Capturar todo el contenido binario del batallón moderno
Source: "dist\CajaFacil_Pro_Portable_Win8_Win11\bin\*"; DestDir: "{app}\bin"; Flags: ignoreversion recursesubdirs createallsubdirs
; Inyectar plantillas base operativas
Source: "dist\CajaFacil_Pro_Portable_Win8_Win11\punpro.db"; DestDir: "{app}"; Flags: ignoreversion skipifsourcedoesntexist
Source: "dist\CajaFacil_Pro_Portable_Win8_Win11\config.json"; DestDir: "{app}"; Flags: ignoreversion skipifsourcedoesntexist

[Icons]
; Crear acceso directo en el Menú de Inicio apuntando al binario interno
Name: "{group}\CajaFacil Pro"; Filename: "{app}\bin\CajaFacil_Pro.exe"
; Crear acceso directo en el Escritorio
Name: "{commondesktop}\CajaFacil Pro"; Filename: "{app}\bin\CajaFacil_Pro.exe"; Tasks: desktopicon

[Dirs]
; Permisos de lectura/escritura absolutos para evitar bloqueos de base de datos
Name: "{app}"; Permissions: everyone-modify

[Run]
; Casilla para iniciar el programa al terminar la instalación
Filename: "{app}\bin\CajaFacil_Pro.exe"; Description: "{cm:LaunchProgram,CajaFacil Pro}"; Flags: nowait postinstall skipifsilent
