"""
CajaFacil Pro - Instalador Universal (Windows 8 a Windows 11)
Compila con:
  pyinstaller --onefile --windowed --name CajaFacil_Pro_Setup scratch\\installer_build.py
"""
import os, sys, json, zipfile, shutil, tempfile, threading
import subprocess, ssl, ctypes, urllib.request, tkinter as tk
from tkinter import ttk, messagebox

APP_NAME     = "CajaFacil Pro"
VERSION      = "2026.2.0"
DESTINO      = r"C:\CajaFacil Pro"
DOWNLOAD_URL = "https://github.com/cesarmaciel1234/cajafacil-releases/releases/latest/download/CajaFacil_Pro.zip"
PYTHON_URL   = "https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe"

C_BG = "#0f172a"; C_CARD = "#1e293b"; C_ACC = "#3b82f6"
C_OK = "#10b981"; C_TXT = "#f1f5f9"; C_SUB = "#94a3b8"
C_BTN = "#2563eb"; C_BTN2 = "#334155"


def is_admin():
    try: return ctypes.windll.shell32.IsUserAnAdmin()
    except: return False

def ssl_ctx():
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    return ctx

def find_python():
    for cmd in ["python", "py"]:
        try:
            r = subprocess.run([cmd, "--version"], capture_output=True, timeout=5)
            if r.returncode == 0:
                ver = (r.stdout + r.stderr).decode(errors="ignore").strip().split()[-1]
                maj, mn = int(ver.split(".")[0]), int(ver.split(".")[1])
                if maj >= 3 and mn >= 8:
                    return cmd
        except: pass
    return None

def download(url, path, on_progress=None):
    req = urllib.request.Request(url, headers={"User-Agent": "CajaFacilPro-Installer"})
    with urllib.request.urlopen(req, context=ssl_ctx(), timeout=90) as r:
        total = int(r.headers.get("Content-Length", 0))
        done = 0
        with open(path, "wb") as f:
            while chunk := r.read(8192):
                f.write(chunk)
                done += len(chunk)
                if on_progress and total:
                    on_progress(done, total)

def make_shortcut(lnk, target, workdir):
    ps = (f'$ws=New-Object -ComObject WScript.Shell;'
          f'$s=$ws.CreateShortcut("{lnk}");'
          f'$s.TargetPath="{target}";'
          f'$s.WorkingDirectory="{workdir}";'
          f'$s.Description="CajaFacil Pro";$s.Save()')
    subprocess.run(["powershell", "-ExecutionPolicy", "Bypass", "-Command", ps],
                   capture_output=True, timeout=10)


