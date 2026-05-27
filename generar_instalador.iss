[Setup]
; Nombre y detalles de tu aplicación
AppName=Cobro Fácil POS
AppVersion=1.0
AppPublisher=PunPro
DefaultDirName={pf}\Cobro Fácil POS
DefaultGroupName=Cobro Fácil POS
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
Source: "dist\CobroFacil_POS_Portable_Win8_Win11\bin\*"; DestDir: "{app}\bin"; Flags: ignoreversion recursesubdirs createallsubdirs
; Inyectar plantillas base operativas
Source: "dist\CobroFacil_POS_Portable_Win8_Win11\punpro.db"; DestDir: "{app}"; Flags: ignoreversion skipifsourcedoesntexist
Source: "dist\CobroFacil_POS_Portable_Win8_Win11\config.json"; DestDir: "{app}"; Flags: ignoreversion skipifsourcedoesntexist

[Icons]
; Crear acceso directo en el Menú de Inicio apuntando al binario interno
Name: "{group}\Cobro Fácil POS"; Filename: "{app}\bin\CobroFacil_POS.exe"
; Crear acceso directo en el Escritorio
Name: "{commondesktop}\Cobro Fácil POS"; Filename: "{app}\bin\CobroFacil_POS.exe"; Tasks: desktopicon

[Dirs]
; Permisos de lectura/escritura absolutos para evitar bloqueos de base de datos
Name: "{app}"; Permissions: everyone-modify

[Run]
; Casilla para iniciar el programa al terminar la instalación
Filename: "{app}\bin\CobroFacil_POS.exe"; Description: "{cm:LaunchProgram,Cobro Fácil POS}"; Flags: nowait postinstall skipifsilent
