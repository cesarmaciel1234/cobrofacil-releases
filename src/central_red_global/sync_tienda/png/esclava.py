"""Esclava: baja PNG de la maestra y sube los que se editan acá."""

from __future__ import annotations

import json
import logging
import os
import urllib.error

from src.central_red_global.sync_tienda.rol import (
    es_esclava,
    es_esta_pc,
    host_maestra,
    pedir_a_maestra,
    url_maestra,
)

logger = logging.getLogger("PunPro")


def _aviso_red(host: str, exc: Exception) -> str:
    if isinstance(exc, urllib.error.HTTPError) and exc.code == 401:
        return (
            "El PNG quedó en esta PC. No se copió a la maestra (clave de red). "
            "La TV de acá ya lo puede mostrar."
        )
    return (
        f"El PNG quedó en esta PC. No se copió a la maestra ({host}). "
        "La TV de acá ya lo puede mostrar."
    )


def enviar_png_a_maestra(filename: str) -> tuple[bool, str]:
    if not es_esclava():
        return True, ""
    host = host_maestra()
    if not host or es_esta_pc(host):
        return True, ""
    from src.config import config
    if not str(config.token_api_lan() or "").strip():
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
    try:
        with pedir_a_maestra(
            url_maestra("/api/carteleria/upload_png", host),
            data=body,
            method="POST",
            extra={"Content-Type": f"multipart/form-data; boundary={boundary}"},
            timeout=12,
        ) as resp:
            if resp.status == 200:
                logger.info("PNG enviado a maestra: %s", name)
                try:
                    from src.central_red_global.sync_tienda.aviso_tv import avisar_datos_nuevos

                    avisar_datos_nuevos()
                except Exception:
                    pass
                return True, "También quedó en la maestra."
            return False, (
                f"El PNG quedó en esta PC. No se copió a la maestra ({host}). "
                "La TV de acá ya lo puede mostrar."
            )
    except Exception as exc:
        logger.warning("No se pudo enviar PNG %s a %s: %s", name, host, exc)
        return False, _aviso_red(host, exc)


def _listar_png_maestra(host: str) -> list[dict]:
    with pedir_a_maestra(url_maestra("/api/carteleria/png_list", host), timeout=8) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    return list(data.get("files") or [])


def _bajar_bytes(urls: list[str]) -> bytes:
    last = b""
    for url in urls:
        try:
            with pedir_a_maestra(url, timeout=20) as resp:
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
    if not host or es_esta_pc(host):
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
