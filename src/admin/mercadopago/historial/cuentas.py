"""Cuentas de Mercado Pago y el período en que cada token estuvo activo en el TPV.

El nombre que se muestra es el de la persona en Mercado Pago, no un apodo.
Cada token solo cuenta los pagos de su período.
"""

from __future__ import annotations

import os
import requests
from datetime import datetime

from src.config import config
from src.logger import logger


def _nombre_legal(info: dict) -> str:
    fn = str((info or {}).get("first_name") or "").strip()
    ln = str((info or {}).get("last_name") or "").strip()
    return f"{fn} {ln}".strip()


def _nombre_de(entrada: dict) -> str:
    return str((entrada or {}).get("nombre_real") or (entrada or {}).get("nombre") or "").strip()


def _recordar(entrada: dict, viejo: str, nuevo: str = "") -> None:
    texto = str(viejo or "").strip()
    actual = str(nuevo or _nombre_de(entrada)).strip()
    if not texto or texto.casefold() == actual.casefold():
        return
    lista = [str(a).strip() for a in (entrada.get("alias_viejos") or []) if str(a).strip()]
    if texto not in lista:
        lista.append(texto)
    entrada["alias_viejos"] = lista


def _es_su_nombre(entrada: dict, texto: str) -> bool:
    buscado = str(texto or "").strip().casefold()
    if not buscado or buscado in ("—", "-", "mp"):
        return False
    candidatos = [entrada.get("nombre"), entrada.get("nombre_real"), *(entrada.get("alias_viejos") or [])]
    return any(str(c or "").strip().casefold() == buscado for c in candidatos)


def _cubre(entrada: dict, fecha: str) -> bool:
    desde = entrada.get("activo_desde") or ""
    hasta = entrada.get("activo_hasta") or "9999-12-31 23:59:59"
    return bool(fecha) and desde <= fecha <= hasta


def _bautizar(token: str, alias: str, collector_id: str) -> tuple[str, str, str]:
    info = _consultar_me_mp(token) if token else {}
    cid = str(collector_id or info.get("id") or "").strip()
    legal = _nombre_legal(info)
    nombre = legal or str(alias or "").strip()
    if not nombre:
        nick = str(info.get("nickname") or "").strip()
        nombre = nick or (f"Cuenta {cid}" if cid else "")
    return cid, legal, nombre


def _consultar_me_mp(token: str) -> dict:
    if not token:
        return {}
    try:
        r = requests.get(
            "https://api.mercadopago.com/users/me",
            headers={"Authorization": f"Bearer {token}"},
            timeout=5,
            verify=False,
        )
        if r.status_code == 200:
            return r.json() or {}
    except Exception:
        pass
    return {}


def registrar_token_activo(token: str, alias: str = "", collector_id: str = "") -> str:
    """Registra un nuevo token como activo en el TPV cerrando el período del token anterior."""
    token = str(token or "").strip()
    if not token:
        return ""

    config._load_config()
    historial = list(config.get("mp_tokens_historial", []) or [])
    ahora_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cid, legal, nombre = _bautizar(token, alias, collector_id)
    if not nombre:
        nombre = f"Token {token[:8]}…"

    token_pfx = (token[:15] + "…") if len(token) > 15 else token

    for entrada in reversed(historial):
        if entrada.get("activo_hasta") is not None:
            continue
        cid_abierto = str(entrada.get("collector_id") or "")
        if cid and cid_abierto:
            mismo = cid == cid_abierto
        else:
            mismo = entrada.get("token_prefix") == token_pfx
        if mismo:
            if legal and _nombre_de(entrada) != legal:
                _recordar(entrada, entrada.get("nombre"), legal)
                entrada["nombre"] = legal
                entrada["nombre_real"] = legal
            elif nombre and not entrada.get("nombre_real"):
                entrada["nombre"] = nombre
                entrada["nombre_real"] = nombre
            if cid:
                entrada["collector_id"] = cid
            if alias.strip() and alias.strip().casefold() != _nombre_de(entrada).casefold():
                _recordar(entrada, alias.strip())
            config.set("mp_token_alias", _nombre_de(entrada) or nombre)
            config.set("mp_tokens_historial", historial)
            if cid:
                config.set("mp_user_id", cid)
            try:
                config.save()
            except Exception:
                pass
            return _nombre_de(entrada) or nombre
        entrada["activo_hasta"] = ahora_str
        break

    visible = legal or nombre
    nueva_entrada = {
        "token_prefix": token_pfx,
        "collector_id": cid,
        "nombre": visible,
        "nombre_real": visible,
        "activo_desde": ahora_str,
        "activo_hasta": None,
        "alias_viejos": [],
    }
    if alias.strip() and alias.strip().casefold() != visible.casefold():
        nueva_entrada["alias_viejos"] = [alias.strip()]
    historial.append(nueva_entrada)
    config.set("mp_token_alias", nombre)
    config.set("mp_tokens_historial", historial)
    if cid:
        config.set("mp_user_id", cid)
    try:
        config.save()
    except Exception:
        pass
    logger.info(f"Mercado Pago: nueva cuenta/token activada en TPV: {nombre} (desde {ahora_str})")
    return nombre


