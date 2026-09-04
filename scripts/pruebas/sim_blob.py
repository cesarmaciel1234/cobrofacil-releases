import sys
import os

BLOB_NAME = "tv_cara.bin"

def buscar_blob(exe_dir):
    candidatos = []
    
    # 1. Simulate frozen candidates
    meipass = os.path.join(exe_dir, "_internal")
    candidatos.extend(
        [
            os.path.join(meipass, BLOB_NAME) if meipass else "",
            os.path.join(exe_dir, "_internal", BLOB_NAME),
            os.path.join(exe_dir, BLOB_NAME),
        ]
    )
    
    # 2. Simulate try blocks
    candidatos.append(os.path.join(exe_dir, "_internal", "src", "carteleria", "lanzador_tv", BLOB_NAME))
    candidatos.append(os.path.join(exe_dir, "_internal", BLOB_NAME))
    candidatos.append(os.path.join(exe_dir, "src", "carteleria", "lanzador_tv", BLOB_NAME))
    
    print("Candidates considered:")
    validos = []
    for path in candidatos:
        print(f" - {path}")
        if path and os.path.isfile(path) and os.path.getsize(path) > 32:
            validos.append(path)
            
    if not validos:
        return ""
        
    validos.sort(key=lambda p: os.path.getmtime(p), reverse=True)
    return validos[0]

print("Selected:", buscar_blob("C:\\Users\\cesar\\CobroFacil_POS_Install"))
