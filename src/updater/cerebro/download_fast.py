"""Descarga rápida del ZIP de release (buffer grande + paralelismo por Range)."""

from __future__ import annotations

import http.client
import os
import threading
import time
import zipfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable

USER_AGENT = "CobroFacil-SilentUpdater/2026"
CHUNK = 1024 * 1024  # 1 MiB
PARALLEL = 6
MIN_PARALLEL_BYTES = 12 * 1024 * 1024  # solo si > 12 MB
CONNECT_TIMEOUT = 45
READ_TIMEOUT = 300  # ZIP ~300 MB en enlaces lentos (LATAM)
REQUEST_TIMEOUT = (CONNECT_TIMEOUT, READ_TIMEOUT)
STREAM_RETRIES = 3


def _is_transient_stream_error(exc: BaseException) -> bool:
    if isinstance(
        exc,
        (TimeoutError, ConnectionError, http.client.IncompleteRead),
    ):
        return True
    msg = str(exc).lower()
    if "incomplet" in msg or "connection broken" in msg:
        return True
    try:
        import requests

        if isinstance(
            exc,
            (
                requests.exceptions.Timeout,
                requests.exceptions.ConnectionError,
                requests.exceptions.ChunkedEncodingError,
            ),
        ):
            return True
    except Exception:
        pass
    try:
        from urllib3.exceptions import ProtocolError

        if isinstance(exc, ProtocolError):
            return True
    except Exception:
        pass
    return False


def _verify_ssl() -> bool:
    try:
        from src.services.auto_heal import is_ssl_relax_enabled

        return not bool(is_ssl_relax_enabled())
    except Exception:
        return True


def _session():
    import requests

    s = requests.Session()
    s.headers.update({"User-Agent": USER_AGENT})
    # Keep-Alive reutiliza TCP (mucho más rápido en LATAM → GitHub)
    s.headers.update({"Connection": "keep-alive", "Accept-Encoding": "identity"})
    return s


def _emit(cb: Callable | None, msg: str, pct: int | None = None) -> None:
    if not cb:
        return
    try:
        if pct is None:
            cb(msg)
        else:
            cb(int(pct), msg)
    except TypeError:
        try:
            cb(msg)
        except Exception:
            pass
    except Exception:
        pass


def download_release_zip(
    url: str,
    dest_path: str,
    progress_callback=None,
    *,
    force_single: bool = False,
) -> None:
    """
    Descarga a dest_path. Usa Range paralelo si el CDN lo permite;
    si no, stream único con chunks de 1 MB + reanudación .part.
    """
    import requests

    os.makedirs(os.path.dirname(dest_path) or ".", exist_ok=True)
    part_path = dest_path + ".part"
    verify = _verify_ssl()
    session = _session()

    try:
        head = session.head(
            url, allow_redirects=True, timeout=REQUEST_TIMEOUT, verify=verify
        )
        head.raise_for_status()
    except Exception:
        # Algunos CDNs no permiten HEAD; seguir con GET
        head = None

    final_url = (head.url if head is not None else url) or url
    total = 0
    accept_ranges = ""
    if head is not None:
        total = int(head.headers.get("Content-Length") or 0)
        accept_ranges = str(head.headers.get("Accept-Ranges") or "").lower()

    use_parallel = (
        not force_single
        and total >= MIN_PARALLEL_BYTES
        and "bytes" in accept_ranges
    )

    if use_parallel:
        try:
            _download_parallel(
                final_url, dest_path, part_path, total, verify, progress_callback
            )
            _verify_downloaded_zip(dest_path)
            return
        except Exception as exc:
            _emit(progress_callback, f"Paralelo falló, modo único: {exc}", 0)
            _cleanup_partial_download(dest_path, part_path)

    _download_single(
        session, final_url, dest_path, part_path, total, verify, progress_callback
    )
    _verify_downloaded_zip(dest_path)


def _verify_downloaded_zip(dest_path: str) -> None:
    """Falla rápido si el ZIP local está truncado o con CRC inválido."""
    with zipfile.ZipFile(dest_path, "r") as zf:
        bad = zf.testzip()
        if bad:
            raise zipfile.BadZipFile(f"Bad CRC-32 for file '{bad}'")


def _cleanup_partial_download(dest_path: str, part_path: str) -> None:
    for path in (dest_path, part_path):
        try:
            if os.path.isfile(path):
                os.remove(path)
        except OSError:
            pass
    for i in range(PARALLEL + 1):
        p = f"{part_path}.{i}"
        try:
            if os.path.isfile(p):
                os.remove(p)
        except OSError:
            pass


def _download_single(session, url, dest_path, part_path, total_hint, verify, cb) -> None:
    last_exc: BaseException | None = None
    for attempt in range(STREAM_RETRIES):
        try:
            _download_single_stream(
                session, url, dest_path, part_path, total_hint, verify, cb
            )
            return
        except Exception as exc:
            last_exc = exc
            if attempt < STREAM_RETRIES - 1 and _is_transient_stream_error(exc):
                _emit(
                    cb,
                    f"Conexión interrumpida, reanudando ({attempt + 2}/{STREAM_RETRIES})…",
                    1,
                )
                time.sleep(3 * (attempt + 1))
                continue
            raise
    if last_exc is not None:
        raise last_exc


