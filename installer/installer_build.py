"""
CajaFacil Pro - Instalador Universal (Windows 8 a Windows 11)
Compila con:
  pyinstaller --onefile --windowed --name CajaFacil_Pro_Setup installer\\installer_build.py
"""
import os, sys, json, zipfile, shutil, tempfile, threading, subprocess
import ssl, ctypes, urllib.request, tkinter as tk
from tkinter import ttk, messagebox, scrolledtext

APP_NAME     = "CajaFacil Pro"
VERSION      = "2026.2.0"
DESTINO      = r"C:\CajaFacil Pro"
DOWNLOAD_URL = "https://github.com/cesarmaciel1234/cajafacil-releases/releases/latest/download/CajaFacil_Pro.zip"
PYTHON_URL   = "https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe"

# Sin ventana de consola en subprocesos (Windows)
NO_WINDOW = subprocess.CREATE_NO_WINDOW if hasattr(subprocess, "CREATE_NO_WINDOW") else 0

C_BG   = "#0f172a"; C_CARD = "#1e293b"; C_ACC  = "#3b82f6"
C_OK   = "#10b981"; C_TXT  = "#f1f5f9"; C_SUB  = "#94a3b8"
C_BTN  = "#2563eb"; C_BTN2 = "#334155"; C_WARN = "#f59e0b"
C_LOG  = "#020a12"; C_LOG2 = "#0ea5e9"   # fondo y texto del log

FRASES = [
    ("🏆", "Con CajaFácil Pro vendés en segundos, sin capacitación"),
    ("⚡", "Primera venta en menos de 5 minutos desde que abrís"),
    ("📱", "Aceptá pagos en efectivo, tarjeta y transferencia"),
    ("🖨️", "Imprimí tickets profesionales con tu ticketera térmica"),
    ("📦", "Controlá tu stock en tiempo real — nunca más quedarte sin mercadería"),
    ("📊", "Reportes de ventas diarios, semanales y mensuales en un clic"),
    ("🔄", "Actualizaciones automáticas — siempre tenés la última versión"),
    ("🛡️", "Tus datos guardados de forma segura en tu propia PC"),
    ("💰", "Cierre de caja automático — el sistema hace las cuentas por vos"),
    ("🔌", "Compatible con balanza, lector de códigos y cajón de dinero"),
    ("👥", "Múltiples cajeros con contraseñas individuales"),
    ("🚀", "Funciona sin internet — ideal para conexión inestable"),
    ("📋", "Exportá tus reportes a Excel con un clic"),
    ("🎯", "Diseñado para carnicerías, verdulerías, kioscos y más"),
    ("⭐", "Soporte técnico incluido — estamos para ayudarte"),
]


# ── Helpers ───────────────────────────────────────────────────────────────────

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
            r = subprocess.run([cmd, "--version"], capture_output=True,
                               timeout=5, creationflags=NO_WINDOW)
            if r.returncode == 0:
                ver = (r.stdout + r.stderr).decode(errors="ignore").strip().split()[-1]
                maj, mn = int(ver.split(".")[0]), int(ver.split(".")[1])
                if maj >= 3 and mn >= 8:
                    return cmd
        except: pass
    return None

def run_cmd(args, on_log=None, timeout=300):
    """Ejecuta un comando SIN abrir consola y manda el output al log interno."""
    proc = subprocess.Popen(
        args,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        creationflags=NO_WINDOW,
        text=True, errors="ignore"
    )
    for line in proc.stdout:
        line = line.rstrip()
        if line and on_log:
            on_log(line)
    proc.wait()
    return proc.returncode

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
                   capture_output=True, timeout=10, creationflags=NO_WINDOW)


# ── Instalador ────────────────────────────────────────────────────────────────

