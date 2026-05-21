"""
error_reporter.py — Recopilador automático de errores hacia GitHub Issues
=========================================================================
Cuando la app crashea, envía un reporte automático como Issue en GitHub.
El desarrollador ve todos los errores de todos los clientes en un solo lugar.

Configurar: poner el GITHUB_TOKEN abajo (token con permiso issues:write)
"""

import os
import sys
import json
import socket
import platform
import traceback
import urllib.request
import urllib.error
import ssl
import logging
from datetime import datetime

# ── Config ────────────────────────────────────────────────────────────────────
GITHUB_REPO  = "cesarmaciel1234/cajafacil-pro"
GITHUB_TOKEN = ""   # <-- completar con tu Personal Access Token
ISSUES_URL   = f"https://api.github.com/repos/{GITHUB_REPO}/issues"

BASE_DIR     = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
VERSION_FILE = os.path.join(BASE_DIR, "version.json")
CRASH_LOG    = os.path.join(BASE_DIR, "crash.log")

# Etiqueta para los issues de error
LABEL_BUG    = "bug"
LABEL_AUTO   = "auto-reportado"


def _get_version() -> str:
    try:
        with open(VERSION_FILE, encoding='utf-8') as f:
            return json.load(f).get("app_version", "?")
    except:
        return "?"


def _get_hostname() -> str:
    """Nombre de PC anonimizado para identificar el origen sin exponer datos."""
    try:
        h = socket.gethostname()
        # Solo primeros 6 chars para no exponer nombre completo
        return h[:6] + "***"
    except:
        return "PC-???"


def _leer_crash_log(max_lines: int = 30) -> str:
    """Lee las últimas líneas del crash.log para incluirlas en el reporte."""
    try:
        if os.path.exists(CRASH_LOG):
            with open(CRASH_LOG, encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
            return "".join(lines[-max_lines:])
    except:
        pass
    return "(no disponible)"


def _ya_reportado(titulo: str) -> bool:
    """
    Verifica si ya existe un Issue abierto con el mismo título
    para evitar duplicados cuando el mismo error se repite.
    """
    if not GITHUB_TOKEN:
        return False
    try:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        url = f"{ISSUES_URL}?state=open&per_page=20"
        req = urllib.request.Request(url, headers={
            "Authorization": f"token {GITHUB_TOKEN}",
            "Accept": "application/vnd.github+json",
            "User-Agent": "CajaFacilPro-ErrorReporter"
        })
        with urllib.request.urlopen(req, timeout=5, context=ctx) as r:
            issues = json.loads(r.read().decode())
        for issue in issues:
            if issue.get("title", "") == titulo:
                return True
    except:
        pass
    return False


def reportar_error(
    exc_type,
    exc_value,
    exc_tb,
    contexto_extra: str = ""
) -> bool:
    """
    Envía un reporte de error como Issue a GitHub.
    Retorna True si se envió correctamente.
    """
    if not GITHUB_TOKEN:
        logging.debug("[ERROR-REPORTER] Sin token configurado, no se reporta.")
        return False

    try:
        # Formatear traceback
        tb_lines = traceback.format_exception(exc_type, exc_value, exc_tb)
        tb_str   = "".join(tb_lines)

        # Título del issue (tipo de error + archivo)
        error_tipo = exc_type.__name__ if exc_type else "Error"
        # Extraer archivo del traceback
        archivo = "?"
        for line in reversed(tb_lines):
            if "File " in line and ".py" in line:
                try:
                    archivo = line.strip().split('"')[1].split("\\")[-1]
                except:
                    pass
                break

        titulo = f"[AUTO] {error_tipo} en {archivo}"

        # Evitar duplicados
        if _ya_reportado(titulo):
            logging.debug(f"[ERROR-REPORTER] Issue ya existe: {titulo}")
            return False

        # Cuerpo del issue
        version  = _get_version()
        hostname = _get_hostname()
        fecha    = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        so       = f"{platform.system()} {platform.release()} ({platform.machine()})"
        py_ver   = sys.version.split()[0]

        body = f"""## 🐛 Error automático detectado

| Campo | Valor |
|-------|-------|
| **Versión app** | `{version}` |
| **Fecha/Hora** | `{fecha}` |
| **PC origen** | `{hostname}` |
| **Sistema** | `{so}` |
| **Python** | `{py_ver}` |

## Traceback completo

```python
{tb_str}
```

## Contexto adicional

```
{contexto_extra if contexto_extra else 'Sin contexto extra'}
```

## Últimas líneas del crash.log

```
{_leer_crash_log()}
```

---
*Reporte generado automáticamente por CajaFácil Pro*
"""

        # Enviar a GitHub
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE

        payload = json.dumps({
            "title": titulo,
            "body": body,
            "labels": [LABEL_BUG, LABEL_AUTO]
        }).encode('utf-8')

        req = urllib.request.Request(
            ISSUES_URL,
            data=payload,
            method="POST",
            headers={
                "Authorization": f"token {GITHUB_TOKEN}",
                "Accept": "application/vnd.github+json",
                "Content-Type": "application/json",
                "User-Agent": "CajaFacilPro-ErrorReporter"
            }
        )

        with urllib.request.urlopen(req, timeout=8, context=ctx) as r:
            resp = json.loads(r.read().decode())
            issue_num = resp.get("number", "?")
            issue_url = resp.get("html_url", "")
            logging.info(f"[ERROR-REPORTER] Issue #{issue_num} creado: {issue_url}")
            return True

    except Exception as e:
        logging.debug(f"[ERROR-REPORTER] No se pudo reportar: {e}")
        return False


def instalar_hook_global():
    """
    Reemplaza sys.excepthook para capturar todos los errores no manejados
    y reportarlos a GitHub automáticamente.
    """
    original_hook = sys.excepthook

    def hook_con_reporte(exc_type, exc_value, exc_tb):
        # 1. Guardar crash.log (comportamiento original)
        try:
            original_hook(exc_type, exc_value, exc_tb)
        except:
            pass
        # 2. Reportar a GitHub en background (no bloquea la app)
        try:
            import threading
            t = threading.Thread(
                target=reportar_error,
                args=(exc_type, exc_value, exc_tb),
                daemon=True
            )
            t.start()
            t.join(timeout=10)  # Esperar máximo 10s
        except:
            pass

    sys.excepthook = hook_con_reporte
    logging.info("[ERROR-REPORTER] Hook global instalado - errores se reportan a GitHub")
