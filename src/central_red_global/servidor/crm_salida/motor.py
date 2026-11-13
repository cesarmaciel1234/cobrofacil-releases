"""Lee punpro.db y lo manda al CRM. Este módulo no importa Qt."""

from __future__ import annotations

import hashlib
import http.cookiejar
import json
import os
import re
import sqlite3
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

_TABLA = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
_SECRETOS = ("password", "passwd", "token", "secret", "api_key", "access_token", "refresh_token")
_TAMANO_PARTE = 150

COLUMNAS = (
    "id",
    "uid",
    "nombre",
    "telefono",
    "dni",
    "direccion",
    "limite_credito",
    "deuda_actual",
    "tipo_cliente",
    "estado_cuenta",
    "actualizado_en",
    "plazo_dias",
)


def leer_clientes(ruta_db: str) -> list[dict]:
    conn = sqlite3.connect(f"file:{ruta_db}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    try:
        tablas = {
            row[0]
            for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
        }
        if "clientes" not in tablas:
            raise RuntimeError(f"punpro.db no tiene clientes: {ruta_db}")
        existentes = {row[1] for row in conn.execute("PRAGMA table_info(clientes)")}
        cols = [c for c in COLUMNAS if c in existentes]
        if "nombre" not in cols:
            raise RuntimeError("La tabla clientes no tiene nombre")
        filas = conn.execute(
            f"SELECT {', '.join(cols)} FROM clientes ORDER BY nombre"
        ).fetchall()
    finally:
        conn.close()

    clientes = []
    for fila in filas:
        item = {col: fila[col] for col in cols}
        nombre = str(item.get("nombre") or "").strip()
        if not nombre:
            continue
        item["nombre"] = nombre
        for clave, valor in list(item.items()):
            if isinstance(valor, bytes):
                item[clave] = valor.decode("utf-8", errors="replace")
        clientes.append(item)
    return clientes


def huella(clientes: list[dict], marca: str = "") -> str:
    """Firma del lote. Si no cambia, no hace falta volver a mandarlo."""
    crudo = json.dumps(
        {"marca": marca, "clientes": clientes},
        ensure_ascii=False,
        sort_keys=True,
        default=str,
    )
    return hashlib.sha256(crudo.encode("utf-8")).hexdigest()


def manifiesto(ruta_db: str) -> str:
    """Firma de toda la base. Cambia si cambia cualquier tabla."""
    trozos = []
    for tabla, columnas, filas in leer_base(ruta_db):
        trozos.append(json.dumps(
            {"tabla": tabla, "columnas": columnas, "filas": filas},
            ensure_ascii=False,
            sort_keys=True,
            default=str,
        ))
    return hashlib.sha256("\n".join(trozos).encode("utf-8")).hexdigest()


def _plano(valor):
    if isinstance(valor, bytes):
        return valor.decode("utf-8", errors="replace")
    return valor


def _clave_secreta(texto: str) -> bool:
    n = texto.lower()
    return any(marca in n for marca in _SECRETOS)


def leer_base(ruta_db: str):
    """Todas las tablas, en orden. Las columnas de claves salen vacías."""
    conn = sqlite3.connect(f"file:{ruta_db}?mode=ro", uri=True)
    try:
        nombres = [
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
            )
        ]
        for nombre in nombres:
            if not _TABLA.match(nombre):
                continue
            columnas = [col[1] for col in conn.execute(f'PRAGMA table_info("{nombre}")')]
            crudas = conn.execute(f'SELECT * FROM "{nombre}"').fetchall()
            idx_clave = next((i for i, col in enumerate(columnas) if col.lower() in ("clave", "key", "nombre")), None)
            idx_valor = next((i for i, col in enumerate(columnas) if col.lower() in ("valor", "value")), None)
            filas = []
            for cruda in crudas:
                fila = [_plano(valor) for valor in cruda]
                for i, col in enumerate(columnas):
                    if _clave_secreta(col):
                        fila[i] = None
                if (
                    idx_clave is not None
                    and idx_valor is not None
                    and _clave_secreta(str(fila[idx_clave] or ""))
                ):
                    fila[idx_valor] = None
                filas.append(fila)
            if nombre == "configuracion" and idx_clave is not None and idx_valor is not None:
                presentes = {str(fila[idx_clave]) for fila in filas}
                try:
                    from src.config import config
                    politica = {
                        "fiado_mantenimiento_pct": config.get("fiado_mantenimiento_pct", 5),
                        "fiado_apalancamiento_pct": config.get("fiado_apalancamiento_pct", 5),
                        "fiado_plazo_dias": config.get("fiado_plazo_dias", 30),
                    }
                except Exception:
                    politica = {
                        "fiado_mantenimiento_pct": 5,
                        "fiado_apalancamiento_pct": 5,
                        "fiado_plazo_dias": 30,
                    }
                for clave, valor in politica.items():
                    if clave in presentes:
                        continue
                    extra = [None] * len(columnas)
                    extra[idx_clave] = clave
                    extra[idx_valor] = valor
                    filas.append(extra)
            yield nombre, columnas, filas
    finally:
        conn.close()


