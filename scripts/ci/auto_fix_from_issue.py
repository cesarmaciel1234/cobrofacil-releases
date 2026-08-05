#!/usr/bin/env python3
"""Orquesta Issue auto-report → Cursor Agent local → branch + PR.

Secrets / env esperados en Actions:
  CURSOR_API_KEY  — API key Cursor (agent CLI o cursor-sdk)
  GH_TOKEN / GITHUB_TOKEN — crear PR y comentar Issue
  ISSUE_NUMBER, ISSUE_TITLE, ISSUE_BODY, ISSUE_LABELS
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def _run(cmd: list[str], check: bool = True, **kwargs) -> subprocess.CompletedProcess:
    print("+", " ".join(cmd), flush=True)
    return subprocess.run(cmd, check=check, text=True, capture_output=True, **kwargs)


def _extract_fp(body: str) -> str:
    m = re.search(r"autofix-fp:([a-f0-9]{8,64})", body or "", re.I)
    if m:
        return m.group(1)
    m = re.search(r"Fingerprint:\s*`([a-f0-9]{8,64})`", body or "", re.I)
    if m:
        return m.group(1)
    return ""


def _gh_json(args: list[str]):
    env = os.environ.copy()
    r = _run(["gh", *args, "--json", "number,title,body,url,labels"], check=False)
    if r.returncode != 0:
        print(r.stderr, file=sys.stderr)
        return None
    try:
        return json.loads(r.stdout or "null")
    except json.JSONDecodeError:
        return None


def _is_ci_noise(title: str, body: str = "") -> bool:
    blob = f"{title}\n{body}".lower()
    return "[ci]" in blob or "token-check" in blob or "token check" in blob


def _list_open_autofix_prs() -> list[dict]:
    r = _run(
        [
            "gh",
            "pr",
            "list",
            "--state",
            "open",
            "--label",
            "auto-fix",
            "--json",
            "number,title,body,url,headRefName",
        ],
        check=False,
    )
    if r.returncode != 0:
        return []
    try:
        return json.loads(r.stdout or "[]")
    except json.JSONDecodeError:
        return []


def _existing_pr_for_fp(fp: str) -> dict | None:
    if not fp:
        return None
    for pr in _list_open_autofix_prs():
        body = pr.get("body") or ""
        if fp and (f"autofix-fp:{fp}" in body or fp in body):
            return pr
    return None


def _existing_pr_for_issue(issue_number: str) -> dict | None:
    """Evita ráfaga de PRs para el mismo Issue (p.ej. token-check)."""
    if not issue_number:
        return None
    needle_close = f"closes #{issue_number}"
    needle_head = f"autofix/issue-{issue_number}-"
    for pr in _list_open_autofix_prs():
        body = (pr.get("body") or "").lower()
        title = pr.get("title") or ""
        head = pr.get("headRefName") or ""
        if needle_close in body or head.startswith(needle_head):
            return pr
        if f"#{issue_number}" in title and "fix(auto)" in title.lower():
            return pr
    return None


def _build_prompt(issue_number: str, title: str, body: str, fp: str) -> str:
    return f"""You are fixing a production bug reported automatically by CobroFacil POS.

## Rules (mandatory)
- Minimal fix only; do not refactor unrelated code.
- Do NOT modify `src/cajero/` unless the traceback clearly points inside it.
- Do NOT touch secrets, tokens, `config.json`, or credentials.
- Do NOT add Firebase/LAN updater code (removed on purpose).
- Prefer defensive guards, null checks, import path fixes, and safe retries.
- Bump patch version in `version.json` `app_version` (e.g. 10.14.1 → 10.14.2).
- Keep UI light theme rules for admin; do not restyle cajero dark theme.
- After changes, ensure Python files compile conceptually (no syntax errors).

## Issue #{issue_number}
Title: {title}

Fingerprint: {fp or "unknown"}

Body:
{body[:12000]}