_INICIALIZADO = False


def asegurar_inicializacion():
    """Si no hay historial pero ya hay un token en config, lo inicializa."""
    global _INICIALIZADO
    if _INICIALIZADO:
        return
    _INICIALIZADO = True
    historial = config.get("mp_tokens_historial")
    token = config.get("mp_access_token")
    if not historial and token:
        cid = str(config.get("mp_user_id") or "")
        alias = str(config.get("mp_token_alias") or "")
        mes_inicio = datetime.now().strftime("%Y-%m-01 00:00:00")
        info_me = _consultar_me_mp(token) if not cid or not alias else {}
        cid = cid or str(info_me.get("id") or "")
        legal = _nombre_legal(info_me)
        nombre = legal or alias.strip()
        if not nombre:
            nick = str(info_me.get("nickname") or "").strip()
            if nick:
                nombre = nick
            elif cid:
                nombre = f"Cuenta {cid}"
            else:
                nombre = "Titular TPV"
        token_pfx = (token[:15] + "…") if len(token) > 15 else token
        historial = [{
            "token_prefix": token_pfx,
            "collector_id": cid,
            "nombre": nombre,
            "nombre_real": legal or nombre,
            "activo_desde": mes_inicio,
            "activo_hasta": None,
        }]
        config.set("mp_token_alias", nombre)
        config.set("mp_tokens_historial", historial)
        if cid:
            config.set("mp_user_id", cid)
        try:
            config.save()
        except Exception:
            pass
    alinear_cuenta_viva()


def alinear_cuenta_viva() -> None:
    """El token cargado pone su nombre. Si es otra cuenta, cierra la anterior y abre la nueva."""
    token = str(config.get("mp_access_token") or "").strip()
    if not token:
        return
    info = _consultar_me_mp(token)
    legal = _nombre_legal(info)
    cid = str(info.get("id") or "").strip()
    if not legal or not cid:
        return
    historial = list(config.get("mp_tokens_historial", []) or [])
    ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    abierto = next((e for e in reversed(historial) if e.get("activo_hasta") is None), None)
    if (
        abierto
        and str(abierto.get("collector_id") or "") == cid
        and _nombre_de(abierto) == legal
        and str(config.get("mp_token_alias") or "") == legal
    ):
        return
    token_pfx = (token[:15] + "…") if len(token) > 15 else token
    if abierto and str(abierto.get("collector_id") or "") == cid:
        if _nombre_de(abierto) != legal:
            _recordar(abierto, abierto.get("nombre"), legal)
            abierto["nombre"] = legal
            abierto["nombre_real"] = legal
    elif abierto:
        abierto["activo_hasta"] = ahora
        historial.append({
            "token_prefix": token_pfx,
            "collector_id": cid,
            "nombre": legal,
            "nombre_real": legal,
            "activo_desde": ahora,
            "activo_hasta": None,
        })
    else:
        historial.append({
            "token_prefix": token_pfx,
            "collector_id": cid,
            "nombre": legal,
            "nombre_real": legal,
            "activo_desde": ahora if historial else "2026-01-01 00:00:00",
            "activo_hasta": None,
        })
    for entrada in historial:
        if str(entrada.get("collector_id") or "") != cid:
            continue
        if _nombre_de(entrada) == legal and entrada.get("nombre_real") == legal:
            continue
        _recordar(entrada, entrada.get("nombre"), legal)
        entrada["nombre"] = legal
        entrada["nombre_real"] = legal
    config.set("mp_token_alias", legal)
    config.set("mp_user_id", cid)
    config.set("mp_tokens_historial", historial)
    try:
        config.save()
    except Exception:
        pass


