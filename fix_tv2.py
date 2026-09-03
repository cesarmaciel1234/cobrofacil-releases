import re

with open("src/carteleria/lanzador_tv/tv_cara_pack.py", "r", encoding="utf-8") as f:
    text = f.read()

replacement = """def instalar_blob_en_dist(dist_dir: str, source_dir: str | None = None) -> str:
    try:
        internal = os.path.join(dist_dir, "_internal")
        os.makedirs(internal, exist_ok=True)
        dest = os.path.join(internal, BLOB_NAME)
        
        # Si ya lo copiaron antes, no hace falta re-empaquetarlo
        necesita_pack = True
        if os.path.isfile(dest):
            with open(dest, "rb") as fh:
                if fh.read().startswith(_MAGIC):
                    necesita_pack = False
        
        if necesita_pack:
            print(f"Empaquetando blob a {dest}...")
            pack_source(dest, source_dir)
        else:
            print(f"Blob ya existe y es valido en {dest}, saltando pack_source.")
            
        leftovers = []
        for root, dirs, _files in os.walk(dist_dir):
            if "la_cara_web" in dirs:
                leftovers.append(os.path.join(root, "la_cara_web"))
                dirs.remove("la_cara_web")
        for path in leftovers:
            shutil.rmtree(path, ignore_errors=True)
        public_src = os.path.join(dist_dir, "src")
        if os.path.isdir(public_src):
            shutil.rmtree(public_src, ignore_errors=True)
        return dest
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise e
"""

text = re.sub(r'def instalar_blob_en_dist\(dist_dir: str, source_dir: str \| None = None\) -> str:.*?return dest\n', replacement, text, flags=re.DOTALL)

with open("src/carteleria/lanzador_tv/tv_cara_pack.py", "w", encoding="utf-8", newline="") as f:
    f.write(text)
