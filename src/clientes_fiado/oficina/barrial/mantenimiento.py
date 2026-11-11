"""Recargo de gestión / mantenimiento de cuenta (modo barrial empresarial).

Al abrir la cartera se aplica solo (ventana 30 días por cuenta).
Base 3% + apalancamiento 5% si hay más de 30 días sin movimiento de cliente
(el propio cargo de mantenimiento no reinicia ese aging).
"""

import math

from src.clientes_fiado.oficina.barrial.reglas import (
    AGING_30,
    APALANCAMIENTO_PCT_DEFAULT,
    MANTENIMIENTO_PCT_DEFAULT,
    MANTENIMIENTO_PCT_MAX,
    MANTENIMIENTO_PCT_MIN,
    MANTENIMIENTO_VENTANA_DIAS,
    MARCA_MANTENIMIENTO,
    PLAZO_DIAS_DEFAULT,
)


def _clamp_pct(valor, default):
    try:
        pct = float(valor)
    except (TypeError, ValueError):
        pct = float(default)
    if not math.isfinite(pct):
        pct = float(default)
    if pct < MANTENIMIENTO_PCT_MIN:
        return MANTENIMIENTO_PCT_MIN
    if pct > MANTENIMIENTO_PCT_MAX:
        return MANTENIMIENTO_PCT_MAX
    return round(pct, 2)


def porcentaje_base() -> float:
    try:
        from src.config import config

        config.reload()
        bruto = config.get("fiado_mantenimiento_pct", MANTENIMIENTO_PCT_DEFAULT)
    except Exception:
        bruto = MANTENIMIENTO_PCT_DEFAULT
    return _clamp_pct(bruto, MANTENIMIENTO_PCT_DEFAULT)


def porcentaje_apalancamiento() -> float:
    try:
        from src.config import config

        config.reload()
        bruto = config.get("fiado_apalancamiento_pct", APALANCAMIENTO_PCT_DEFAULT)
    except Exception:
        bruto = APALANCAMIENTO_PCT_DEFAULT
    return _clamp_pct(bruto, APALANCAMIENTO_PCT_DEFAULT)


def porcentaje() -> float:
    """Compat: solo la base (sin apalancamiento). Preferir tarifar()."""
    return porcentaje_base()


def plazo_dias_defecto() -> int:
    try:
        from src.config import config

        config.reload()
        bruto = config.get("fiado_plazo_dias", PLAZO_DIAS_DEFAULT)
        return max(1, int(bruto))
    except Exception:
        return PLAZO_DIAS_DEFAULT


def guardar_politicas_detalle(base_pct, apal_pct, plazo_dias=None) -> tuple[bool, str]:
    """Envía políticas a la Maestra (única fuente de verdad) y replica al config local."""
    try:
        from src.central_red_global.sync_tienda.config_tienda import guardar_y_sincronizar

        cambios = {
            "fiado_mantenimiento_pct": _clamp_pct(base_pct, MANTENIMIENTO_PCT_DEFAULT),
            "fiado_apalancamiento_pct": _clamp_pct(apal_pct, APALANCAMIENTO_PCT_DEFAULT),
        }
        if plazo_dias is not None:
            try:
                cambios["fiado_plazo_dias"] = max(1, int(plazo_dias))
            except (TypeError, ValueError):
                pass
        return guardar_y_sincronizar(cambios)
    except Exception as exc:
        return False, str(exc) or "No se pudo guardar la política."


def guardar_politicas(base_pct, apal_pct, plazo_dias=None) -> bool:
    """Persiste y sincroniza políticas vía Maestra."""
    ok, _err = guardar_politicas_detalle(base_pct, apal_pct, plazo_dias)
    return bool(ok)


