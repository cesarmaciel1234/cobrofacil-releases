import urllib.request
import json
import zipfile
import io

URL = "https://github.com/cesarmaciel1234/cobrofacil-releases/releases/download/v13.2.8/CobroFacil_POS_Release.zip"

print(f"Downloading v13.2.8...")
req = urllib.request.Request(URL, headers={'User-Agent': 'Mozilla/5.0'})
with urllib.request.urlopen(req) as response:
    zip_data = response.read()

with zipfile.ZipFile(io.BytesIO(zip_data)) as z:
    info = z.getinfo("CobroFacil_POS/CobroFacil_POS.exe")
    print("v13.2.8 exe size:", info.file_size)
