"""Resuelve la URL de descarga del ZIP desde GitHub Releases (API)."""

from __future__ import annotations

import json
import urllib.error
import urllib.request

GITHUB_REPO = "cesarmaciel1234/cobrofacil-releases"
RELEASE_ZIP_NAME = "CobroFacil_POS_Release.zip"
USER_AGENT = "CobroFacil-ReleaseResolver/2026"


def _pick_asset_url(release: dict) -> str | None:
    for asset in release.get("assets") or []:
        if asset.get("name") == RELEASE_ZIP_NAME:
            return str(asset.get("browser_download_url") or "").strip() or None
    return None


def _fetch_json(url: str, timeout: int = 30) -> dict | list | None:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "application/vnd.github+json",
        },
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def resolve_release_zip_url(timeout: int = 30) -> str | None:
    """
    Devuelve browser_download_url del asset CobroFacil_POS_Release.zip
    del release más reciente, o None si no hay release publicado.
    """
    base = f"https://api.github.com/repos/{GITHUB_REPO}/releases"
    try:
        latest = _fetch_json(f"{base}/latest", timeout=timeout)
        if isinstance(latest, dict):
            url = _pick_asset_url(latest)
            if url:
                return url
    except urllib.error.HTTPError as exc:
        if exc.code not in (404, 403):
            raise
    except Exception:
        pass

    try:
        releases = _fetch_json(f"{base}?per_page=10", timeout=timeout)
        if isinstance(releases, list):
            for release in releases:
                url = _pick_asset_url(release)
                if url:
                    return url
    except Exception:
        pass

    return None


def release_zip_url_or_fallback() -> str:
    """URL resuelta por API o patrón legacy (puede fallar si no hay release)."""
    resolved = resolve_release_zip_url()
    if resolved:
        return resolved
    return (
        f"https://github.com/{GITHUB_REPO}/releases/latest/download/{RELEASE_ZIP_NAME}"
    )