def tarifar(deuda, dias=None) -> dict:
    """
    Calcula desglose de mantenimiento / tarifa.
    deuda <= 0 → monto 0 (cuenta en cero no aplica).
    `dias` = días desde el último pago (ABONO). Si > plazo_dias → base + apalancamiento.
    Si dias es None, solo base.
    """
    from src.utils.dinero import redondear_dinero

    try:
        saldo = float(deuda or 0)
    except (TypeError, ValueError):
        saldo = 0.0
    pct_base = porcentaje_base()
    pct_apal_cfg = porcentaje_apalancamiento()
    try:
        n_dias = int(dias) if dias is not None else None
    except (TypeError, ValueError):
        n_dias = None
    limite_dias = plazo_dias_defecto()
    aplica_apal = n_dias is not None and n_dias > limite_dias
    pct_apal = pct_apal_cfg if aplica_apal else 0.0
    pct_total = round(pct_base + pct_apal, 2)
    if saldo <= 0.009 or pct_total <= 0:
        return {
            "pct_base": pct_base,
            "pct_apal": pct_apal,
            "pct_total": pct_total,
            "monto_base": 0.0,
            "monto_apal": 0.0,
            "monto_total": 0.0,
            "aplica_apal": aplica_apal,
            "dias": n_dias,
        }
    monto_base = redondear_dinero(saldo * pct_base / 100.0)
    monto_apal = redondear_dinero(saldo * pct_apal / 100.0) if aplica_apal else 0.0
    monto_total = redondear_dinero(monto_base + monto_apal)
    return {
        "pct_base": pct_base,
        "pct_apal": pct_apal,
        "pct_total": pct_total,
        "monto_base": monto_base,
        "monto_apal": monto_apal,
        "monto_total": monto_total,
        "aplica_apal": aplica_apal,
        "dias": n_dias,
    }


def calcular(deuda, dias=None, pct=None) -> float:
    """Monto total. Si `pct` se fuerza, ignora aging. Si hay `dias`, usa tarifar."""
    if pct is not None:
        try:
            saldo = float(deuda or 0)
        except (TypeError, ValueError):
            saldo = 0.0
        if saldo <= 0.009:
            return 0.0
        tasa = float(pct)
        if tasa <= 0:
            return 0.0
        from src.utils.dinero import redondear_dinero

        return redondear_dinero(saldo * tasa / 100.0)
    return float(tarifar(deuda, dias).get("monto_total") or 0)


def descripcion(tarifa=None, pct=None) -> str:
    if tarifa is None and pct is not None:
        return f"{MARCA_MANTENIMIENTO} {float(pct):g}% gestión de cuenta"
    t = tarifa or {}
    base = float(t.get("pct_base") or porcentaje_base())
    if t.get("aplica_apal"):
        apal = float(t.get("pct_apal") or 0)
        total = float(t.get("pct_total") or (base + apal))
        return (
            f"{MARCA_MANTENIMIENTO} {base:g}%+{apal:g}% apal ({total:g}%) gestión"
        )
    return f"{MARCA_MANTENIMIENTO} {base:g}% gestión de cuenta"


def etiqueta_tarifa(dias=None) -> str:
    """Texto corto para columna Tarifa: '3%' o '8%'."""
    t = tarifar(100.0, dias)  # deuda dummy solo para % 
    total = float(t.get("pct_total") or 0)
    return f"{total:g}%"


def aplicar(cliente_id, deuda=None, dias=None, pct=None):
    """
    Escribe un CARGO de mantenimiento.
    Retorna (ok, nuevo_saldo, nombre, monto) o (False, 0, "", 0).
    """
    from src.clientes_fiado.oficina.cuenta.motor import MotorCuenta

    cuenta = MotorCuenta()
    if deuda is None:
        ficha = cuenta.obtener(cliente_id)
        if not ficha:
            return False, 0.0, "", 0.0
        deuda = float(dict(ficha).get("deuda_actual") or 0)
    if pct is not None:
        monto = calcular(deuda, pct=pct)
        desc = descripcion(pct=pct)
    else:
        tarifa = tarifar(deuda, dias)
        monto = float(tarifa.get("monto_total") or 0)
        desc = descripcion(tarifa)
    if monto <= 0.009:
        return False, 0.0, "", 0.0
    ok, nuevo, nombre = cuenta.cargar_manual(cliente_id, monto, desc)
    if not ok:
        return False, 0.0, "", 0.0
    return True, float(nuevo or 0), str(nombre or ""), monto


