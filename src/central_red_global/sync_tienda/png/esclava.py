"""Esclava: baja PNG de la maestra y sube los que se editan acá."""

from __future__ import annotations

import json
import logging
import os
import urllib.request

from src.central_red_global.sync_tienda.rol import es_esclava, host_maestra, url_maestra

logger = logging.getLogger("PunPro")


def enviar_png_a_maestra(filename: str) -> tuple[bool, str]:
    if not es_esclava():
        return True, ""
    host = host_maestra()
    if not host:
        return True, ""
    from src.carteleria.assets_paths import ruta_archivo_icono

    name = os.path.basename(str(filename or "").strip())
    if not name:
        return False, "Sin nombre de PNG."
    fpath = ruta_archivo_icono(name)
    if not fpath or not os.path.isfile(fpath):
        return False, "No se encontró el PNG local para enviar."

    boundary = "----PunProPngBoundary"
    with open(fpath, "rb") as fh:
        raw = fh.read()
    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="file"; filename="{name}"\r\n'
        "Content-Type: image/png\r\n\r\n"
    ).encode("utf-8") + raw + f"\r\n--{boundary}--\r\n".encode("utf-8")
    req = urllib.request.Request(
        url_maestra("/api/carteleria/upload_png", host),
        data=body,
        method="POST",
        headers={
            "Content-Type": f"multipart/form-data; boundary={boundary}",
            "User-Agent": "CobroFacil-Esclava",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=12) as resp:
            if resp.status == 200:
                logger.info("PNG enviado a maestra: %s", name)
                return True, f"PNG copiado a la maestra ({host})."
            return False, f"HTTP {resp.status} al enviar PNG"
    except Exception as exc:
        logger.warning("No se pudo enviar PNG %s a %s: %s", name, host, exc)
        return False, str(exc)


def _listar_png_maestra(host: str) -> list[dict]:
    req = urllib.request.Request(
        url_maestra("/api/carteleria/png_list", host),
        headers={"User-Agent": "CobroFacil-Esclava"},
    )
    with urllib.request.urlopen(req, timeout=8) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    return list(data.get("files") or [])


def _bajar_bytes(urls: list[str]) -> bytes:
    last = b""
    for url in urls:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "CobroFacil-Esclava"})
            with urllib.request.urlopen(req, timeout=20) as resp:
                payload = resp.read()
            if payload and not payload.lstrip().startswith(b"{") and not payload.lstrip().startswith(b"<"):
                return payload
            last = payload
        except Exception:
            continue
    return last if last and last[:1] not in (b"{", b"<") else b""


def _bajar_archivo(host: str, name: str, dest: str) -> bool:
    from urllib.parse import quote

    q = quote(name)
    payload = _bajar_bytes([
        url_maestra("/api/carteleria/png/" + q, host),
        f"http://{host}:5000/carteleria/{q}",
        f"http://{host}:5055/carteleria/{q}",
    ])
    if not payload:
        return False
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    tmp = dest + ".part"
    with open(tmp, "wb") as fh:
        fh.write(payload)
    os.replace(tmp, dest)
    return True


def bajar_pngs_de_maestra(solo_nombres: list[str] | None = None) -> int:
    """Pisa PNG locales con los de la maestra. Devuelve cuántos archivos bajó."""
    if not es_esclava():
        return 0
    host = host_maestra()
    if not host:
        return 0
    from src.carteleria.assets_paths import png_productos_dir

    dest_dir = png_productos_dir()
    remotos = []
    try:
        remotos = _listar_png_maestra(host)
    except Exception as exc:
        logger.warning("No se pudo listar PNG de la maestra %s: %s", host, exc)

    extras = []
    wanted = None
    if solo_nombres:
        extras = [os.path.basename(str(n or "").strip()) for n in solo_nombres if n]
        if not remotos:
            wanted = {n.lower() for n in extras}

    items = list(remotos)
    for extra in extras:
        key = extra.lower()
        if extra and key not in {os.path.basename(str(i.get("name") or "")).lower() for i in items}:
            items.append({"name": extra, "size": 0, "mtime": 0})

    bajados = 0
    for item in items:
        name = os.path.basename(str(item.get("name") or "").strip())
        if not name:
            continue
        if wanted is not None and name.lower() not in wanted:
            continue
        dest = os.path.join(dest_dir, name)
        size = int(item.get("size") or 0)
        mtime = float(item.get("mtime") or 0)
        if size > 0 and os.path.isfile(dest):
            st = os.stat(dest)
            if int(st.st_size) == size and abs(st.st_mtime - mtime) < 2:
                continue
        try:
            if _bajar_archivo(host, name, dest):
                try:
                    os.utime(dest, (mtime, mtime))
                except OSError:
                    pass
                bajados += 1
        except Exception as exc:
            logger.debug("PNG %s no bajó: %s", name, exc)
    if bajados:
        try:
            from src.carteleria.motor_carteleria import iconos_tv

            iconos_tv._png_nombre_cache.clear()
            iconos_tv._png_indice_cache = None
        except Exception:
            pass
        logger.info("Esclava: %s PNG pisados desde la maestra %s", bajados, host)
    return bajados
