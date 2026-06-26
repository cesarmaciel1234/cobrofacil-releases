"""Regenera version.json en la raíz del repo (checksums + app_version)."""

import argparse
import hashlib
import json
import os
from datetime import datetime

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VERSION_FILE = os.path.join(REPO_ROOT, "version.json")

EXCLUIR = {
    ".venv", "__pycache__", ".git", "build", "dist",
    "backups", "scratch", "logs", "reportes",
    "Etiquetas_Impresas", "Folletos_Oferta", "Carteles_Oferta",
    "ofertas_pdf", "data", "docs", "ia planificacion",
    "utilidades_hardware", "Instalador_Final", "temp_restore",
    "src_backup", "chatbot", "CATORTA_USB_PUNPRO", "certificados",
    "mariadb_server",
    "_update_cache", "locks",
}

EXCLUIR_EXT = {
    ".db", ".log", ".pyc", ".spec", ".zip", ".bat",
    ".iss", ".pdf", ".png", ".jpg", ".ico", ".exe",
    ".ps1", ".ini",
}
INCLUIR_JSON = {"version.json"}

SKIP_ROOT_FILES = {
    "get-pip.py", "old_admin.py", "test_error.py", "stress_test.py",
    "detect_ports.py", "clean_excel.py",
}


def load_manifest() -> dict:
    if os.path.isfile(VERSION_FILE) and os.path.getsize(VERSION_FILE) > 0:
        with open(VERSION_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {
        "app_version": "4.0",
        "channel": "stable",
        "build_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "modules": {},
    }


def scan_modules() -> dict:
    modules = {}
    for root, dirs, files in os.walk(REPO_ROOT):
        dirs[:] = [d for d in dirs if d not in EXCLUIR and not d.startswith(".")]
        for fname in files:
            ext = os.path.splitext(fname)[1].lower()
            if ext in EXCLUIR_EXT and fname not in INCLUIR_JSON:
                continue
            if fname.endswith(".json") and fname not in INCLUIR_JSON:
                continue

            file_path = os.path.join(root, fname)
            rel_path = os.path.relpath(file_path, REPO_ROOT).replace("\\", "/")
            if rel_path in SKIP_ROOT_FILES:
                continue

            with open(file_path, "rb") as f:
                content = f.read()
            modules[rel_path] = {
                "version": "1.0.0",
                "checksum": hashlib.md5(content).hexdigest(),
                "channel": "stable",
                "size": len(content),
            }
    return modules


def main():
    parser = argparse.ArgumentParser(description="Regenerar version.json")
    parser.add_argument("--version", "-v", help="Nueva app_version (ej. 4.6)")
    args = parser.parse_args()

    data = load_manifest()
    if args.version:
        data["app_version"] = str(args.version).strip()
    data["channel"] = data.get("channel") or "stable"
    data["build_date"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    data["modules"] = scan_modules()

    with open(VERSION_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(
        f"version.json OK — app_version={data['app_version']} "
        f"({len(data['modules'])} módulos)"
    )


if __name__ == "__main__":
    main()
