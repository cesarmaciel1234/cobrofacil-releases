import urllib.request
import zipfile
import io

req = urllib.request.Request("https://api.github.com/repos/cesarmaciel1234/cobrofacil-releases/actions/runs/33660803245/logs")
try:
    with urllib.request.urlopen(req) as response:
        with zipfile.ZipFile(io.BytesIO(response.read())) as z:
            for name in z.namelist():
                if 'Asegurar cara web' in name:
                    print(f"--- {name} ---")
                    print(z.read(name).decode('utf-8'))
except Exception as e:
    print(f"Error: {e}")
