import os
import shutil

def move_docs():
    target_dir = "docs"
    if not os.path.exists(target_dir):
        os.makedirs(target_dir)
        print(f"✅ Carpeta creada: {target_dir}")

    docs = ["README.md", "README_HARDWARE.md", "DIARIO_DE_APRENDIZAJE.md"]
    
    for doc in docs:
        if os.path.exists(doc):
            try:
                shutil.move(doc, os.path.join(target_dir, doc))
                print(f"✅ Movido a docs/: {doc}")
            except Exception as e:
                print(f"❌ Error al mover {doc}: {e}")

if __name__ == "__main__":
    move_docs()