def _consulta_escribible(sql, params=()):
    """
    Lee de la misma base donde escribe _confirmar/get_connection.
    execute_query en esclava offline puede ir al espejo (solo lectura) y no ve los cargos nuevos.
    """
    from src.base_de_datos.database import db_manager

    conn = None
    try:
        conn = db_manager.get_connection()
        cur = conn.cursor()
        q = sql
        p = params
        if hasattr(db_manager, "_normalize_query"):
            q = db_manager._normalize_query(sql)
        cur.execute(q, p)
        return cur.fetchall() or []
    except Exception:
        return []
    finally:
        if conn:
            try:
                conn.close()
            except Exception:
                pass


def ultimos_mantenimientos(cliente_ids):
    """Última fecha de CARGO con marca MANTENIMIENTO por cliente (base escribible)."""
    ids = list(dict.fromkeys(cid for cid in cliente_ids if cid is not None))
    fechas = {}
    marca = f"{MARCA_MANTENIMIENTO}%"
    for inicio in range(0, len(ids), 500):
        bloque = ids[inicio:inicio + 500]
        placeholders = ", ".join("?" for _ in bloque)
        filas = _consulta_escribible(
            f"""
            SELECT cliente_id, MAX(fecha) AS fecha
            FROM cuenta_corriente
            WHERE tipo = 'CARGO'
              AND descripcion LIKE ?
              AND cliente_id IN ({placeholders})
            GROUP BY cliente_id
            """,
            (marca,) + tuple(bloque),
        )
        for fila in filas:
            if hasattr(fila, "keys") and not isinstance(fila, (tuple, list)):
                try:
                    cid, fecha = fila["cliente_id"], fila["fecha"]
                except Exception:
                    vals = list(fila)
                    cid, fecha = vals[0], vals[1]
            else:
                cid, fecha = fila[0], fila[1]
            if cid is not None and fecha is not None:
                try:
                    fechas[int(cid)] = fecha
                except (TypeError, ValueError):
                    fechas[cid] = fecha
    return fechas


def _parse_fecha_mov(valor):
    from datetime import datetime

    if valor is None:
        return None
    if isinstance(valor, datetime):
        return valor
    texto = str(valor).strip().split(".")[0]
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(texto[:19] if " " in texto else texto[:10], fmt)
        except ValueError:
            continue
    return None


def corresponde_auto(ultima_fecha_mant, ahora=None) -> bool:
    """True si no hubo mantenimiento en la ventana o nunca se cobró."""
    from datetime import datetime

    if ahora is None:
        ahora = datetime.now()
    dt = _parse_fecha_mov(ultima_fecha_mant)
    if dt is None:
        return True
    return (ahora - dt).days >= MANTENIMIENTO_VENTANA_DIAS


def aplicar_automatico(items):
    """
    Usa la lista [(cliente_id, deuda, dias), ...] para identificar cuentas.
    La deuda, el aging y la ventana se vuelven a comprobar dentro de la transacción.
    Retorna {ok, aplicados, omitidos, fallos, monto_total, detalle}.
    detalle = [(cliente_id, nuevo_saldo, monto), ...] para actualizar la UI sin releer el espejo.
    """
    from src.clientes_fiado.oficina.cuenta.motor import MotorCuenta
    from src.logger import logger

    cuenta = MotorCuenta()
    aplicados = 0
    omitidos = 0
    fallos = 0
    monto_total = 0.0
    detalle = []
    errores = []
    procesados = set()
    for item in items or []:
        if not isinstance(item, (tuple, list)) or len(item) < 3:
            fallos += 1
            errores.append((None, "elemento inválido"))
            continue
        cliente_id = item[0]
        try:
            cid = int(cliente_id)
        except (TypeError, ValueError):
            fallos += 1
            errores.append((cliente_id, "id inválido"))
            continue
        if cid in procesados:
            omitidos += 1
            continue
        procesados.add(cid)
        try:
            resultado = cuenta.aplicar_mantenimiento_automatico(cid)
        except Exception as error:
            logger.exception(
                "[Mantenimiento cartera] Falló cliente %s durante el cargo automático",
                cid,
            )
            resultado = {"estado": "fallo", "error": str(error)}
        estado = resultado.get("estado")
        if estado in ("omitido", "sin_deuda", "desactivado"):
            omitidos += 1
            continue
        if estado == "aplicado":
            aplicados += 1
            nuevo = resultado.get("saldo", 0.0)
            monto = resultado.get("monto", 0.0)
            monto_total += float(monto or 0)
            detalle.append((cid, float(nuevo or 0), float(monto or 0)))
        else:
            fallos += 1
            motivo = str(resultado.get("error") or estado or "error desconocido")
            errores.append((cid, motivo))
            logger.error(
                "[Mantenimiento cartera] No se aplicó para cliente %s: %s",
                cid,
                motivo,
            )
    return {
        "ok": fallos == 0,
        "aplicados": aplicados,
        "omitidos": omitidos,
        "fallos": fallos,
        "monto_total": monto_total,
        "detalle": detalle,
        "errores": errores,
    }


