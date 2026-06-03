import json
import os
import hashlib

base_dir = os.path.dirname(os.path.abspath(__file__))
version_file = os.path.join(base_dir, 'version.json')

try:
    if os.path.getsize(version_file) == 0:
        raise ValueError("Archivo vacío")
    with open(version_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
        # Forzar URL siempre
        data["download_url"] = "https://firebasestorage.googleapis.com/v0/b/cajafacil-pro-updates.firebasestorage.app/o/CobroFacil_POS_v3010.0.zip?alt=media&token=28b880d8-5cc1-4813-8ec5-f83c05c96e31"
except:
    data = {
        "app_version": "3010.0",
        "latest_version": "3010.0",
        "download_url": "https://firebasestorage.googleapis.com/v0/b/cajafacil-pro-updates.firebasestorage.app/o/CobroFacil_POS_v3010.0.zip?alt=media&token=28b880d8-5cc1-4813-8ec5-f83c05c96e31",
        "channel": "stable",
        "build_date": "2026-06-01 19:34:27",
        "modules": {}
    }

EXCLUIR = {
    '.venv', '__pycache__', '.git', 'build', 'dist',
    'backups', 'scratch', 'logs', 'reportes',
    'Etiquetas_Impresas', 'Folletos_Oferta', 'Carteles_Oferta',
    'ofertas_pdf', 'data', 'docs', 'ia planificacion',
    'utilidades_hardware', 'Instalador_Final', 'temp_restore',
    'src_backup', 'launcher_installer', 'tests_e2e', 'CATORTA_USB_PUNPRO', 'certificados'
}

EXCLUIR_EXT = {'.db', '.log', '.pyc', '.spec', '.zip', '.bat',
               '.iss', '.pdf', '.png', '.jpg', '.ico', '.exe',
               '.ps1', '.ini', '.json'}
INCLUIR_JSON = {'version.json'}

new_modules = {}
for root, dirs, files in os.walk(base_dir):
    dirs[:] = [d for d in dirs if d not in EXCLUIR and not d.startswith('.')]
    for fname in files:
        ext = os.path.splitext(fname)[1].lower()
        if ext in EXCLUIR_EXT and fname not in INCLUIR_JSON:
            continue
        if fname.endswith('.json') and fname not in INCLUIR_JSON:
            continue
            
        file_path = os.path.join(root, fname)
        rel_path = os.path.relpath(file_path, base_dir).replace("\\", "/")
        
        # Omitir archivos innecesarios en el root
        if rel_path in ["get-pip.py", "old_admin.py", "test_error.py", "stress_test.py", "generar_version.py", "run_pyinstaller.py", "detect_ports.py", "clean_excel.py"]:
            continue
            
        with open(file_path, 'rb') as f:
            content = f.read()
            checksum = hashlib.md5(content).hexdigest()
            size = len(content)
            
        new_modules[rel_path] = {
            "version": "1.0.0",
            "checksum": checksum,
            "channel": "stable",
            "size": size
        }

data['modules'] = new_modules

with open(version_file, 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2)

print(f"version.json limpiado y actualizado correctamente con {len(new_modules)} módulos.")
