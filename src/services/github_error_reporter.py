"""
Reporte automático de errores a GitHub Issues (repo cobrofacil-releases).

Token (uno de estos):
  - Variable de entorno COBROFACIL_GITHUB_TOKEN
  - config.json → github_report_token
  - error_report.json en la carpeta de instalación (inyectado en CI)

Labels:
  - auto-report, client-error (siempre)
  - needs-auto-fix (si no fue curado en runtime)
  - auto-healed (solo log local; no se abre issue si healed)
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import socket
import threading
import traceback
import urllib.error
import urllib.request
from datetime import datetime, timezone

from src.utils.paths import get_base_path

_DEFAULT_REPO = "cesarmaciel1234/cobrofacil-releases"
_QUEUE_FILE = "github_error_queue.json"
_STATE_FILE = "github_report_state.json"
_DEBOUNCE_HOURS = 6
_MAX_BODY = 12000
_MAX_LOG_LINES = 80

_lock = threading.Lock()
_flush_scheduled = False


def _log_dir() -> str:
    path = os.path.join(get_base_path(), "logs")
    os.makedirs(path, exist_ok=True)
    return path


def _queue_path() -> str:
    return os.path.join(_log_dir(), _QUEUE_FILE)


def _state_path() -> str:
    return os.path.join(_log_dir(), _STATE_FILE)


def _load_json(path: str, default):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return default


def _save_json(path: str, data) -> None:
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except OSError:
        pass


def _report_settings() -> tuple[bool, str, str]:
    """(activo, token, repo_slug)"""
    try:
        from src.config import config

        enabled = bool(config.get("github_error_report", True))
        token = str(config.get("github_report_token", "") or "").strip()
        repo = str(config.get("github_report_repo", _DEFAULT_REPO) or _DEFAULT_REPO).strip()
    except Exception:
        enabled = True
        token = ""
        repo = _DEFAULT_REPO

    token = token or os.environ.get("COBROFACIL_GITHUB_TOKEN", "").strip()

    cfg_path = os.path.join(get_base_path(), "error_report.json")
    file_cfg = _load_json(cfg_path, {})
    if isinstance(file_cfg, dict):
        token = token or str(file_cfg.get("token", "") or "").strip()
        repo = str(file_cfg.get("repo", repo) or repo).strip()

    return enabled, token, repo


def _fingerprint(message: str, source: str) -> str:
    raw = f"{source}|{message[:500]}"
    return hashlib.sha256(raw.encode("utf-8", errors="replace")).hexdigest()[:16]


def _recently_sent(fp: str) -> bool:
    state = _load_json(_state_path(), {})
    sent_at = state.get(fp)
    if not sent_at:
        return False
    try:
        dt = datetime.fromisoformat(sent_at)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        age_h = (datetime.now(timezone.utc) - dt).total_seconds() / 3600
        return age_h < _DEBOUNCE_HOURS
    except (TypeError, ValueError):
        return False


def _mark_sent(fp: str) -> None:
    state = _load_json(_state_path(), {})
    state[fp] = datetime.now(timezone.utc).isoformat()
    if len(state) > 200:
        for key in list(state.keys())[:-200]:
            state.pop(key, None)
    _save_json(_state_path(), state)


def _tail_log_file() -> str:
    log_dir = _log_dir()
    try:
        files = sorted(
            (f for f in os.listdir(log_dir) if f.startswith("punpro_") and f.endswith(".log")),
            reverse=True,
        )
    except OSError:
        return ""
    if not files:
        return ""
    path = os.path.join(log_dir, files[0])
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            lines = f.readlines()
        return "".join(lines[-_MAX_LOG_LINES:])
    except OSError:
        return ""


def _app_version() -> str:
    try:
        path = os.path.join(get_base_path(), "version.json")
        with open(path, encoding="utf-8") as f:
            v_data = json.load(f)
            return str(v_data.get("app_version") or v_data.get("version", "10.3"))
    except (OSError, json.JSONDecodeError, TypeError):
        return "10.3"


def _build_body(entry: dict) -> str:
    parts = [
        "## Reporte automático Cobro Fácil POS",
        "",
        f"- **Fecha UTC:** {entry.get('ts', '')}",
        f"- **Equipo:** {entry.get('hostname', '')}",
        f"- **Versión:** {entry.get('version', '')}",
        f"- **Origen:** {entry.get('source', '')}",
        f"- **Nivel:** {entry.get('level', 'ERROR')}",
        f"- **Fingerprint:** `{entry.get('fp', '')}`",
        "",
        "### Mensaje",
        "```",
        str(entry.get("message", ""))[:4000],
        "```",
    ]
    if entry.get("traceback"):
        parts.extend(["", "### Traceback", "```", entry["traceback"][:4000], "```"])
    log_tail = entry.get("log_tail") or _tail_log_file()
    if log_tail:
        parts.extend(["", "### Últimas líneas del log", "```", log_tail[-4000:], "```"])
    # Marcador estable para dedup del workflow auto-fix
    parts.extend(["", f"<!-- autofix-fp:{entry.get('fp', '')} -->"])
    body = "\n".join(parts)
    return body[:_MAX_BODY]


def _ssl_contexts():
    """Primero CA normal / certifi; si falla (Windows limpio), sin verificar."""
    import ssl

    contexts = []
    try:
        import certifi

        contexts.append(ssl.create_default_context(cafile=certifi.where()))
    except Exception:
        contexts.append(ssl.create_default_context())
    try:
        from src.services.auto_heal import is_ssl_relax_enabled

        force_insecure = bool(is_ssl_relax_enabled())
    except Exception:
        force_insecure = False
    if force_insecure:
        insecure = ssl.create_default_context()
        insecure.check_hostname = False
        insecure.verify_mode = ssl.CERT_NONE
        return [insecure]
    insecure = ssl.create_default_context()
    insecure.check_hostname = False
    insecure.verify_mode = ssl.CERT_NONE
    contexts.append(insecure)
    return contexts


def _http_json(
    method: str,
    url: str,
    token: str,
    payload: dict | None = None,
    *,
    timeout: int = 25,
) -> tuple[int, bytes]:
    """(status, body). status 0 = error de red/SSL."""
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "User-Agent": "CobroFacil-POS-ErrorReporter",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if data is not None:
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, method=method, headers=headers)
    last_err: Exception | None = None
    for ctx in _ssl_contexts():
        try:
            with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
                return int(resp.status), resp.read()
        except urllib.error.HTTPError as e:
            return int(e.code), e.read()
        except Exception as e:
            last_err = e
            continue
    logging.getLogger("PunPro").warning(
        "GitHub error report: red/SSL (%s)", type(last_err).__name__ if last_err else "?"
    )
    return 0, b""


def _post_via_dispatch(token: str, repo: str, title: str, body: str, labels: list[str]) -> bool | str:
    """Fallback: Actions crea el Issue con GITHUB_TOKEN (workflow pos-client-error)."""
    # client_payload tiene límite práctico; recortar body
    payload = {
        "event_type": "pos-client-error",
        "client_payload": {
            "title": title[:200],
            "body": body[:65000],
            "labels": labels[:10],
        },
    }
    status, raw = _http_json(
        "POST",
        f"https://api.github.com/repos/{repo}/dispatches",
        token,
        payload,
    )
    if status in (204, 200):
        return True
    if status in (401, 403):
        logging.getLogger("PunPro").warning(
            "GitHub error report: dispatch HTTP %s (hace falta Contents:write o PAT classic repo)",
            status,
        )
        return "auth"
    logging.getLogger("PunPro").warning(
        "GitHub error report: dispatch HTTP %s %s",
        status,
        raw[:200].decode("utf-8", errors="replace"),
    )
    return False


def _post_issue(token: str, repo: str, title: str, body: str, labels: list[str]) -> bool | str:
    """True OK · False reintentable · 'auth' token/permisos (cortar flush)."""
    payload = {
        "title": title[:200],
        "body": body,
        "labels": labels,
    }
    status, raw = _http_json(
        "POST",
        f"https://api.github.com/repos/{repo}/issues",
        token,
        payload,
    )
    if 200 <= status < 300:
        return True
    # Labels inexistentes
    if status == 422 and "needs-auto-fix" in labels:
        return _post_issue(
            token,
            repo,
            title,
            body,
            [lb for lb in labels if lb in ("auto-report", "client-error")],
        )
    if status in (401, 403):
        logging.getLogger("PunPro").warning(
            "GitHub error report: issues HTTP %s — probando repository_dispatch",
            status,
        )
        return _post_via_dispatch(token, repo, title, body, labels)
    logging.getLogger("PunPro").warning(
        "GitHub error report: issues HTTP %s %s",
        status,
        raw[:200].decode("utf-8", errors="replace"),
    )
    return False


def _enqueue(entry: dict) -> None:
    with _lock:
        queue = _load_json(_queue_path(), [])
        if not isinstance(queue, list):
            queue = []
        queue.append(entry)
        if len(queue) > 50:
            queue = queue[-50:]
        _save_json(_queue_path(), queue)


def _schedule_flush() -> None:
    global _flush_scheduled
    with _lock:
        if _flush_scheduled:
            return
        _flush_scheduled = True

    def _run():
        global _flush_scheduled
        try:
            flush_pending_reports()
        finally:
            with _lock:
                _flush_scheduled = False

    threading.Thread(target=_run, name="GitHubErrorFlush", daemon=True).start()


def queue_error_report(
    message: str,
    *,
    level: str = "ERROR",
    source: str = "app",
    exc_info=None,
    log_tail: str | None = None,
    skip_heal: bool = False,
) -> None:
    """Encola un error para envío a GitHub (no bloquea la UI).

    Primero intenta autocura local; si se curó, no abre Issue.
    """
    enabled, token, _repo = _report_settings()
    if not enabled:
        return

    msg = str(message or "").strip()
    if not msg:
        return

    tb_text = ""
    exc_obj = None
    if exc_info:
        if exc_info is True:
            exc_info = None
        if isinstance(exc_info, tuple) and exc_info[0] is not None:
            tb_text = "".join(traceback.format_exception(*exc_info))
            exc_obj = exc_info[1]

    # Errores ya emitidos por reconectar_* no deben disparar auto_heal de MariaDB
    # (bucle: ERROR log → try_auto_heal → reconectar_mariadb → ERROR log → …).
    if not skip_heal:
        lower = msg.lower()
        if "reconectar_mariadb" in lower or "reconectar_local" in lower:
            skip_heal = True

    if not skip_heal:
        try:
            from src.services.auto_heal import try_auto_heal

            heal = try_auto_heal(msg, exc=exc_obj, traceback_text=tb_text)
            if heal.healed:
                logging.getLogger("PunPro").warning(
                    "Error curado en runtime (%s): %s — no se reporta a GitHub",
                    heal.action,
                    msg[:200],
                )
                return
        except Exception:
            pass

    entry = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "hostname": socket.gethostname(),
        "version": _app_version(),
        "source": source,
        "level": level,
        "message": msg,
        "traceback": tb_text,
        "log_tail": log_tail,
        "fp": _fingerprint(msg, source),
        "labels": ["auto-report", "client-error", "needs-auto-fix"],
    }
    _enqueue(entry)

    if token:
        _schedule_flush()
    else:
        # Cola crece pero nunca sale: sin error_report.json / secret en el .exe
        logging.getLogger("PunPro").warning(
            "GitHub error report: error encolado pero NO hay token "
            "(falta error_report.json o secret COBROFACIL_ERROR_REPORT_TOKEN en el release)."
        )


def flush_pending_reports() -> int:
    """Envía la cola pendiente. Devuelve cantidad enviada."""
    enabled, token, repo = _report_settings()
    if not enabled:
        return 0
    if not token:
        try:
            queue = _load_json(_queue_path(), [])
            n = len(queue) if isinstance(queue, list) else 0
        except Exception:
            n = 0
        if n:
            logging.getLogger("PunPro").warning(
                "GitHub error report: %s errores en cola local sin token — no llegan a GitHub.",
                n,
            )
        return 0

    with _lock:
        queue = _load_json(_queue_path(), [])
        if not isinstance(queue, list) or not queue:
            return 0

    sent = 0
    remaining = []
    for entry in queue:
        if not isinstance(entry, dict):
            continue
        fp = entry.get("fp") or _fingerprint(str(entry.get("message", "")), str(entry.get("source", "")))
        if _recently_sent(fp):
            continue

        title = f"[POS {entry.get('level', 'ERROR')}] {entry.get('hostname', '?')} — {str(entry.get('message', ''))[:80]}"
        body = _build_body(entry)
        labels = list(entry.get("labels") or ["auto-report", "client-error", "needs-auto-fix"])
        result = _post_issue(token, repo, title, body, labels)
        if result is True:
            _mark_sent(fp)
            sent += 1
        elif result == "auth":
            # Token sin permisos: no martillar la API con toda la cola
            remaining.append(entry)
            remaining.extend(
                e for e in queue[queue.index(entry) + 1 :] if isinstance(e, dict)
            )
            break
        else:
            remaining.append(entry)

    with _lock:
        _save_json(_queue_path(), remaining)

    return sent


class GitHubReportHandler(logging.Handler):
    """Handler de logging: encola ERROR/CRITICAL para GitHub."""

    def emit(self, record: logging.LogRecord) -> None:
        if record.levelno < logging.ERROR:
            return
        # Evitar bucle si el propio heal/reporter loguea WARNING/ERROR
        if record.name.startswith("PunPro.auto_heal"):
            return
        try:
            msg = self.format(record)
            queue_error_report(
                msg,
                level=record.levelname,
                source=record.name,
                exc_info=record.exc_info,
            )
        except Exception:
            pass


def install_github_error_handler(logger: logging.Logger | None = None) -> None:
    """Registra el handler en el logger principal (idempotente)."""
    target = logger or logging.getLogger("PunPro")
    for h in target.handlers:
        if isinstance(h, GitHubReportHandler):
            return
    handler = GitHubReportHandler()
    handler.setLevel(logging.ERROR)
    target.addHandler(handler)