def _pedir(abridor, req, timeout: int, intentos: int = 4):
    """Reintenta si Render corta la conexión a mitad de una tabla."""
    ultimo = None
    for numero in range(intentos):
        try:
            with abridor(req, timeout=timeout) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            detalle = exc.read().decode("utf-8", errors="replace")
            if exc.code in (502, 503, 504) and numero + 1 < intentos:
                time.sleep(3 * (numero + 1))
                continue
            raise RuntimeError(detalle[:180]) from exc
        except (urllib.error.URLError, TimeoutError, ConnectionError, OSError) as exc:
            ultimo = exc
            if numero + 1 < intentos:
                time.sleep(3 * (numero + 1))
                continue
            raise
    raise ultimo


def subir_base(crm_url, api_key, ruta_db, empresa_id=None, sucursal_id=None, sucursal=None, opener=None, timeout=120, reentrar=None) -> dict:
    """Manda cada tabla en partes. La primera parte reemplaza la copia anterior."""
    abridor = opener.open if opener is not None else urllib.request.urlopen
    tablas_ok = 0
    filas = 0
    errores = []
    for tabla, columnas, todas in leer_base(ruta_db):
        print(f"tabla {tabla} {len(todas)}", file=sys.stderr, flush=True)
        partes = [todas[i:i + _TAMANO_PARTE] for i in range(0, len(todas), _TAMANO_PARTE)] or [[]]
        fallo = None
        for numero, bloque in enumerate(partes, start=1):
            cuerpo = {
                "tabla": tabla,
                "columnas": columnas,
                "filas": bloque,
                "parte": numero,
                "partes": len(partes),
            }
            if sucursal_id not in (None, ""):
                cuerpo["sucursal_id"] = int(sucursal_id)
            if sucursal:
                cuerpo["sucursal"] = sucursal
            headers = {"Content-Type": "application/json"}
            if api_key:
                headers["X-API-Key"] = api_key
            if empresa_id not in (None, ""):
                headers["X-Empresa-ID"] = str(empresa_id).strip()
            req = urllib.request.Request(
                f"{crm_url.rstrip('/')}/api/pos/base/tabla",
                data=json.dumps(cuerpo, default=str).encode("utf-8"),
                method="POST",
                headers=headers,
            )
            reintentos_sesion = 0
            while True:
                try:
                    dato = _pedir(abridor, req, timeout)
                    break
                except Exception as exc:
                    texto = str(exc)
                    sesion_vencida = "No autorizado" in texto or "expirada" in texto.lower()
                    if reentrar is not None and sesion_vencida and reintentos_sesion < 2:
                        reintentos_sesion += 1
                        print("sesion renovada", file=sys.stderr, flush=True)
                        nuevo = reentrar()
                        if nuevo is not None:
                            abridor = nuevo.open if hasattr(nuevo, "open") else nuevo
                        time.sleep(2)
                        continue
                    fallo = {"tabla": tabla, "parte": numero, "error": texto[:180]}
                    break
            if fallo:
                break
            if not dato.get("ok"):
                fallo = {"tabla": tabla, "parte": numero, "error": str(dato.get("error") or dato)}
                break
        if fallo:
            errores.append(fallo)
            continue
        tablas_ok += 1
        filas += len(todas)
    return {"tablas": tablas_ok, "filas": filas, "errores": errores}


def resolver_empresa(crm_url: str, api_key: str, nombre: str, timeout: int = 20) -> str:
    """El nombre de la empresa pasa a su número. El lote entra en esa cuenta."""
    consulta = urllib.parse.urlencode({"nombre": nombre})
    req = urllib.request.Request(
        f"{crm_url.rstrip('/')}/api/pos/empresas/resolver?{consulta}",
        method="GET",
        headers={"X-API-Key": api_key},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            dato = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detalle = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"No encontré la empresa {nombre}: {detalle}") from exc
    empresa_id = str(dato.get("id") or "").strip()
    if not empresa_id:
        raise RuntimeError(f"El CRM no devolvió el número de {nombre}")
    return empresa_id


