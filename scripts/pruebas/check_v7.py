import urllib.request
import zipfile
import io
import json

URL = "https://github.com/cesarmaciel1234/cobrofacil-releases/releases/download/v13.2.7/CobroFacil_POS_Release.zip"

print(f"Downloading v13.2.7...")
req = urllib.request.Request(URL, headers={'User-Agent': 'Mozilla/5.0'})
with urllib.request.urlopen(req) as response:
    zip_data = response.read()

with zipfile.ZipFile(io.BytesIO(zip_data)) as z:
    with z.open("CobroFacil_POS/_internal/tv_cara.bin") as f:
        blob = f.read()
        print("Extracted tv_cara.bin")

def dec(b):
    r = bytearray(b)
    for i in range(len(r)):
        r[i] ^= 0x5A
    return bytes(r)

with zipfile.ZipFile(io.BytesIO(dec(blob))) as inner:
    with inner.open("modules/columna4/tarjetas/tarjeta_chef.js") as f:
        js = f.read().decode("utf-8")
        if "FAMILIAS COMPRARON" in js:
            print("YES, NEW CODE IS PRESENT IN V13.2.7!")
        else:
            print("NO NEW CODE IN V13.2.7!")