class Installer(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(f"{APP_NAME} â€” Instalador v{VERSION}")
        self.geometry("520x420")
        self.resizable(False, False)
        self.configure(bg=C_BG)
        self.eval("tk::PlaceWindow . center")
        self._ui()

    def _ui(self):
        # Header
        hdr = tk.Frame(self, bg=C_ACC, height=78); hdr.pack(fill="x"); hdr.pack_propagate(False)
        tk.Label(hdr, text="ðŸ†", font=("Segoe UI", 30), bg=C_ACC, fg="white").pack(side="left", padx=16, pady=14)
        fr = tk.Frame(hdr, bg=C_ACC); fr.pack(side="left", pady=14)
        tk.Label(fr, text="CajaFÃ¡cil Pro", font=("Segoe UI", 20, "bold"), bg=C_ACC, fg="white").pack(anchor="w")
        tk.Label(fr, text="VendÃ© rÃ¡pido Â· Sin experiencia Â· Sin complicaciones",
                 font=("Segoe UI", 9), bg=C_ACC, fg="#bfdbfe").pack(anchor="w")

        # Card
        card = tk.Frame(self, bg=C_CARD); card.pack(fill="both", expand=True, padx=24, pady=14)

        tk.Label(card, text="Se instalarÃ¡ en:", font=("Segoe UI", 10),
                 bg=C_CARD, fg=C_SUB).pack(anchor="w", padx=20, pady=(16, 2))
        tk.Label(card, text=DESTINO, font=("Consolas", 11, "bold"),
                 bg=C_CARD, fg=C_TXT).pack(anchor="w", padx=20)

        info = tk.Frame(card, bg="#172033"); info.pack(fill="x", padx=20, pady=12)
        for txt in ["Descarga automÃ¡tica desde internet",
                     "Python se instala si no estÃ¡ presente",
                     "Acceso directo en el Escritorio",
                     "Compatible: Windows 8 / 10 / 11 (32 y 64 bits)"]:
            row = tk.Frame(info, bg="#172033"); row.pack(fill="x", padx=12, pady=2)
            tk.Label(row, text="âœ“", font=("Segoe UI", 10), bg="#172033", fg=C_OK).pack(side="left")
            tk.Label(row, text=f"  {txt}", font=("Segoe UI", 10), bg="#172033", fg=C_TXT).pack(side="left")

        self.lbl = tk.Label(card, text="Listo para instalar", font=("Segoe UI", 10),
                             bg=C_CARD, fg=C_SUB)
        self.lbl.pack(anchor="w", padx=20, pady=(10, 3))

        style = ttk.Style(); style.theme_use("default")
        style.configure("A.Horizontal.TProgressbar", background=C_ACC,
                         troughcolor="#334155", borderwidth=0, relief="flat")
        self.bar = ttk.Progressbar(card, style="A.Horizontal.TProgressbar",
                                    mode="determinate", length=460)
        self.bar.pack(padx=20, pady=(0, 14))

        bf = tk.Frame(card, bg=C_CARD); bf.pack(fill="x", padx=20, pady=(0, 16))
        self.btn = tk.Button(bf, text="  âš¡  INSTALAR AHORA  ",
                              font=("Segoe UI", 12, "bold"), bg=C_BTN, fg="white",
                              activebackground="#1d4ed8", activeforeground="white",
                              relief="flat", cursor="hand2", bd=0, padx=20, pady=12,
                              command=self.start)
        self.btn.pack(side="left", fill="x", expand=True)
        self.btn_x = tk.Button(bf, text="Cancelar", font=("Segoe UI", 10),
                                bg=C_BTN2, fg=C_SUB, activebackground="#475569",
                                activeforeground="white", relief="flat", cursor="hand2",
                                bd=0, padx=20, pady=12, command=self.destroy)
        self.btn_x.pack(side="right", padx=(10, 0))

        tk.Label(self, text=f"v{VERSION}  Â·  Windows 8 / 10 / 11",
                 font=("Segoe UI", 8), bg=C_BG, fg="#475569").pack(pady=(0, 7))

    def status(self, msg, pct=None):
        def _u():
            self.lbl.config(text=msg)
            if pct is not None: self.bar["value"] = pct
        self.after(0, _u)

    def start(self):
        if not is_admin():
            if not messagebox.askyesno("Permisos",
                "Se recomienda ejecutar como Administrador.\nÂ¿Continuar de todas formas?"):
                return
        self.btn.config(state="disabled", text="  â³  Instalando...  ")
        self.btn_x.config(state="disabled")
        threading.Thread(target=self._run, daemon=True).start()

    def _run(self):
        tmp = None
        try:
            tmp = tempfile.mkdtemp(prefix="cajafacil_")
            zip_path = os.path.join(tmp, "app.zip")

            # 1. Descargar
            self.status("Descargando CajaFÃ¡cil Pro...", 5)
            def prog(done, total):
                self.status(f"Descargando... {int(done/total*100)}%",
                             int(5 + 40 * done / total))
            download(DOWNLOAD_URL, zip_path, prog)
            self.status("Descarga completa âœ“", 47)

            # 2. Extraer
            self.status("Extrayendo archivos...", 50)
            with zipfile.ZipFile(zip_path, "r") as zf:
                zf.extractall(tmp)
            src = tmp
            for d in os.listdir(tmp):
                full = os.path.join(tmp, d)
                if os.path.isdir(full) and d != "__MACOSX":
                    src = full; break

            # 3. Instalar archivos
            self.status("Instalando en " + DESTINO + "...", 55)
            os.makedirs(DESTINO, exist_ok=True)
            for item in ["src", "main.py", "version.json",
                          "requirements_core.txt", "CajaFacil_Pro.bat", "ACTUALIZAR.bat"]:
                s = os.path.join(src, item)
                d = os.path.join(DESTINO, item)
                if not os.path.exists(s): continue
                if os.path.isdir(s):
                    if os.path.exists(d): shutil.rmtree(d)
                    shutil.copytree(s, d)
                else:
                    shutil.copy2(s, d)
            for fname in ["config.json", "punpro.db"]:
                s = os.path.join(src, fname)
                d = os.path.join(DESTINO, fname)
                if os.path.exists(s) and not os.path.exists(d):
                    shutil.copy2(s, d)
            for folder in ["logs", "reportes", "backups", "certificados"]:
                os.makedirs(os.path.join(DESTINO, folder), exist_ok=True)

            # 4. Python
            self.status("Verificando Python...", 62)
            py = find_python()
            if not py:
                self.status("Descargando Python 3.11...", 63)
                py_inst = os.path.join(tmp, "python_setup.exe")
                download(PYTHON_URL, py_inst)
                self.status("Instalando Python...", 66)
                subprocess.run([py_inst, "/quiet", "InstallAllUsers=1",
                                 "PrependPath=1", "Include_pip=1"],
                               check=True, timeout=180)
                py = "python"

            # 5. Venv
            self.status("Creando entorno virtual...", 70)
            venv = os.path.join(DESTINO, ".venv")
            if not os.path.exists(os.path.join(venv, "Scripts", "python.exe")):
                subprocess.run([py, "-m", "venv", venv],
                               check=True, capture_output=True, timeout=60)

            # 6. Dependencias
            self.status("Instalando dependencias (2-3 min)...", 74)
            pip = os.path.join(venv, "Scripts", "pip.exe")
            req = os.path.join(DESTINO, "requirements_core.txt")
            subprocess.run([pip, "install", "-q", "--upgrade", "pip"],
                           capture_output=True, timeout=60)
            subprocess.run([pip, "install", "-q", "-r", req],
                           check=True, capture_output=True, timeout=300)
            self.status("Dependencias instaladas âœ“", 90)

            # 7. Limpiar config
            try:
                cfg = os.path.join(DESTINO, "config.json")
                with open(cfg, encoding="utf-8") as f: d2 = json.load(f)
                d2["db_path"] = ""
                with open(cfg, "w", encoding="utf-8") as f:
                    json.dump(d2, f, indent=4, ensure_ascii=False)
            except: pass

            # 8. Acceso directo
            self.status("Creando acceso directo...", 93)
            desk = os.path.join(os.path.expanduser("~"), "Desktop")
            make_shortcut(
                os.path.join(desk, "CajaFacil Pro.lnk"),
                os.path.join(DESTINO, "CajaFacil_Pro.bat"),
                DESTINO
            )

            # 9. Limpiar temp
            self.status("Limpiando temporales...", 97)
            shutil.rmtree(tmp, ignore_errors=True)

            self.status("âœ…  InstalaciÃ³n completa!", 100)
            self.after(0, self._ok)

        except Exception as e:
            if tmp: shutil.rmtree(tmp, ignore_errors=True)
            self.after(0, lambda: self._err(str(e)))

    def _ok(self):
        self.btn.config(state="normal", text="  âœ…  Abrir CajaFÃ¡cil Pro  ",
                         bg=C_OK, command=self._open)
        self.btn_x.config(state="normal", text="Cerrar", command=self.destroy)
        messagebox.showinfo("âœ… Listo",
                             f"CajaFÃ¡cil Pro instalado en:\n{DESTINO}\n\n"
                             "Doble clic en 'CajaFacil Pro' del escritorio.")

    def _err(self, e):
        self.btn.config(state="normal", text="  âš¡  Reintentar  ")
        self.btn_x.config(state="normal")
        self.status("âŒ Error â€” revisÃ¡ tu conexiÃ³n a internet", 0)
        messagebox.showerror("Error", f"OcurriÃ³ un error:\n\n{e}")

    def _open(self):
        bat = os.path.join(DESTINO, "CajaFacil_Pro.bat")
        if os.path.exists(bat):
            subprocess.Popen(["cmd", "/c", bat], cwd=DESTINO)
        self.destroy()


if __name__ == "__main__":
    Installer().mainloop()