def rango_activo_token_actual() -> tuple[str | None, str | None]:
    """Devuelve (activo_desde, activo_hasta) para el token actualmente activo."""
    asegurar_inicializacion()
    historial = list(config.get("mp_tokens_historial", []) or [])
    for entrada in reversed(historial):
        if entrada.get("activo_hasta") is None:
            return entrada.get("activo_desde"), None
    if historial:
        return historial[-1].get("activo_desde"), historial[-1].get("activo_hasta")
    return None, None


def nombre_cuenta_para_pago(collector_id: str = "", fecha: str = "", almacenada: str = "") -> str:
    """Nombre legal de la cuenta que cobró ese id. Vacío si ese día no hubo token."""
    asegurar_inicializacion()
    historial = list(config.get("mp_tokens_historial", []) or [])
    cid_str = str(collector_id or "").strip()
    f_str = str(fecha or "").strip()[:19]
    guardada = str(almacenada or "").strip()

    if cid_str:
        propios = [e for e in historial if str(e.get("collector_id") or "") == cid_str]
        elegido = None
        if f_str:
            en_fecha = [e for e in propios if _cubre(e, f_str)]
            if en_fecha:
                en_fecha.sort(key=lambda e: e.get("activo_desde") or "")
                elegido = en_fecha[-1]
        if elegido is None and propios:
            elegido = propios[-1]
        if elegido:
            return _nombre_de(elegido) or cid_str

    if f_str and historial:
        en_fecha = [e for e in historial if _cubre(e, f_str)]
        if guardada:
            por_nombre = [e for e in en_fecha if _es_su_nombre(e, guardada)]
            if por_nombre:
                return _nombre_de(por_nombre[-1])
        if en_fecha:
            en_fecha.sort(key=lambda e: e.get("activo_desde") or "")
            return _nombre_de(en_fecha[-1])
    return ""


def listar_cuentas() -> list[str]:
    """Titulares que tuvieron un token, del más antiguo al que está activo."""
    historial = list(config.get("mp_tokens_historial", []) or [])
    orden = sorted(historial, key=lambda e: str(e.get("activo_desde") or ""))
    salida = []
    for entrada in orden:
        nombre = _nombre_de(entrada)
        if nombre and nombre not in salida:
            salida.append(nombre)
    return salida


def es_pago_valido_en_periodo(fecha: str, collector_id: str = "") -> bool:
    """Verifica si un pago ocurrió dentro del período activo de su cuenta en este TPV."""
    asegurar_inicializacion()
    historial = list(config.get("mp_tokens_historial", []) or [])
    if not historial:
        return True
    f_str = str(fecha or "").strip()[:19]
    if not f_str:
        return True
    cid_str = str(collector_id or "").strip()

    # Si conocemos el collector_id, validamos contra los períodos en que estuvo activo ese collector_id
    coincidentes = [e for e in historial if cid_str and e.get("collector_id") == cid_str]
    if coincidentes:
        for ent in coincidentes:
            desde = ent.get("activo_desde") or ""
            hasta = ent.get("activo_hasta") or "9999-12-31 23:59:59"
            if desde <= f_str <= hasta:
                return True
        return False

    # Si no hay collector_id específico (o es histórico sin id), verificar si cayó en cualquier período activo registrado
    for ent in historial:
        desde = ent.get("activo_desde") or ""
        hasta = ent.get("activo_hasta") or "9999-12-31 23:59:59"
        if desde <= f_str <= hasta:
            return True
    return False
