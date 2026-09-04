import sys
import os
sys.path.insert(0, os.getcwd())
from src.carteleria.lanzador_tv.tv_cara_pack import _bytes_desencriptados
import zipfile
import io

try:
    raw = _bytes_desencriptados("downloaded_tv_cara.bin")
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        html = z.read("index.html").decode('utf-8')
        print(html[:500])
        print("...")
        if "tarjeta_chef.js" in html:
            print("YES, tarjeta_chef.js is in index.html")
        else:
            print("NO, tarjeta_chef.js is NOT in index.html!")
except Exception as e:
    print(e)
