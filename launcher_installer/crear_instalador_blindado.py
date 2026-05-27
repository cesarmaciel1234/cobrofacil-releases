import os
import sys
import subprocess
import shutil

# Rutas
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ZIP_PATH = os.path.join(BASE_DIR, "CATORTA_USB_PUNPRO", "2_Archivos_Comprimidos_ZIP", "Batallon_TPV_Win8_Win11.zip")
INSTALLER_SCRIPT = os.path.join(BASE_DIR, "launcher_installer", "web_installer.py")
DIST_DIR = os.path.join(BASE_DIR, "launcher_installer", "dist")

def blindar_instalador():
    print("==========================================================")
    print("--- COMPILADOR BLINDADO ANTI-PIRATERIA (PAYLOAD OCULTO) ---")
    print("==========================================================")
    
    if not os.path.exists(ZIP_PATH):
        print(f"ERROR: No se encontro el paquete maestro: {ZIP_PATH}")
        print("Asegurate de ejecutar primero 'empaquetar_batallon.bat'")
        return

    # Aquí podríamos añadir ofuscación (ej: XOR bit a bit). 
    # Por ahora confiaremos en que PyInstaller lo empaca dentro del binario
    # y nuestro web_installer.py intentará extraerlo en memoria con la contraseña.
    
    print("Empaquetando Setup.exe con el ZIP embebido internamente...")
    print("Esto puede demorar unos minutos por el tamaño del ZIP.")
    
    cmd = [
        "pyinstaller",
        "--noconfirm",
        "--onefile",
        "--windowed",
        "--name", "Instalar_CajaFacil_Pro_Blindado",
        "--hidden-import", "win32com",
        "--hidden-import", "win32com.client",
        "--icon=NONE",
        f"--add-data={ZIP_PATH};.", # <-- MAGIA AQUI: Mete el ZIP entero DENTRO del exe
        INSTALLER_SCRIPT
    ]
    
    # Ejecutamos Pyinstaller desde la carpeta launcher_installer para no ensuciar root
    launcher_dir = os.path.join(BASE_DIR, "launcher_installer")
    subprocess.run(cmd, cwd=launcher_dir)
    
    print("\nCOMPILACION BLINDADA TERMINADA.")
    print("El archivo resultante contiene toda la aplicacion oculta y encriptada.")
    print(f"Ruta: {os.path.join(DIST_DIR, 'Instalar_CajaFacil_Pro_Blindado.exe')}")

if __name__ == "__main__":
    blindar_instalador()