## Deliverable
Apply the fix in this working tree. Commit is done by CI after you finish.
If the report is not actionable (noise / env-only), create or update a short file
`docs/autofix_skip_reason.txt` explaining why, and make no other code changes.
"""


def _run_cursor_agent(prompt: str) -> bool:
    api_key = os.environ.get("CURSOR_API_KEY", "").strip()
    if not api_key:
        print("ERROR: CURSOR_API_KEY missing", file=sys.stderr)
        return False

    env = os.environ.copy()
    env["CURSOR_API_KEY"] = api_key
    agent = os.environ.get("CURSOR_AGENT_BIN", "agent")
    model = os.environ.get("CURSOR_AGENT_MODEL", "composer-2")

    # Cursor CLI (docs: GitHub Actions) — modo no interactivo con -p
    cmd = [agent, "-p", prompt, "--model", model]
    help_txt = (_run([agent, "--help"], check=False).stdout or "") + (
        _run([agent, "--help"], check=False).stderr or ""
    )
    if "--force" in help_txt:
        cmd.append("--force")

    print("Running Cursor agent…", flush=True)
    proc = subprocess.run(cmd, cwd=str(REPO_ROOT), env=env, text=True)
    if proc.returncode == 0:
        return True
    print(f"agent exit={proc.returncode}; trying cursor-sdk local…", flush=True)

    try:
        from cursor_sdk import Agent, AgentOptions, LocalAgentOptions

        result = Agent.prompt(
            prompt,
            AgentOptions(
                api_key=api_key,
                model=os.environ.get("CURSOR_AGENT_MODEL", "composer-2.5"),
                local=LocalAgentOptions(cwd=str(REPO_ROOT)),
            ),
        )
        status = getattr(result, "status", None)
        print("SDK status:", status, flush=True)
        return str(status).lower() in ("finished", "completed", "success", "ok") or status is None
    except Exception as e:
        print(f"cursor-sdk fallback failed: {e}", file=sys.stderr)
        return False

def _git_has_changes() -> bool:
    r = _run(["git", "status", "--porcelain"], check=False)
    return bool((r.stdout or "").strip())


def _ensure_labels():
    for label, color in (
        ("auto-fix", "1D76DB"),
        ("needs-auto-fix", "E4E669"),
        ("auto-report", "D93F0B"),
        ("client-error", "B60205"),
    ):
        _run(
            ["gh", "label", "create", label, "--color", color, "--force"],
            check=False,
        )


def main() -> int:
    os.chdir(REPO_ROOT)
    issue_number = os.environ.get("ISSUE_NUMBER", "").strip()
    title = os.environ.get("ISSUE_TITLE", "").strip()
    body = os.environ.get("ISSUE_BODY", "")
    if not issue_number:
        print("ISSUE_NUMBER required", file=sys.stderr)
        return 2

    if _is_ci_noise(title, body):
        print(f"Skip CI noise issue #{issue_number}: {title[:80]}")
        _run(
            [
                "gh",
                "issue",
                "comment",
                issue_number,
                "--body",
                "Auto-fix omitido: Issue de validación CI/token-check (anti-bucle).",
            ],
            check=False,
        )
        return 0

    fp = _extract_fp(body)
    existing = _existing_pr_for_issue(issue_number) or _existing_pr_for_fp(fp)
    if existing:
        url = existing.get("url", "")
        _run(
            [
                "gh",
                "issue",
                "comment",
                issue_number,
                "--body",
                f"Ya hay un PR de auto-fix abierto: {url}\n\n<!-- autofix-fp:{fp} -->",
            ],
            check=False,
        )
        print("Dedup: PR already open", url)
        return 0

    _ensure_labels()
    prompt = _build_prompt(issue_number, title, body, fp)
    if not _run_cursor_agent(prompt):
        _run(
            [
                "gh",
                "issue",
                "comment",
                issue_number,
                "--body",
                "Auto-fix: el agente no pudo completar el arreglo. Revisar logs del workflow.",
            ],
            check=False,
        )
        return 1

    skip_file = REPO_ROOT / "docs" / "autofix_skip_reason.txt"
    if skip_file.exists() and not _git_has_changes():
        reason = skip_file.read_text(encoding="utf-8", errors="replace")[:1500]
        _run(
            ["gh", "issue", "comment", issue_number, "--body", f"Auto-fix omitido:\n\n{reason}"],
            check=False,
        )
        return 0

    if not _git_has_changes():
        # Agent may have written skip file only
        if skip_file.exists():
            reason = skip_file.read_text(encoding="utf-8", errors="replace")[:1500]
            _run(
                ["gh", "issue", "comment", issue_number, "--body", f"Auto-fix omitido:\n\n{reason}"],
                check=False,
            )
            return 0
        _run(
            [
                "gh",
                "issue",
                "comment",
                issue_number,
                "--body",
                "Auto-fix: el agente no produjo cambios en el árbol.",
            ],
            check=False,
        )
        return 1

    # Si el agente solo dejó skip_reason / docs, no abrir PR (evita ruido)
    changed = (_run(["git", "status", "--porcelain"], check=False).stdout or "").strip().splitlines()
    code_changes = [
        ln
        for ln in changed
        if "docs/autofix_skip_reason.txt" not in ln and not ln.endswith("autofix_skip_reason.txt")
    ]
    if not code_changes:
        reason = ""
        if skip_file.exists():
            reason = skip_file.read_text(encoding="utf-8", errors="replace")[:1500]
        _run(
            [
                "gh",
                "issue",
                "comment",
                issue_number,
                "--body",
                f"Auto-fix omitido (sin cambios de código):\n\n{reason or 'solo docs/skip'}",
            ],
            check=False,
        )
        print("Skip PR: no code changes")
        return 0

    branch = f"autofix/issue-{issue_number}-{fp or 'nofp'}"[:60]
    _run(["git", "checkout", "-B", branch], check=True)
    _run(["git", "add", "-A"], check=True)
    # [skip ci] en el commit de la rama: evita cascades en push; PR Smoke sigue por pull_request.
    msg = f"fix(auto): issue #{issue_number} fingerprint {fp or 'n/a'} [skip ci]"
    _run(["git", "commit", "-m", msg], check=True)
    _run(["git", "push", "-u", "origin", branch, "--force"], check=True)

    pr_body = f"""## Summary
