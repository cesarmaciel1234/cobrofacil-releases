import sys

with open('src/carteleria/lanzador_tv/tv_cara_pack.py', 'r', encoding='utf-8') as f:
    content = f.read()

old_code = """    for path in candidatos:
        if path and os.path.isfile(path) and os.path.getsize(path) > 32:
            return path
    return \"\""""

new_code = """    # Tambien buscar en la carpeta src/ actualizada por OTA
    try:
        from src.utils.paths import get_base_path
        candidatos.append(os.path.join(get_base_path(), "src", "carteleria", "lanzador_tv", BLOB_NAME))
    except Exception:
        pass

    validos = []
    for path in candidatos:
        if path and os.path.isfile(path) and os.path.getsize(path) > 32:
            validos.append(path)
            
    if not validos:
        return ""
        
    # Devolver el blob más reciente (por fecha de modificación) para asegurar que se usa el descargado por OTA
    import os
    validos.sort(key=lambda p: os.path.getmtime(p), reverse=True)
    return validos[0]"""

content = content.replace(old_code, new_code)

with open('src/carteleria/lanzador_tv/tv_cara_pack.py', 'w', encoding='utf-8') as f:
    f.write(content)
