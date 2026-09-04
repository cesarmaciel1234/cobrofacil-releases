import sys
import os

def get_candidatos():
    BLOB_NAME = "tv_cara.bin"
    candidatos = []
    if True: # Simulating frozen
        exe_dir = "C:\\Users\\cesar\\CobroFacil_POS_Install"
        meipass = os.path.join(exe_dir, "_internal")
        candidatos.extend([
            os.path.join(meipass, BLOB_NAME) if meipass else "",
            os.path.join(exe_dir, "_internal", BLOB_NAME),
            os.path.join(exe_dir, BLOB_NAME),
        ])
    try:
        candidatos.append(os.path.join(exe_dir, "_internal", "src", "carteleria", "lanzador_tv", BLOB_NAME))
        candidatos.append(os.path.join(exe_dir, "_internal", BLOB_NAME))
    except Exception:
        pass
    try:
        candidatos.append(os.path.join(exe_dir, "src", "carteleria", "lanzador_tv", BLOB_NAME))
    except Exception:
        pass
        
    validos = []
    for path in candidatos:
        if path and os.path.isfile(path) and os.path.getsize(path) > 32:
            validos.append((path, os.path.getmtime(path)))
    
    return validos

v = get_candidatos()
for p in v:
    print(p)
