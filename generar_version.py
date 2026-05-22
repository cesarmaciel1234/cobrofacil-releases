"""
Regenera version.json con los checksums actuales de todos los archivos del proyecto.
Ejecutar desde la raiz del proyecto antes de publicar una actualizacion.
"""
import os
import json
import hashlib
from datetime import datetime

BASE = os.path.dirname(os.path.abspath(__file__))

EXCLUIR = {
    '.venv', '__pycache__', '.git', 'build', 'dist',
    'backups', 'scratch', 'logs', 'reportes',
    'Etiquetas_Impresas', 'Folletos_Oferta', 'Carteles_Oferta',
    'ofertas_pdf', 'data', 'docs', 'ia planificacion',
    'utilidades_hardware', 'Instalador_Final',
}
EXCLUIR_EXT = {'.db', '.log', '.pyc', '.spec', '.zip', '.bat',
               '.iss', '.pdf', '.png', '.jpg', '.ico', '.exe',
               '.ps1', '.ini', '.json'}
INCLUIR_JSON = {'version.json', 'config.json'}  # estos sí se incluyen

def md5(filepath):
    h = hashlib.md5()
    with open(filepath, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            h.update(chunk)
    return h.hexdigest()

def recopilar_modulos():
    modulos = {}
    for root, dirs, files in os.walk(BASE):
        # Filtrar carpetas excluidas
        dirs[:] = [d for d in dirs if d not in EXCLUIR and not d.startswith('.')]
        for fname in files:
            ext = os.path.splitext(fname)[1].lower()
            if ext in EXCLUIR_EXT and fname not in INCLUIR_JSON:
                continue
            if fname.endswith('.json') and fname not in INCLUIR_JSON:
                continue
            full = os.path.join(root, fname)
            rel = os.path.relpath(full, BASE).replace('\\', '/')
            modulos[rel] = {
                "version": "2026.3.0",
                "checksum": md5(full),
                "channel": "stable"
            }
    return modulos

if __name__ == '__main__':
    print("Generando version.json actualizado...")
    modulos = recopilar_modulos()

    manifest = {
        "app_version": "2026.3.0",
        "channel": "stable",
        "build_date": datetime.now().strftime("%Y-%m-%d"),
        "modules": modulos
    }

    out = os.path.join(BASE, 'version.json')
    with open(out, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)

    print(f"OK: version.json generado con {len(modulos)} modulos")
    print(f"   Version: 2026.2.0")
    print(f"   Fecha: {manifest['build_date']}")
