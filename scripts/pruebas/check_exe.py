import urllib.request
import zipfile
import io

url = "https://github.com/cesarmaciel1234/cobrofacil-releases/releases/download/v13.2.7/CobroFacil_POS_Release.zip"
print("Downloading...")
req = urllib.request.Request(url)
with urllib.request.urlopen(req) as response:
    zip_data = response.read()

with zipfile.ZipFile(io.BytesIO(zip_data)) as z:
    for info in z.infolist():
        if "CobroFacil_POS.exe" in info.filename:
            print(f"{info.filename}: size={info.file_size}, date={info.date_time}")