def _download_single_stream(session, url, dest_path, part_path, total_hint, verify, cb) -> None:
    import requests

    existing = os.path.getsize(part_path) if os.path.isfile(part_path) else 0
    headers = {}
    mode = "wb"
    done = 0
    if existing > 0 and (total_hint <= 0 or existing < total_hint):
        headers["Range"] = f"bytes={existing}-"
        mode = "ab"
        done = existing
        _emit(cb, f"Reanudando descarga… {done / (1024*1024):.0f} MB", 1)

    with session.get(
        url, headers=headers, stream=True, timeout=REQUEST_TIMEOUT, verify=verify
    ) as resp:
        if resp.status_code == 416:
            # Ya completo
            if os.path.isfile(part_path):
                os.replace(part_path, dest_path)
            return
        resp.raise_for_status()
        # Si pedimos Range y el server ignora, reiniciar
        if existing > 0 and resp.status_code == 200:
            mode = "wb"
            done = 0
            existing = 0

        total = total_hint
        cl = resp.headers.get("Content-Length")
        if cl and resp.status_code == 206:
            total = existing + int(cl)
        elif cl and resp.status_code == 200:
            total = int(cl)

        last_pct = -1
        last_emit = done
        with open(part_path, mode) as out:
            for chunk in resp.iter_content(chunk_size=CHUNK):
                if not chunk:
                    continue
                out.write(chunk)
                done += len(chunk)
                if total > 0:
                    pct = min(95, int(done * 95 / total))
                    if pct != last_pct and (
                        pct - last_pct >= 2 or done - last_emit >= 2 * CHUNK
                    ):
                        last_pct = pct
                        last_emit = done
                        mb = done / (1024 * 1024)
                        total_mb = total / (1024 * 1024)
                        _emit(cb, f"Descargando… {mb:.0f}/{total_mb:.0f} MB ({pct}%)", pct)
                elif done - last_emit >= 2 * CHUNK:
                    last_emit = done
                    mb = done / (1024 * 1024)
                    _emit(cb, f"Descargando… {mb:.0f} MB", min(90, int(mb)))

    os.replace(part_path, dest_path)


def _download_parallel(url, dest_path, part_path, total, verify, cb) -> None:
    n = PARALLEL
    # Limpiar restos
    for i in range(n):
        p = f"{part_path}.{i}"
        try:
            if os.path.isfile(p):
                os.remove(p)
        except OSError:
            pass

    size = total
    part_size = size // n
    ranges = []
    for i in range(n):
        start = i * part_size
        end = size - 1 if i == n - 1 else (start + part_size - 1)
        ranges.append((i, start, end))

    done_lock = threading.Lock()
    done = [0]
    last_pct = [-1]

    def worker(idx: int, start: int, end: int) -> str:
        import requests

        path = f"{part_path}.{idx}"
        headers = {"Range": f"bytes={start}-{end}"}
        expected = end - start + 1
        last_exc: BaseException | None = None
        for attempt in range(STREAM_RETRIES):
            try:
                if attempt > 0:
                    try:
                        if os.path.isfile(path):
                            os.remove(path)
                    except OSError:
                        pass
                # Session por hilo: requests.Session no es thread-safe.
                with _session().get(
                    url, headers=headers, stream=True, timeout=REQUEST_TIMEOUT, verify=verify
                ) as resp:
                    if resp.status_code not in (200, 206):
                        raise RuntimeError(f"Range HTTP {resp.status_code}")
                    with open(path, "wb") as out:
                        for chunk in resp.iter_content(chunk_size=CHUNK):
                            if not chunk:
                                continue
                            out.write(chunk)
                            with done_lock:
                                done[0] += len(chunk)
                                pct = min(95, int(done[0] * 95 / size))
                                if pct - last_pct[0] >= 2:
                                    last_pct[0] = pct
                                    mb = done[0] / (1024 * 1024)
                                    total_mb = size / (1024 * 1024)
                                    _emit(
                                        cb,
                                        f"Descarga rápida… {mb:.0f}/{total_mb:.0f} MB ({pct}%) · {n} hilos",
                                        pct,
                                    )
                actual = os.path.getsize(path) if os.path.isfile(path) else 0
                if actual != expected:
                    raise RuntimeError(
                        f"Shard incompleto: {actual} bytes recibidos, esperados {expected}"
                    )
                return path
            except Exception as exc:
                last_exc = exc
                if attempt < STREAM_RETRIES - 1 and _is_transient_stream_error(exc):
                    with done_lock:
                        try:
                            partial = os.path.getsize(path) if os.path.isfile(path) else 0
                            done[0] = max(0, done[0] - partial)
                        except OSError:
                            pass
                    time.sleep(2 * (attempt + 1))
                    continue
                raise
        if last_exc is not None:
            raise last_exc
        raise RuntimeError("Shard download failed")

    _emit(cb, f"Descarga rápida ({n} conexiones)…", 1)
    paths = [None] * n
    with ThreadPoolExecutor(max_workers=n) as pool:
        futs = {pool.submit(worker, i, s, e): i for i, s, e in ranges}
        for fut in as_completed(futs):
            idx = futs[fut]
            paths[idx] = fut.result()

    # Ensamblar
    _emit(cb, "Uniendo partes…", 96)
    with open(dest_path, "wb") as out:
        for i in range(n):
            p = paths[i] or f"{part_path}.{i}"
            with open(p, "rb") as inp:
                while True:
                    block = inp.read(CHUNK)
                    if not block:
                        break
                    out.write(block)
            try:
                os.remove(p)
            except OSError:
                pass

    try:
        if os.path.isfile(part_path):
            os.remove(part_path)
    except OSError:
        pass

    actual = os.path.getsize(dest_path)
    if actual != size:
        raise RuntimeError(
            f"Descarga incompleta: {actual} bytes recibidos, esperados {size}"
        )
