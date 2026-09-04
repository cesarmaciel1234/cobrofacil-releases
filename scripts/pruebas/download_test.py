import urllib.request
import zipfile
import io
import os

url = "https://github.com/cesarmaciel1234/cobrofacil-releases/releases/download/v13.2.7/CobroFacil_POS_Release.zip"
print("Downloading...")
req = urllib.request.Request(url)
with urllib.request.urlopen(req) as response:
    zip_data = response.read()

print("Extracting tv_cara.bin...")
with zipfile.ZipFile(io.BytesIO(zip_data)) as z:
    for name in z.namelist():
        if name.endswith("tv_cara.bin"):
            blob = z.read(name)
            with open("downloaded_tv_cara.bin", "wb") as f:
                f.write(blob)
            print(f"Saved {name}")
