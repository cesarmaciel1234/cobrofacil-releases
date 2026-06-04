import os
import sys
import subprocess
import shutil

# Rutas
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ZIP_PATH = os.path.join(BASE_DIR, "CATORTA_USB_PUNPRO", "2_Archivos_Comprimidos_ZIP", "Batallon_TPV_Win8_Win11.zip")
INSTALLER_SCRIPT = os.path.join(BASE_DIR, "launcher_installer", "web_installer.py")
DIST_DIR = os.path.join(BASE_DIR, "launcher_installer", "dist")
PAYLOAD_BIN = os.path.join(BASE_DIR, "launcher_installer", "payload.bin")

def encrypt_file(input_file, output_file, key):
    """Encriptación XOR simple para ocultar la firma del archivo"""
    print(f"Encriptando payload: {input_file} -> {output_file}")
    with open(input_file, "rb") as f_in, open(output_file, "wb") as f_out:
        key_bytes = key.encode('utf-8')
        key_len = len(key_bytes)
        
        while True:
            chunk = f_in.read(1024 * 1024) # Leer en chunks de 1MB
            if not chunk:
                break
            # XOR cada byte con la clave repetida
            encrypted_chunk = bytearray(
                b ^ key_bytes[i % key_len] for i, b in enumerate(chunk)
            )
            f_out.write(encrypted_chunk)

def blindar_instalador():
    print("==========================================================")
    print("--- COMPILADOR BLINDADO ANTI-PIRATERIA (PAYLOAD OCULTO) ---")
    print("==========================================================")
    
    if not os.path.exists(ZIP_PATH):
        print(f"ERROR: No se encontro el paquete maestro: {ZIP_PATH}")
        print("Asegurate de ejecutar primero 'empaquetar_batallon.bat'")
        return

    # 1. Encriptar el ZIP original a payload.bin
    encryption_key = "PUNPRO2026_BLINDAJE_ULTIMATE"
    encrypt_file(ZIP_PATH, PAYLOAD_BIN, encryption_key)
    
    print("Empaquetando Setup.exe con el binario encriptado...")
    print("Esto puede demorar unos minutos por el tamaño del archivo.")
    
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm",
        "--onefile",
        "--windowed",
        "--name", "Instalar_CobroFacil_POS_Blindado",
        "--hidden-import", "win32com",
        "--hidden-import", "win32com.client",
        "--icon=NONE",
        f"--add-data={PAYLOAD_BIN};.", # <-- Empaquetar el BINARIO CIFRADO, no el ZIP
        INSTALLER_SCRIPT
    ]
    
    # Ejecutamos Pyinstaller desde la carpeta launcher_installer
    launcher_dir = os.path.join(BASE_DIR, "launcher_installer")
    subprocess.run(cmd, cwd=launcher_dir)
    
    # Limpiar el payload temporal
    if os.path.exists(PAYLOAD_BIN):
        os.remove(PAYLOAD_BIN)
    
    print("\nCOMPILACION BLINDADA TERMINADA.")
    print("El archivo resultante contiene toda la aplicacion cifrada con XOR.")
    print(f"Ruta: {os.path.join(DIST_DIR, 'Instalar_CobroFacil_POS_Blindado.exe')}")

if __name__ == "__main__":
    blindar_instalador()
