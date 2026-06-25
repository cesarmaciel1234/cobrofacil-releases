"""Empaqueta dist/CobroFacil_POS + mariadb_server en CobroFacil_POS_Release.zip."""

import os
import sys
import zipfile

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
POS_DIR = os.path.join(REPO_ROOT, "dist", "CobroFacil_POS")
OUT_ZIP = os.path.join(REPO_ROOT, "dist", "CobroFacil_POS_Release.zip")
MARIADB_DIR = os.path.join(REPO_ROOT, "mariadb_server")


def main():
    if not os.path.isfile(os.path.join(POS_DIR, "CobroFacil_POS.exe")):
        print(f"ERROR: falta {POS_DIR}/CobroFacil_POS.exe", file=sys.stderr)
        sys.exit(1)
    if not os.path.isfile(os.path.join(MARIADB_DIR, "bin", "mysqld.exe")):
        print("ERROR: falta mariadb_server/bin/mysqld.exe (ejecute prepare_mariadb_release.py)", file=sys.stderr)
        sys.exit(1)

    if os.path.exists(OUT_ZIP):
        os.remove(OUT_ZIP)

    count = 0
    with zipfile.ZipFile(OUT_ZIP, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
        for root, _, files in os.walk(POS_DIR):
            for name in files:
                path = os.path.join(root, name)
                zf.write(path, os.path.relpath(path, POS_DIR))
                count += 1

        for root, _, files in os.walk(MARIADB_DIR):
            for name in files:
                path = os.path.join(root, name)
                arc = os.path.join("mariadb_server", os.path.relpath(path, MARIADB_DIR))
                zf.write(path, arc)
                count += 1

    bad = zipfile.ZipFile(OUT_ZIP).testzip()
    if bad:
        print(f"ZIP corrupto: {bad}", file=sys.stderr)
        sys.exit(1)

    print(f"ZIP OK: {OUT_ZIP} ({os.path.getsize(OUT_ZIP)} bytes, {count} archivos)")


if __name__ == "__main__":
    main()