def _celda_fila(fila, clave, idx=0):
    if hasattr(fila, "keys") and not isinstance(fila, (tuple, list)):
        try:
            return fila[clave]
        except Exception:
            vals = list(fila)
            return vals[idx] if idx < len(vals) else None
    return fila[idx] if fila is not None else None


def _deuda_escribible(cliente_id):
    filas = _consulta_escribible(
        "SELECT deuda_actual FROM clientes WHERE id = ?",
        (cliente_id,),
    )
    if not filas:
        return None
    try:
        return float(_celda_fila(filas[0], "deuda_actual", 0))
    except (TypeError, ValueError):
        return None


_CAMPOS_LOCAL = ("deuda_actual", "estado_cuenta", "promesa_fecha", "promesa_nota")


def fichas_escribibles(cliente_ids):
    """
    Mapa id → campos locales (deuda / estado / promesa) desde la base escribible.
    En esclava offline el listado suele venir del espejo; esto trae lo ya cargado en local.
    """
    ids = list(dict.fromkeys(cid for cid in cliente_ids if cid is not None))
    out = {}
    for inicio in range(0, len(ids), 500):
        bloque = ids[inicio:inicio + 500]
        placeholders = ", ".join("?" for _ in bloque)
        filas = _consulta_escribible(
            f"""
            SELECT id, deuda_actual, estado_cuenta, promesa_fecha, promesa_nota
            FROM clientes WHERE id IN ({placeholders})
            """,
            tuple(bloque),
        )
        for fila in filas:
            try:
                cid = int(_celda_fila(fila, "id", 0))
            except (TypeError, ValueError):
                continue
            try:
                deuda = float(_celda_fila(fila, "deuda_actual", 1) or 0)
            except (TypeError, ValueError):
                deuda = 0.0
            out[cid] = {
                "deuda_actual": deuda,
                "estado_cuenta": _celda_fila(fila, "estado_cuenta", 2),
                "promesa_fecha": _celda_fila(fila, "promesa_fecha", 3),
                "promesa_nota": _celda_fila(fila, "promesa_nota", 4),
            }
    return out


def deudas_escribibles(cliente_ids):
    """Mapa id → deuda_actual desde la base donde se escribe (no el espejo)."""
    return {
        cid: float(datos.get("deuda_actual") or 0)
        for cid, datos in fichas_escribibles(cliente_ids).items()
    }


def aplicar_overlay_local(ficha, locales):
    """Copia deuda/estado/promesa locales sobre una ficha leída del espejo."""
    if not ficha or not locales:
        return ficha
    try:
        cid = int(ficha.get("id") if hasattr(ficha, "get") else None)
    except (TypeError, ValueError):
        return ficha
    local = locales.get(cid)
    if not local:
        return ficha
    out = dict(ficha)
    for clave in _CAMPOS_LOCAL:
        if clave in local:
            out[clave] = local[clave]
    return out


def overlay_lista(fichas):
    """Aplica overlay local a una lista de fichas."""
    lista = list(fichas or [])
    if not lista:
        return lista
    ids = []
    for f in lista:
        try:
            ids.append(int(f.get("id")))
        except (TypeError, ValueError, AttributeError):
            continue
    locales = fichas_escribibles(ids)
    if not locales:
        return [dict(f) if not isinstance(f, dict) else f for f in lista]
    return [aplicar_overlay_local(f, locales) for f in lista]
