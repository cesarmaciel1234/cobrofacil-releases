"""Verificación de PIN de cajero (texto plano legacy o SHA-256 desde admin)."""
import hashlib


def verify_pin(entered: str, stored: str) -> bool:
    if not stored:
        return False
    entered = (entered or "").strip()
    stored = str(stored).strip()
    if not entered:
        return False
    if entered == stored:
        return True
    return hashlib.sha256(entered.encode()).hexdigest() == stored
