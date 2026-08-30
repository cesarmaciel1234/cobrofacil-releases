# Runtime hook PyInstaller: DLL de Qt en PATH antes de importar WebEngine.
import os
import sys

if getattr(sys, "frozen", False):
    roots = []
    meipass = getattr(sys, "_MEIPASS", "") or ""
    exe_dir = os.path.dirname(os.path.abspath(sys.executable))
    if meipass:
        roots.append(meipass)
    roots.append(os.path.join(exe_dir, "_internal"))
    extra = [p for p in roots if p and os.path.isdir(p)]
    for root in list(extra):
        bin_dir = os.path.join(root, "PyQt6", "Qt6", "bin")
        if os.path.isdir(bin_dir):
            extra.append(bin_dir)
    if extra:
        os.environ["PATH"] = os.pathsep.join(extra + [os.environ.get("PATH", "")])
