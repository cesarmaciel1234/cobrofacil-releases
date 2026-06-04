import os
import zipfile
import json

BASE = os.path.dirname(os.path.abspath(__file__))

EXCLUIR = {
    '.venv', '__pycache__', '.git', 'build', 'dist',
    'backups', 'scratch', 'logs', 'reportes',
    'Etiquetas_Impresas', 'Folletos_Oferta', 'Carteles_Oferta',
    'ofertas_pdf', 'data', 'docs', 'ia planificacion',
    'utilidades_hardware', 'Instalador_Final', 'temp_restore',
    'src_backup', 'launcher_installer', 'chatbot', 'CATORTA_USB_PUNPRO', 'certificados'
}
EXCLUIR_EXT = {'.db', '.log', '.pyc', '.spec', '.zip', '.bat',
               '.iss', '.pdf', '.png', '.jpg', '.ico', '.exe',
               '.ps1', '.ini', '.json'}
INCLUIR_JSON = {'version.json'}

# Leer version
with open(os.path.join(BASE, 'version.json'), 'r', encoding='utf-8') as f:
    manifest = json.load(f)
version = manifest.get("app_version", "2026.3.3")

zip_filename = f"CobroFacil_POS_v{version}.zip"
zip_path = os.path.join(BASE, zip_filename)

if os.path.exists(zip_path):
    os.remove(zip_path)

print(f"Creando paquete de actualización {zip_filename}...")

count = 0
with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zip_file:
    for root, dirs, files in os.walk(BASE):
        # Filtrar carpetas excluidas
        dirs[:] = [d for d in dirs if d not in EXCLUIR and not d.startswith('.')]
        for fname in files:
            ext = os.path.splitext(fname)[1].lower()
            if "mariadb_server" in root:
                # Permitir todo en mariadb_server excepto basura obvia
                if ext in {'.log', '.pyc', '.zip'}:
                    continue
            else:
                if ext in EXCLUIR_EXT and fname not in INCLUIR_JSON:
                    continue
                if fname.endswith('.json') and fname not in INCLUIR_JSON:
                    continue
            full = os.path.join(root, fname)
            rel = os.path.relpath(full, BASE)
            zip_file.write(full, rel)
            count += 1

print(f"¡Éxito! Se ha creado el paquete {zip_filename} con {count} archivos.")
