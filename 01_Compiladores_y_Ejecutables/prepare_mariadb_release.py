"""Prepara mariadb_server para el ZIP de release (CI y empaquetado local)."""

import os
import shutil
import sys
import urllib.request
import zipfile

MARIADB_URL = (
    "https://archive.mariadb.org/mariadb-10.11.7/winx64-packages/"
    "mariadb-10.11.7-winx64.zip"
)
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SERVER_DIR = os.path.join(REPO_ROOT, "mariadb_server")
MYSQLD_EXE = os.path.join(SERVER_DIR, "bin", "mysqld.exe")


def _download_mariadb():
    temp_zip = os.path.join(REPO_ROOT, "temp_mariadb_release.zip")
    prefix = "mariadb-10.11.7-winx64/"

    print("Descargando MariaDB portable para el release...")
    urllib.request.urlretrieve(MARIADB_URL, temp_zip)

    os.makedirs(SERVER_DIR, exist_ok=True)
    with zipfile.ZipFile(temp_zip, "r") as archive:
        for name in archive.namelist():
            if name.startswith(f"{prefix}bin/") or name.startswith(f"{prefix}share/"):
                archive.extract(name, REPO_ROOT)

    extracted = os.path.join(REPO_ROOT, "mariadb-10.11.7-winx64")
    for item in os.listdir(extracted):
        src = os.path.join(extracted, item)
        dst = os.path.join(SERVER_DIR, item)
        if os.path.exists(dst):
            shutil.rmtree(dst) if os.path.isdir(dst) else os.remove(dst)
        shutil.move(src, dst)
    os.rmdir(extracted)
    os.remove(temp_zip)
    print("MariaDB portable listo en mariadb_server/")


def _reset_data_dir():
    data_dir = os.path.join(SERVER_DIR, "data")
    if os.path.isdir(data_dir):
        shutil.rmtree(data_dir)
    os.makedirs(data_dir, exist_ok=True)


def main():
    if not os.path.isfile(MYSQLD_EXE):
        _download_mariadb()

    if not os.path.isfile(MYSQLD_EXE):
        print(f"ERROR: no se encontró {MYSQLD_EXE}", file=sys.stderr)
        sys.exit(1)

    _reset_data_dir()
    print(f"OK: {MYSQLD_EXE}")


if __name__ == "__main__":
    main()
