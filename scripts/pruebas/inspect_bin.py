import sys
import os
sys.path.insert(0, os.getcwd())
from src.carteleria.lanzador_tv.tv_cara_pack import _bytes_desencriptados
import zipfile
import io

try:
    raw = _bytes_desencriptados("downloaded_tv_cara.bin")
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        chef = z.read("modules/columna4/tarjetas/tarjeta_chef.js").decode('utf-8')
        if "NUEVO" in chef:
            for line in chef.splitlines():
                if "NUEVO" in line:
                    print(line.strip().encode('utf-8'))
        else:
            print("NUEVO not found")
        if "COMPRA" in chef:
            for line in chef.splitlines():
                if "COMPRA" in line:
                    print(line.strip().encode('utf-8'))
except Exception as e:
    print(e)