def entrar(crm_url: str, usuario: str, password: str, timeout: int = 20):
    """Entra con la cuenta de la empresa y devuelve la sesión y su número."""
    jar = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
    cuerpo = json.dumps({"username": usuario, "password": password}).encode("utf-8")
    req = urllib.request.Request(
        f"{crm_url.rstrip('/')}/auth/login",
        data=cuerpo,
        method="POST",
        headers={"Content-Type": "application/json"},
    )
    try:
        with opener.open(req, timeout=timeout) as resp:
            dato = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detalle = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"No se pudo entrar: {detalle}") from exc
    if not dato.get("ok"):
        raise RuntimeError(str(dato.get("error") or "No se pudo entrar"))
    user = dato.get("user") or {}
    return opener, str(user.get("empresa_id") or "").strip()


def enviar(
    crm_url: str,
    api_key: str,
    clientes: list[dict],
    timeout: int = 120,
    empresa_id: str | None = None,
    sucursal_id: str | int | None = None,
    sucursal: str | None = None,
    opener=None,
) -> dict:
    cuerpo_obj: dict = {"clientes": clientes}
    if sucursal_id not in (None, ""):
        cuerpo_obj["sucursal_id"] = int(sucursal_id)
    if sucursal:
        cuerpo_obj["sucursal"] = sucursal
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["X-API-Key"] = api_key
    if empresa_id not in (None, ""):
        headers["X-Empresa-ID"] = str(empresa_id).strip()
    cuerpo = json.dumps(cuerpo_obj).encode("utf-8")
    req = urllib.request.Request(
        f"{crm_url.rstrip('/')}/api/pos/clientes/lote",
        data=cuerpo,
        method="POST",
        headers=headers,
    )
    try:
        abridor = opener.open if opener is not None else urllib.request.urlopen
        return _pedir(abridor, req, timeout)
    except RuntimeError as exc:
        raise RuntimeError(f"El CRM respondió {exc}") from exc


def main() -> int:
    url = (os.environ.get("CRM_URL") or "").strip().rstrip("/")
    clave = (os.environ.get("CRM_API_KEY") or "").strip()
    usuario = (os.environ.get("CRM_USER") or "").strip()
    password = os.environ.get("CRM_PASSWORD") or ""
    ruta = (os.environ.get("PUNPRO_DB") or "").strip()
    if not url or not ruta or not ((usuario and password) or clave):
        print(json.dumps({"ok": False, "error": "Faltan la cuenta de la empresa o la base"}))
        return 1
    if not os.path.isfile(ruta):
        print(json.dumps({"ok": False, "error": f"No está punpro.db en {ruta}"}))
        return 1
    empresa = (os.environ.get("CRM_EMPRESA_ID") or "").strip()
    nombre_empresa = (os.environ.get("CRM_EMPRESA") or "").strip()
    sucursal_id = (os.environ.get("CRM_SUCURSAL_ID") or "").strip()
    sucursal = (os.environ.get("CRM_SUCURSAL") or "").strip()
    opener = None
    try:
        if usuario and password:
            opener, empresa_login = entrar(url, usuario, password)
            if empresa_login:
                empresa = empresa_login
        elif nombre_empresa:
            empresa = resolver_empresa(url, clave, nombre_empresa)
        clientes = leer_clientes(ruta)
        resultado = enviar(
            url,
            clave,
            clientes,
            empresa_id=empresa or None,
            sucursal_id=sucursal_id or None,
            sucursal=sucursal or None,
            opener=opener,
        )
        def reentrar():
            nonlocal opener, empresa
            nuevo, empresa_login = entrar(url, usuario, password)
            opener = nuevo
            if empresa_login:
                empresa = empresa_login
            return nuevo

        base = subir_base(
            url,
            clave,
            ruta,
            empresa_id=empresa or None,
            sucursal_id=sucursal_id or None,
            sucursal=sucursal or None,
            opener=opener,
            reentrar=reentrar if usuario and password else None,
        )
    except Exception as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False))
        return 1
    if isinstance(resultado, dict):
        resultado.setdefault("ok", not base["errores"])
        resultado["leidos"] = len(clientes)
        resultado["tablas"] = base["tablas"]
        resultado["filas"] = base["filas"]
        resultado["errores_base"] = base["errores"]
    print(json.dumps(resultado, ensure_ascii=False))
    return 0 if not base["errores"] else 1