Auto-fix generado desde Issue #{issue_number}.

Fingerprint: `{fp}`

<!-- autofix-fp:{fp} -->

Closes #{issue_number}

## Test plan
- [ ] PR Smoke workflow verde
- [ ] Validar que el traceback del Issue queda cubierto
"""
    r = _run(
        [
            "gh",
            "pr",
            "create",
            "--title",
            f"fix(auto): #{issue_number} {title[:80]}",
            "--body",
            pr_body,
            "--label",
            "auto-fix",
            "--base",
            "main",
            "--head",
            branch,
        ],
        check=False,
    )
    print(r.stdout)
    print(r.stderr, file=sys.stderr)
    if r.returncode != 0:
        return 1

    # Quitar needs-auto-fix del issue si existe
    _run(["gh", "issue", "edit", issue_number, "--remove-label", "needs-auto-fix"], check=False)
    _run(
        [
            "gh",
            "issue",
            "comment",
            issue_number,
            "--body",
            f"Auto-fix: PR creado. Esperando CI smoke + auto-merge.\n\n<!-- autofix-fp:{fp} -->",
        ],
        check=False,
    )
    # Habilitar auto-merge cuando haya checks
    pr_url = (r.stdout or "").strip().splitlines()[-1] if r.stdout else ""
    if pr_url.startswith("http"):
        _run(["gh", "pr", "merge", pr_url, "--auto", "--squash"], check=False)
    return 0


if __name__ == "__main__":
    sys.exit(main())
