import urllib.request
import os

icons = {
    "sol": "http://openweathermap.org/img/wn/01d@2x.png",
    "nube": "http://openweathermap.org/img/wn/02d@2x.png",
    "lluvia": "http://openweathermap.org/img/wn/10d@2x.png"
}

out_dir = r"c:\Users\cesar\OneDrive\Desktop\tpv pro 2026\src\vistas\assets"

for name, url in icons.items():
    out_path = os.path.join(out_dir, f"{name}.png")
    urllib.request.urlretrieve(url, out_path)
    print(f"Downloaded {out_path}")
