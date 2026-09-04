import sys
import os
sys.path.insert(0, os.getcwd())
from src.carteleria.lanzador_tv.tv_cara_pack import _bytes_desencriptados
import zipfile
import io
import re

try:
    raw = _bytes_desencriptados("downloaded_tv_cara.bin")
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        html = z.read("index.html").decode('utf-8')
        scripts = re.findall(r'<script.*?</script>', html, flags=re.DOTALL | re.IGNORECASE)
        for s in scripts:
            print(s)
except Exception as e:
    print(e)
