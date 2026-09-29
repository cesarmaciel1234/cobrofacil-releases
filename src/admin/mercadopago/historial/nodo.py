"""Sincronización del historial y los vínculos de MP con el nodo portable."""

from __future__ import annotations

import csv
import json
import os
import tempfile

from src.admin.mercadopago.historial import archivo

COLUMNA_CAMBIO_ESTADO = archivo.COLUMNA_CAMBIO_ESTADO


def _ruta_nodo(root: str, nombre: str) -> str:
    return os.path.join(root, "reportes", nombre)


def _leer_csv(path: str) -> list[dict] | None:
    if not os.path.isfile(path):
        return None
    with open(path, newline="", encoding="utf-8-sig") as f:
        lector = csv.DictReader(f)
        if not lector.fieldnames or "ID de Pago" not in lector.fieldnames:
            raise ValueError(f"El historial de Mercado Pago no tiene un encabezado válido: {path}")
        return [
            {columna: str(fila.get(columna) or "").strip() for columna in archivo.COLUMNAS}
            for fila in lector
            if str(fila.get("ID de Pago") or "").strip()
            and "SIMULADO" not in str(fila.get("ID de Pago") or "")
        ]


def _marca_estado(fila: dict) -> str:
    return fila.get(COLUMNA_CAMBIO_ESTADO) or fila.get("Fecha Registro Local") or ""


def _escribir_csv(path: str, filas: list[dict]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    fd, temporal = tempfile.mkstemp(prefix=".mp_historial_", suffix=".csv", dir=os.path.dirname(path))
    try:
        with os.fdopen(fd, "w", newline="", encoding="utf-8-sig") as f:
            escritor = csv.DictWriter(f, fieldnames=archivo.COLUMNAS)
            escritor.writeheader()
            escritor.writerows(filas)
        os.replace(temporal, path)
    except Exception:
        try:
            os.remove(temporal)
        except FileNotFoundError:
            pass
        raise


def _mezclar_csv(local_path: str, nodo_path: str) -> None:
    local = _leer_csv(local_path)
    nodo = _leer_csv(nodo_path)
    if local is None and nodo is None:
        return

    por_id: dict[str, dict] = {}
    for fila in nodo or []:
        por_id[fila["ID de Pago"]] = fila
    for fila_local in local or []:
        payment_id = fila_local["ID de Pago"]
        fila_nodo = por_id.get(payment_id)
        if fila_nodo is None:
            por_id[payment_id] = fila_local
            continue

        # Se completa la fila local con los campos que falten en la copia del nodo.
        fila = {
            columna: fila_local.get(columna) or fila_nodo.get(columna) or ""
            for columna in archivo.COLUMNAS
        }
        marca_local = _marca_estado(fila_local)
        marca_nodo = _marca_estado(fila_nodo)
        marca_explicita_local = fila_local.get(COLUMNA_CAMBIO_ESTADO, "")
        marca_explicita_nodo = fila_nodo.get(COLUMNA_CAMBIO_ESTADO, "")
        estados_distintos = fila_local.get("Estado") != fila_nodo.get("Estado")
        if estados_distintos and not marca_explicita_local and not marca_explicita_nodo:
            # CSV viejos no distinguen una restauración manual del estado APPROVED inicial.
            fila["Estado"] = (
                "OMITIDO"
                if "OMITIDO" in (fila_local.get("Estado"), fila_nodo.get("Estado"))
                else fila.get("Estado")
            )
            fila[COLUMNA_CAMBIO_ESTADO] = max(marca_local, marca_nodo)
        elif marca_nodo > marca_local:
            fila["Estado"] = fila_nodo.get("Estado") or fila.get("Estado")
            fila[COLUMNA_CAMBIO_ESTADO] = marca_nodo
        else:
            fila["Estado"] = fila_local.get("Estado") or fila.get("Estado")
            fila[COLUMNA_CAMBIO_ESTADO] = marca_local
        por_id[payment_id] = fila

    filas = list(por_id.values())
    _escribir_csv(local_path, filas)
    _escribir_csv(nodo_path, filas)


def _leer_vinculos(path: str) -> dict:
    if not os.path.isfile(path):
        return {}
    with open(path, encoding="utf-8") as f:
        datos = json.load(f)
    if not isinstance(datos, dict):
        raise ValueError(f"El archivo de vínculos de Mercado Pago no es un objeto JSON: {path}")
    return datos


def _marca_vinculo(vinculo: dict) -> str:
    return str(vinculo.get("cuando") or "")


def _mezclar_vinculos(local_path: str, nodo_path: str) -> None:
    local_existe = os.path.isfile(local_path)
    nodo_existe = os.path.isfile(nodo_path)
    if not local_existe and not nodo_existe:
        return
    local = _leer_vinculos(local_path)
    nodo = _leer_vinculos(nodo_path)
    unido: dict[str, dict] = {}

    for fuente in (nodo, local):
        for mes, pagos in fuente.items():
            if not isinstance(pagos, dict):
                raise ValueError(f"El mes {mes} no contiene vínculos válidos de Mercado Pago.")
            destino = unido.setdefault(str(mes), {})
            for payment_id, vinculo in pagos.items():
                if not isinstance(vinculo, dict):
                    raise ValueError(f"El vínculo del pago {payment_id} no es válido.")
                previo = destino.get(str(payment_id))
                if previo is None or _marca_vinculo(vinculo) < _marca_vinculo(previo):
                    destino[str(payment_id)] = vinculo

    contenido = json.dumps(unido, ensure_ascii=False, indent=2)
    for path in (local_path, nodo_path):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        fd, temporal = tempfile.mkstemp(prefix=".mp_vinculos_", suffix=".json", dir=os.path.dirname(path))
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                f.write(contenido)
            os.replace(temporal, path)
        except Exception:
            try:
                os.remove(temporal)
            except FileNotFoundError:
                pass
            raise


def sincronizar_nodo(root: str) -> None:
    """Une historial y vínculos locales con el nodo y deja ambas copias iguales."""
    from src.cajero.paso6_cobro.vinculo_mp import libro

    csv_nodo = _ruta_nodo(root, os.path.basename(archivo.RUTA))
    vinculos_nodo = _ruta_nodo(root, os.path.basename(libro.RUTA))
    with archivo._LOCK, libro._LOCK:
        _leer_csv(archivo.RUTA)
        _leer_csv(csv_nodo)
        _leer_vinculos(libro.RUTA)
        _leer_vinculos(vinculos_nodo)
        _mezclar_csv(archivo.RUTA, csv_nodo)
        _mezclar_vinculos(libro.RUTA, vinculos_nodo)
    try:
        from src.motor_cobros_digitales import despertar

        despertar()
    except Exception as error:
        from src.logger import logger

        logger.warning(f"[Cobros digitales] No se pudo despertar el motor tras sincronizar el nodo: {error}")


def sincronizar_nodo_configurado() -> bool:
    """Actualiza el nodo configurado; False si el puesto no tiene nodo asignado."""
    from src.jefe.nodo_portable.motor_nodo import estado_nodo, get_nodo_path

    root = get_nodo_path()
    if not root:
        return False
    if estado_nodo(root) != "ready":
        raise FileNotFoundError(
            "El nodo está configurado pero no está disponible. Conectá la unidad y volvé a sincronizar."
        )
    sincronizar_nodo(root)
    return True
