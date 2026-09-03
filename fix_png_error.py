with open("src/carteleria/creador_png/panel_png_productos.py", "r", encoding="utf-8") as f:
    text = f.read()

replacement = """        last_err = ""
        last_err_8000 = ""
        for url in urls:
            try:
                with open(fpath, "rb") as f:
                    res = requests.post(
                        url,
                        files={"file": (filename, f, "image/png")},
                        timeout=8,
                    )
                if res.status_code == 200:
                    print(f"[Cartelería] PNG {filename} enviado a maestra {url}")
                    return True, f"PNG copiado a la maestra ({db_host})."
                last_err = f"HTTP {res.status_code} en {url}"
                if "8000" in url: last_err_8000 = last_err
            except Exception as e:
                last_err = str(e)
                if "8000" in url: last_err_8000 = last_err
                continue
                
        err_mostrar = last_err_8000 if last_err_8000 else last_err
        return (
            False,
            f"No se pudo enviar el PNG a la maestra {db_host}.\\n"
            "Encendé esa PC y el Servidor de Tienda (puerto 8000).\\n"
            f"{err_mostrar}",
        )"""

import re
text = re.sub(r'        last_err = "".*?        \)', replacement, text, flags=re.DOTALL)

with open("src/carteleria/creador_png/panel_png_productos.py", "w", encoding="utf-8", newline="") as f:
    f.write(text)
