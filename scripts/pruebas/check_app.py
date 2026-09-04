import sys
import os
sys.path.insert(0, os.getcwd())
from src.carteleria.lanzador_tv.tv_cara_pack import _bytes_desencriptados
import zipfile
import io

try:
    raw = _bytes_desencriptados("downloaded_tv_cara.bin")
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        app = z.read("app.js").decode('utf-8')
        print(app[:500])
        if "tarjeta_chef" in app:
            print("YES, tarjeta_chef is in app.js")
        else:
            print("NO, tarjeta_chef is NOT in app.js")
except Exception as e:
    print(e)
