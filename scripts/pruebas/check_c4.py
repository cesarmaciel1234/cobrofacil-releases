import sys
import os
sys.path.insert(0, os.getcwd())
from src.carteleria.lanzador_tv.tv_cara_pack import _bytes_desencriptados
import zipfile
import io

try:
    raw = _bytes_desencriptados("downloaded_tv_cara.bin")
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        c4 = z.read("modules/columna4/columna4.js").decode('utf-8')
        print(c4[:500])
        if "tarjeta_chef" in c4:
            print("YES, tarjeta_chef is in columna4.js")
        else:
            print("NO, tarjeta_chef is NOT in columna4.js")
except Exception as e:
    print(e)
