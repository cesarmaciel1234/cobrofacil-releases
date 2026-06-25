"""
Reporte automático de errores a GitHub Issues (repo cobrofacil-releases).

Token (uno de estos):
  - Variable de entorno COBROFACIL_GITHUB_TOKEN
  - config.json → github_report_token
  - error_report.json en la carpeta de instalación (inyectado en CI)
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
    # Mantener solo los últimos 200 hashes
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
            return str(json.load(f).get("version", "desconocida"))
    except (OSError, json.JSONDecodeError, TypeError):
        return "desconocida"


def _build_body(entry: dict) -> str:
    parts = [
        "## Reporte automático Cobro Fácil POS",
        "",
        f"- **Fecha UTC:** {entry.get('ts', '')}",
        f"- **Equipo:** {entry.get('hostname', '')}",
        f"- **Versión:** {entry.get('version', '')}",
        f"- **Origen:** {entry.get('source', '')}",
        f"- **Nivel:** {entry.get('level', 'ERROR')}",
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
    body = "\n".join(parts)
    return body[:_MAX_BODY]


def _post_issue(token: str, repo: str, title: str, body: str) -> bool:
    url = f"https://api.github.com/repos/{repo}/issues"
    payload = {
        "title": title[:200],
        "body": body,
        "labels": ["auto-report", "client-error"],
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        method="POST",
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "Content-Type": "application/json",
            "User-Agent": "CobroFacil-POS-ErrorReporter",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=25) as resp:
            return 200 <= resp.status < 300
    except urllib.error.HTTPError:
        return False
    except Exception:
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
) -> None:
    """Encola un error para envío a GitHub (no bloquea la UI)."""
    enabled, token, _repo = _report_settings()
    if not enabled:
        return

    msg = str(message or "").strip()
    if not msg:
        return

    tb_text = ""
    if exc_info:
        if exc_info is True:
            exc_info = None
        if isinstance(exc_info, tuple) and exc_info[0] is not None:
            tb_text = "".join(traceback.format_exception(*exc_info))

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
    }
    _enqueue(entry)

    if token:
        _schedule_flush()


def flush_pending_reports() -> int:
    """Envía la cola pendiente. Devuelve cantidad enviada."""
    enabled, token, repo = _report_settings()
    if not enabled or not token:
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
        if _post_issue(token, repo, title, body):
            _mark_sent(fp)
            sent += 1
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