class Installer(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(f"{APP_NAME} — Instalador v{VERSION}")
        self.geometry("560x530")
        self.resizable(False, False)
        self.configure(bg=C_BG)
        self.eval("tk::PlaceWindow . center")
        self._frase_idx = 0
        self._instalando = False
        self._log_visible = False
        self._ui()
        self._rotar_frase()

    # ── Construcción UI ───────────────────────────────────────────────────────
    def _ui(self):
        # Header
        hdr = tk.Frame(self, bg=C_ACC, height=78)
        hdr.pack(fill="x"); hdr.pack_propagate(False)
        tk.Label(hdr, text="🏆", font=("Segoe UI Emoji", 30),
                 bg=C_ACC, fg="white").pack(side="left", padx=16, pady=13)
        fr = tk.Frame(hdr, bg=C_ACC); fr.pack(side="left", pady=13)
        tk.Label(fr, text="CajaFácil Pro", font=("Segoe UI", 20, "bold"),
                 bg=C_ACC, fg="white").pack(anchor="w")
        tk.Label(fr, text="Vendé rápido · Sin experiencia · Sin complicaciones",
                 font=("Segoe UI", 9), bg=C_ACC, fg="#bfdbfe").pack(anchor="w")

        # Card
        self.card = tk.Frame(self, bg=C_CARD)
        self.card.pack(fill="both", expand=True, padx=20, pady=10)

        # Destino
        tk.Label(self.card, text="Se instalará en:", font=("Segoe UI", 9),
                 bg=C_CARD, fg=C_SUB).pack(anchor="w", padx=18, pady=(12, 1))
        tk.Label(self.card, text=DESTINO, font=("Consolas", 11, "bold"),
                 bg=C_CARD, fg=C_TXT).pack(anchor="w", padx=18)

        # Checks
        checks = tk.Frame(self.card, bg="#172033")
        checks.pack(fill="x", padx=18, pady=(8, 0))
        for txt in ["Descarga automática desde internet",
                     "Python 3.11 se instala si no está",
                     "Acceso directo en el Escritorio",
                     "Compatible: Windows 8 / 10 / 11"]:
            row = tk.Frame(checks, bg="#172033"); row.pack(fill="x", padx=10, pady=1)
            tk.Label(row, text="✓", font=("Segoe UI", 9),
                     bg="#172033", fg=C_OK).pack(side="left")
            tk.Label(row, text=f"  {txt}", font=("Segoe UI", 9),
                     bg="#172033", fg=C_TXT).pack(side="left")

        tk.Frame(self.card, bg="#2d3f55", height=1).pack(fill="x", padx=18, pady=6)

        # Frases animadas
        frase_frame = tk.Frame(self.card, bg="#0d1b2e", height=58)
        frase_frame.pack(fill="x", padx=18)
        frase_frame.pack_propagate(False)
        self.lbl_fi = tk.Label(frase_frame, text="💡", font=("Segoe UI Emoji", 17),
                                bg="#0d1b2e", fg=C_WARN)
        self.lbl_fi.place(x=10, y=10)
        self.lbl_ft = tk.Label(frase_frame, text="", font=("Segoe UI", 9),
                                bg="#0d1b2e", fg="#cbd5e1",
                                wraplength=460, justify="left")
        self.lbl_ft.place(x=42, y=8, width=490, height=44)

        # Estado + barra
        self.lbl_st = tk.Label(self.card, text="Listo para instalar",
                                font=("Segoe UI", 10), bg=C_CARD, fg=C_SUB)
        self.lbl_st.pack(anchor="w", padx=18, pady=(8, 2))

        sty = ttk.Style(); sty.theme_use("default")
        sty.configure("P.Horizontal.TProgressbar", background=C_ACC,
                       troughcolor="#334155", borderwidth=0, relief="flat")
        self.bar = ttk.Progressbar(self.card, style="P.Horizontal.TProgressbar",
                                    mode="determinate", length=520)
        self.bar.pack(padx=18, pady=(0, 8))

        # ── Panel de log (oculto por defecto) ────────────────────────────────
        self.log_frame = tk.Frame(self.card, bg=C_LOG)
        # No se hace pack aquí — se muestra/oculta con el botón

        self.log_txt = scrolledtext.ScrolledText(
            self.log_frame, height=7, bg=C_LOG, fg="#38bdf8",
            font=("Consolas", 8), bd=0, relief="flat",
            insertbackground="white", state="disabled"
        )
        self.log_txt.pack(fill="both", expand=True, padx=6, pady=4)

        # Botones
        bf = tk.Frame(self.card, bg=C_CARD)
        bf.pack(fill="x", padx=18, pady=(0, 12))

        self.btn = tk.Button(bf, text="  ⚡  INSTALAR AHORA  ",
                              font=("Segoe UI", 12, "bold"), bg=C_BTN, fg="white",
                              activebackground="#1d4ed8", activeforeground="white",
                              relief="flat", cursor="hand2", bd=0, padx=20, pady=11,
                              command=self.start)
        self.btn.pack(side="left", fill="x", expand=True)

        self.btn_log = tk.Button(bf, text="📋 Ver log",
                                  font=("Segoe UI", 9), bg=C_BTN2, fg=C_SUB,
                                  activebackground="#475569", activeforeground="white",
                                  relief="flat", cursor="hand2", bd=0, padx=12, pady=11,
                                  command=self._toggle_log)
        self.btn_log.pack(side="right", padx=(6, 0))

        self.btn_x = tk.Button(bf, text="Cancelar",
                                font=("Segoe UI", 9), bg=C_BTN2, fg=C_SUB,
                                activebackground="#475569", activeforeground="white",
                                relief="flat", cursor="hand2", bd=0, padx=12, pady=11,
                                command=self.destroy)
        self.btn_x.pack(side="right", padx=(6, 0))

        tk.Label(self, text=f"v{VERSION}  ·  Windows 8 / 10 / 11",
                 font=("Segoe UI", 8), bg=C_BG, fg="#475569").pack(pady=(0, 5))

    # ── Toggle log panel ──────────────────────────────────────────────────────
    def _toggle_log(self):
        if self._log_visible:
            self.log_frame.pack_forget()
            self.geometry("560x530")
            self.btn_log.config(text="📋 Ver log")
            self._log_visible = False
        else:
            self.log_frame.pack(fill="x", padx=18, pady=(0, 6))
            self.geometry("560x660")
            self.btn_log.config(text="📋 Ocultar log")
            self._log_visible = True

    # ── Agregar línea al log ──────────────────────────────────────────────────
    def log(self, line: str):
        def _write():
            self.log_txt.config(state="normal")
            self.log_txt.insert("end", line + "\n")
            self.log_txt.see("end")
            self.log_txt.config(state="disabled")
        self.after(0, _write)

    # ── Frases animadas ───────────────────────────────────────────────────────
    def _rotar_frase(self):
        icon, texto = FRASES[self._frase_idx % len(FRASES)]
        self.lbl_fi.config(text=icon)
        self.lbl_ft.config(fg="#0d1b2e")
        self.after(120, lambda: self._fade(texto))

    def _fade(self, texto):
        self.lbl_ft.config(text=texto, fg="#cbd5e1")
        self._frase_idx += 1
        self.after(5000 if self._instalando else 4000, self._rotar_frase)

    # ── Estado ────────────────────────────────────────────────────────────────
    def status(self, msg, pct=None):
        def _u():
            self.lbl_st.config(text=msg)
            if pct is not None:
                self.bar["value"] = pct
        self.after(0, _u)

    # ── Inicio ────────────────────────────────────────────────────────────────
    def start(self):
        if not is_admin():
            if not messagebox.askyesno("Permisos",
                "Se recomienda ejecutar como Administrador.\n¿Continuar de todas formas?"):
                return
        self._instalando = True
        self.btn.config(state="disabled", text="  ⏳  Instalando...  ")
        self.btn_x.config(state="disabled")
        # Mostrar log automáticamente al empezar
        if not self._log_visible:
            self._toggle_log()
        threading.Thread(target=self._run, daemon=True).start()

    # ── Proceso ───────────────────────────────────────────────────────────────
    def _run(self):
        tmp = None
        try:
            tmp = tempfile.mkdtemp(prefix="cajafacil_")
            zip_path = os.path.join(tmp, "app.zip")

            # 1. Descargar app
            self.log("► Conectando con GitHub...")
            self.status("Descargando CajaFácil Pro...", 3)
            def prog(done, total):
                pct = int(4 + 38 * done / total)
                self.status(f"Descargando... {int(done/total*100)}%", pct)
                if done == total:
                    self.log(f"✓ Descarga completa ({total//1024} KB)")
            download(DOWNLOAD_URL, zip_path, prog)
            self.status("✓ Descarga completa", 44)

            # 2. Extraer
            self.log("► Extrayendo archivos...")
            self.status("Descomprimiendo...", 47)
            with zipfile.ZipFile(zip_path, "r") as zf:
                zf.extractall(tmp)
            src = tmp
            for d in os.listdir(tmp):
                full = os.path.join(tmp, d)
                if os.path.isdir(full) and d != "__MACOSX":
                    src = full; break
            self.log("✓ Archivos extraídos")

            # 3. Copiar al destino
            self.log(f"► Instalando en {DESTINO}...")
            self.status("Copiando archivos del sistema...", 50)
            os.makedirs(DESTINO, exist_ok=True)
            items = ["src", "main.py", "version.json", "requirements_core.txt",
                     "requirements_full.txt", "CajaFacil_Pro.bat", "ACTUALIZAR.bat"]
            for item in items:
                s = os.path.join(src, item)
                d = os.path.join(DESTINO, item)
                if not os.path.exists(s): continue
                if os.path.isdir(s):
                    if os.path.exists(d): shutil.rmtree(d)
                    shutil.copytree(s, d)
                else:
                    shutil.copy2(s, d)
                self.log(f"  ✓ {item}")
            for fname in ["config.json", "punpro.db"]:
                s = os.path.join(src, fname)
                d = os.path.join(DESTINO, fname)
                if os.path.exists(s) and not os.path.exists(d):
                    shutil.copy2(s, d)
                    self.log(f"  ✓ {fname} (nuevo)")
            for folder in ["logs", "reportes", "backups", "certificados"]:
                os.makedirs(os.path.join(DESTINO, folder), exist_ok=True)
            self.status("✓ Archivos instalados", 56)

            # 4. Verificar Python
            self.log("► Verificando Python...")
            self.status("Verificando Python...", 59)
            py = find_python()
            if not py:
                self.log("  Python no encontrado — descargando 3.11...")
                self.status("Descargando Python 3.11...", 60)
                py_inst = os.path.join(tmp, "python_setup.exe")
                download(PYTHON_URL, py_inst)
                self.log("  Instalando Python 3.11 (sin ventanas)...")
                self.status("Instalando Python...", 64)
                run_cmd([py_inst, "/quiet", "InstallAllUsers=1",
                         "PrependPath=1", "Include_pip=1"], self.log, timeout=180)
                py = "python"
                self.log("✓ Python 3.11 instalado")
            else:
                self.log(f"✓ Python ya disponible ({py})")
            self.status("✓ Python listo", 67)

            # 5. Entorno virtual
            self.log("► Creando entorno virtual (.venv)...")
            self.status("Creando entorno de ejecución...", 69)
            venv = os.path.join(DESTINO, ".venv")
            if not os.path.exists(os.path.join(venv, "Scripts", "python.exe")):
                run_cmd([py, "-m", "venv", venv], self.log, timeout=60)
                self.log("✓ Entorno virtual creado")
            else:
                self.log("✓ Entorno virtual ya existe")
            self.status("✓ Entorno listo", 72)

            # 6. Actualizar pip
            pip = os.path.join(venv, "Scripts", "pip.exe")
            self.log("► Actualizando pip...")
            self.status("Actualizando gestor de paquetes...", 73)
            run_cmd([pip, "install", "--upgrade", "pip"], self.log, timeout=60)

            # 7. PyQt5
            self.log("► Instalando PyQt5 (interfaz gráfica)...")
            self.status("Instalando motor de interfaz (PyQt5)...", 75)
            run_cmd([pip, "install", "PyQt5"], self.log, timeout=180)
            self.log("✓ PyQt5 instalado")
            self.status("✓ Interfaz gráfica lista", 86)

            # 8. Pillow + requests
            self.log("► Instalando pillow y requests...")
            self.status("Instalando módulos de imágenes y red...", 88)
            run_cmd([pip, "install", "pillow", "requests"], self.log, timeout=120)
            self.log("✓ Módulos esenciales completos")
            self.status("✓ Módulos esenciales instalados", 91)

            # 9. Limpiar config
            try:
                cfg = os.path.join(DESTINO, "config.json")
                with open(cfg, encoding="utf-8") as f: d2 = json.load(f)
                d2["db_path"] = ""
                with open(cfg, "w", encoding="utf-8") as f:
                    json.dump(d2, f, indent=4, ensure_ascii=False)
                self.log("✓ Configuración limpiada")
            except: pass

            # 10. Acceso directo
            self.log("► Creando acceso directo en el escritorio...")
            self.status("Creando acceso directo...", 94)
            desk = os.path.join(os.path.expanduser("~"), "Desktop")
            make_shortcut(os.path.join(desk, "CajaFacil Pro.lnk"),
                          os.path.join(DESTINO, "CajaFacil_Pro.bat"), DESTINO)
            self.log("✓ Acceso directo creado")

            # 11. Limpiar temp
            self.log("► Limpiando archivos temporales...")
            self.status("Limpiando temporales...", 97)
            shutil.rmtree(tmp, ignore_errors=True)
            self.log("✓ Temporales eliminados")
            self.log("")
            self.log("═══════════════════════════════════")
            self.log("  ✅ INSTALACIÓN COMPLETADA        ")
            self.log("═══════════════════════════════════")

            self.status("✅  ¡CajaFácil Pro instalado correctamente!", 100)
            self.after(0, self._ok)

        except Exception as e:
            if tmp: shutil.rmtree(tmp, ignore_errors=True)
            self.log(f"\n❌ ERROR: {e}")
            self.after(0, lambda: self._err(str(e)))

    # ── Resultados ────────────────────────────────────────────────────────────
    def _ok(self):
        self._instalando = False
        self.btn.config(state="normal",
                         text="  ✅  Abrir CajaFácil Pro  ",
                         bg=C_OK, command=self._open)
        self.btn_x.config(state="normal", text="Cerrar", command=self.destroy)
        messagebox.showinfo("✅ ¡Instalación completa!",
                             f"CajaFácil Pro está listo en:\n{DESTINO}\n\n"
                             "• Doble clic en 'CajaFacil Pro' del escritorio\n"
                             "• Los módulos adicionales se instalan solos al usar la app")

    def _err(self, e):
        self._instalando = False
        self.btn.config(state="normal", text="  ⚡  Reintentar  ")
        self.btn_x.config(state="normal")
        self.status("❌ Error — revisá tu conexión a internet", 0)
        messagebox.showerror("Error", f"Ocurrió un error:\n\n{e}")

    def _open(self):
        bat = os.path.join(DESTINO, "CajaFacil_Pro.bat")
        if os.path.exists(bat):
            subprocess.Popen(["cmd", "/c", bat], cwd=DESTINO,
                             creationflags=NO_WINDOW)
        self.destroy()


if __name__ == "__main__":
    Installer().mainloop()
