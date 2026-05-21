"""
CajaFacil Pro - Instalador Universal (Windows 8 a Windows 11)
Compila con:
  pyinstaller --onefile --windowed --name CajaFacil_Pro_Setup installer\\installer_build.py
"""
import os, sys, json, zipfile, shutil, tempfile, threading, time
import subprocess, ssl, ctypes, urllib.request, tkinter as tk
from tkinter import ttk, messagebox

APP_NAME     = "CajaFacil Pro"
VERSION      = "2026.2.0"
DESTINO      = r"C:\CajaFacil Pro"
DOWNLOAD_URL = "https://github.com/cesarmaciel1234/cajafacil-releases/releases/latest/download/CajaFacil_Pro.zip"
PYTHON_URL   = "https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe"

C_BG = "#0f172a"; C_CARD = "#1e293b"; C_ACC = "#3b82f6"
C_OK = "#10b981"; C_TXT = "#f1f5f9"; C_SUB = "#94a3b8"
C_BTN = "#2563eb"; C_BTN2 = "#334155"; C_WARN = "#f59e0b"

# ── Frases que rotan mientras se instala ──────────────────────────────────────
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
    ("👥", "Manejo de múltiples cajeros con contraseñas individuales"),
    ("🚀", "Funciona sin internet — ideal para negocios con conexión inestable"),
    ("📋", "Exportá tus reportes a Excel con un clic"),
    ("🎯", "Diseñado para carnicerías, verdulerías, kioscos y más"),
    ("⭐", "Soporte técnico incluido — estamos para ayudarte"),
]


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
        self.title(f"{APP_NAME} — Instalador v{VERSION}")
        self.geometry("540x480")
        self.resizable(False, False)
        self.configure(bg=C_BG)
        self.eval("tk::PlaceWindow . center")
        self._frase_idx = 0
        self._instalando = False
        self._ui()
        self._iniciar_rotacion_frases()

    # ── UI ────────────────────────────────────────────────────────────────────
    def _ui(self):
        # Header
        hdr = tk.Frame(self, bg=C_ACC, height=80)
        hdr.pack(fill="x"); hdr.pack_propagate(False)
        tk.Label(hdr, text="🏆", font=("Segoe UI Emoji", 32),
                 bg=C_ACC, fg="white").pack(side="left", padx=18, pady=14)
        fr = tk.Frame(hdr, bg=C_ACC); fr.pack(side="left", pady=14)
        tk.Label(fr, text="CajaFácil Pro", font=("Segoe UI", 22, "bold"),
                 bg=C_ACC, fg="white").pack(anchor="w")
        tk.Label(fr, text="Vendé rápido · Sin experiencia · Sin complicaciones",
                 font=("Segoe UI", 9), bg=C_ACC, fg="#bfdbfe").pack(anchor="w")

        # Card principal
        card = tk.Frame(self, bg=C_CARD)
        card.pack(fill="both", expand=True, padx=22, pady=12)

        # Destino
        tk.Label(card, text="Se instalará en:", font=("Segoe UI", 9),
                 bg=C_CARD, fg=C_SUB).pack(anchor="w", padx=18, pady=(14, 1))
        tk.Label(card, text=DESTINO, font=("Consolas", 11, "bold"),
                 bg=C_CARD, fg=C_TXT).pack(anchor="w", padx=18)

        # Check list
        checks = tk.Frame(card, bg="#172033"); checks.pack(fill="x", padx=18, pady=10)
        for txt in ["Descarga automática desde internet",
                     "Python 3.11 se instala si no está",
                     "Acceso directo en el Escritorio",
                     "Windows 8 / 10 / 11  (64 bits)"]:
            row = tk.Frame(checks, bg="#172033"); row.pack(fill="x", padx=10, pady=1)
            tk.Label(row, text="✓", font=("Segoe UI", 9), bg="#172033", fg=C_OK).pack(side="left")
            tk.Label(row, text=f"  {txt}", font=("Segoe UI", 9),
                     bg="#172033", fg=C_TXT).pack(side="left")

        # Separador
        tk.Frame(card, bg="#2d3f55", height=1).pack(fill="x", padx=18, pady=(6, 0))

        # ── Zona de frases animadas ───────────────────────────────────────────
        frase_frame = tk.Frame(card, bg="#0d1b2e", height=62)
        frase_frame.pack(fill="x", padx=18, pady=8)
        frase_frame.pack_propagate(False)

        self.lbl_frase_icon = tk.Label(frase_frame, text="💡", font=("Segoe UI Emoji", 18),
                                        bg="#0d1b2e", fg=C_WARN)
        self.lbl_frase_icon.place(x=12, y=10)

        self.lbl_frase = tk.Label(frase_frame, text="",
                                   font=("Segoe UI", 10), bg="#0d1b2e", fg="#cbd5e1",
                                   wraplength=430, justify="left")
        self.lbl_frase.place(x=44, y=8, width=470, height=46)

        # ── Barra de progreso + estado ────────────────────────────────────────
        self.lbl_status = tk.Label(card, text="Listo para instalar",
                                    font=("Segoe UI", 10), bg=C_CARD, fg=C_SUB)
        self.lbl_status.pack(anchor="w", padx=18, pady=(2, 3))

        style = ttk.Style(); style.theme_use("default")
        style.configure("A.Horizontal.TProgressbar", background=C_ACC,
                         troughcolor="#334155", borderwidth=0, relief="flat")
        self.bar = ttk.Progressbar(card, style="A.Horizontal.TProgressbar",
                                    mode="determinate", length=496)
        self.bar.pack(padx=18, pady=(0, 12))

        # Botones
        bf = tk.Frame(card, bg=C_CARD); bf.pack(fill="x", padx=18, pady=(0, 14))
        self.btn = tk.Button(bf, text="  ⚡  INSTALAR AHORA  ",
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

        tk.Label(self, text=f"v{VERSION}  ·  Windows 8 / 10 / 11",
                 font=("Segoe UI", 8), bg=C_BG, fg="#475569").pack(pady=(0, 6))

    # ── Rotación de frases ────────────────────────────────────────────────────
    def _iniciar_rotacion_frases(self):
        self._mostrar_frase()

    def _mostrar_frase(self):
        icon, texto = FRASES[self._frase_idx % len(FRASES)]
        # Fade out
        self.lbl_frase.config(fg="#0d1b2e")
        self.lbl_frase_icon.config(text=icon)
        self.after(150, lambda: self._fade_in_frase(texto))

    def _fade_in_frase(self, texto):
        self.lbl_frase.config(text=texto, fg="#cbd5e1")
        self._frase_idx += 1
        # Siguiente frase cada 4 segundos (más tiempo para leer)
        delay = 4000 if not self._instalando else 5000
        self.after(delay, self._mostrar_frase)

    # ── Estado y progreso ─────────────────────────────────────────────────────
    def status(self, msg, pct=None):
        def _u():
            self.lbl_status.config(text=msg)
            if pct is not None:
                self.bar["value"] = pct
        self.after(0, _u)

    # ── Inicio de instalación ─────────────────────────────────────────────────
    def start(self):
        if not is_admin():
            if not messagebox.askyesno("Permisos",
                "Se recomienda ejecutar como Administrador.\n¿Continuar de todas formas?"):
                return
        self._instalando = True
        self.btn.config(state="disabled", text="  ⏳  Instalando...  ")
        self.btn_x.config(state="disabled")
        threading.Thread(target=self._run, daemon=True).start()

    # ── Proceso de instalación ────────────────────────────────────────────────
    def _run(self):
        tmp = None
        try:
            tmp = tempfile.mkdtemp(prefix="cajafacil_")
            zip_path = os.path.join(tmp, "app.zip")

            # 1. Descargar
            self.status("Conectando con GitHub...", 3)
            def prog(done, total):
                self.status(f"Descargando CajaFácil Pro... {int(done/total*100)}%",
                             int(4 + 38 * done / total))
            download(DOWNLOAD_URL, zip_path, prog)
            self.status("✓ Descarga completa", 44)

            # 2. Extraer
            self.status("Descomprimiendo archivos...", 48)
            with zipfile.ZipFile(zip_path, "r") as zf:
                zf.extractall(tmp)
            src = tmp
            for d in os.listdir(tmp):
                full = os.path.join(tmp, d)
                if os.path.isdir(full) and d != "__MACOSX":
                    src = full; break

            # 3. Copiar al destino
            self.status("Instalando archivos del sistema...", 52)
            os.makedirs(DESTINO, exist_ok=True)
            for item in ["src", "main.py", "version.json", "requirements_core.txt",
                          "requirements_full.txt", "CajaFacil_Pro.bat", "ACTUALIZAR.bat"]:
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
            self.status("✓ Archivos copiados", 57)

            # 4. Python
            self.status("Verificando Python...", 60)
            py = find_python()
            if not py:
                self.status("Descargando Python 3.11 (puede tardar)...", 61)
                py_inst = os.path.join(tmp, "python_setup.exe")
                download(PYTHON_URL, py_inst)
                self.status("Instalando Python 3.11...", 65)
                subprocess.run([py_inst, "/quiet", "InstallAllUsers=1",
                                 "PrependPath=1", "Include_pip=1"],
                               check=True, timeout=180)
                py = "python"
            self.status("✓ Python listo", 68)

            # 5. Entorno virtual
            self.status("Creando entorno de ejecución...", 70)
            venv = os.path.join(DESTINO, ".venv")
            if not os.path.exists(os.path.join(venv, "Scripts", "python.exe")):
                subprocess.run([py, "-m", "venv", venv],
                               check=True, capture_output=True, timeout=60)
            self.status("✓ Entorno creado", 73)

            # 6. Dependencias esenciales
            pip = os.path.join(venv, "Scripts", "pip.exe")
            req = os.path.join(DESTINO, "requirements_core.txt")
            self.status("Actualizando gestor de paquetes...", 74)
            subprocess.run([pip, "install", "-q", "--upgrade", "pip"],
                           capture_output=True, timeout=60)
            self.status("Instalando motor de interfaz (PyQt5)...", 76)
            subprocess.run([pip, "install", "-q", "PyQt5"],
                           capture_output=True, timeout=180)
            self.status("Instalando módulo de imágenes...", 85)
            subprocess.run([pip, "install", "-q", "pillow", "requests"],
                           capture_output=True, timeout=120)
            self.status("✓ Módulos esenciales instalados", 90)

            # 7. Limpiar config
            try:
                cfg = os.path.join(DESTINO, "config.json")
                with open(cfg, encoding="utf-8") as f: d2 = json.load(f)
                d2["db_path"] = ""
                with open(cfg, "w", encoding="utf-8") as f:
                    json.dump(d2, f, indent=4, ensure_ascii=False)
            except: pass

            # 8. Acceso directo
            self.status("Creando acceso directo en el escritorio...", 93)
            desk = os.path.join(os.path.expanduser("~"), "Desktop")
            make_shortcut(
                os.path.join(desk, "CajaFacil Pro.lnk"),
                os.path.join(DESTINO, "CajaFacil_Pro.bat"),
                DESTINO
            )

            # 9. Limpiar temporales
            self.status("Limpiando archivos temporales...", 97)
            shutil.rmtree(tmp, ignore_errors=True)

            self.status("✅  ¡Listo! CajaFácil Pro instalado", 100)
            self.after(0, self._ok)

        except Exception as e:
            if tmp: shutil.rmtree(tmp, ignore_errors=True)
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
                             "• Hacé doble clic en 'CajaFacil Pro' del escritorio\n"
                             "• Los módulos adicionales se instalan solos al usar la app")

    def _err(self, e):
        self._instalando = False
        self.btn.config(state="normal", text="  ⚡  Reintentar  ")
        self.btn_x.config(state="normal")
        self.status("❌ Error — revisá tu conexión a internet", 0)
        messagebox.showerror("Error en la instalación",
                              f"Ocurrió un error:\n\n{e}\n\n"
                              "Verificá tu conexión e intentá de nuevo.")

    def _open(self):
        bat = os.path.join(DESTINO, "CajaFacil_Pro.bat")
        if os.path.exists(bat):
            subprocess.Popen(["cmd", "/c", bat], cwd=DESTINO)
        self.destroy()


if __name__ == "__main__":
    Installer().mainloop()
