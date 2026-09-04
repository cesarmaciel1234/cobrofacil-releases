import urllib.request
import zipfile
import io
import sys
import os
sys.path.insert(0, os.getcwd())
from src.carteleria.lanzador_tv.tv_cara_pack import _bytes_desencriptados

url = "https://github.com/cesarmaciel1234/cobrofacil-releases/releases/download/v13.2.8/CobroFacil_POS_Release.zip"
print("Downloading v13.2.8...")
req = urllib.request.Request(url)
with urllib.request.urlopen(req) as response:
    zip_data = response.read()

with zipfile.ZipFile(io.BytesIO(zip_data)) as z:
    for name in z.namelist():
        if name.endswith("tv_cara.bin"):
            blob = z.read(name)
            with open("downloaded_tv_cara.bin", "wb") as f:
                f.write(blob)
            print("Extracted tv_cara.bin")

try:
    raw = _bytes_desencriptados("downloaded_tv_cara.bin")
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        chef = z.read("modules/columna4/tarjetas/tarjeta_chef.js").decode('utf-8')
        if "FAMILIAS COMPRARON" in chef:
            print("YES, NEW CODE IS PRESENT!")
        else:
            print("NO, OLD CODE IS PRESENT!")
except Exception as e:
    print(e)
