import csv
import os
from datetime import datetime, timedelta, timezone

from src.logger import logger

ZONA_AR = timezone(timedelta(hours=-3))

RUTA = os.path.join("reportes", "mercado_pago_sync.csv")
COLUMNAS = [
    "Fecha Aprobacion",
    "ID de Pago",
    "Monto",
    "Cliente",
    "Email Cliente",
    "Estado",
    "Fecha Registro Local",
    "Tipo Operacion",
    "Monto Neto",
    "Tarifa",
]


def _limpio(valor):
    texto = str(valor or "").strip()
    if texto.lower() == "none":
        return ""
    return texto


def _fecha_ar(valor):
    """Hora de Argentina, como la muestra la app de Mercado Pago."""
    texto = str(valor or "").strip()
    if not texto:
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        from dateutil.parser import isoparse

        momento = isoparse(texto)
        if momento.tzinfo is None:
            return momento.strftime("%Y-%m-%d %H:%M:%S")
        return momento.astimezone(ZONA_AR).strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return texto.replace("T", " ").split(".")[0].split("+")[0].strip()


def _rotulo(pago):
    """El mismo texto que el historial de la app, y el tipo que usa la grilla."""
    pagador = pago.get("payer") or {}
    nombre = " ".join(
        parte for parte in (
            _limpio(pagador.get("first_name")),
            _limpio(pagador.get("last_name")),
        ) if parte
    )
    poi = pago.get("point_of_interaction") or {}
    poi_tipo = _limpio(poi.get("type")).upper()
    banco = ((poi.get("transaction_data") or {}).get("bank_info") or {}).get("payer") or {}
    banco_nombre = _limpio(banco.get("long_name"))
    if banco_nombre:
        nombre = banco_nombre.title() if banco_nombre.isupper() else banco_nombre
    op = _limpio(pago.get("operation_type")) or "regular_payment"
    metodo = _limpio(pago.get("payment_method_id")).lower()
    ptype = _limpio(pago.get("payment_type_id")).lower()
    es_transferencia = ptype == "bank_transfer" or metodo == "cvu" or poi_tipo == "PSP_TRANSFER"
    if es_transferencia:
        op = "transferencia"
    if not nombre:
        if op == "pos_payment" or poi_tipo in ("POINT", "POINT_SMART"):
            nombre = "Venta con Point Smart"
        elif poi_tipo == "INSTORE":
            nombre = "Venta con código QR"
        elif es_transferencia:
            nombre = "Transferencia recibida"
        else:
            nombre = "Cliente"
    return op, nombre


def _ids():
    if not os.path.exists(RUTA):
        return set()
    vistos = set()
    try:
        with open(RUTA, mode="r", encoding="utf-8-sig") as archivo:
            lector = csv.reader(archivo)
            next(lector, None)
            for fila in lector:
                if fila and len(fila) > 1:
                    vistos.add(str(fila[1]).strip())
    except Exception:
        pass
    return vistos


def _fila_de(pago):
    id_pago = str(pago.get("id", "")).strip()
    try:
        monto = float(pago.get("transaction_amount") or 0)
    except (TypeError, ValueError):
        monto = 0.0
    pagador = pago.get("payer") or {}
    email = _limpio(pagador.get("email")) or "sin_email@mercadopago.com"
    detalles = pago.get("transaction_details") or {}
    neto = detalles.get("net_received_amount")
    try:
        neto = float(neto) if neto is not None else monto
    except (TypeError, ValueError):
        neto = monto
    op, nombre = _rotulo(pago)
    return [
        _fecha_ar(pago.get("date_approved")),
        id_pago,
        f"{monto:.2f}",
        nombre,
        email,
        str(pago.get("status") or "approved").upper(),
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        op,
        f"{neto:.2f}",
        f"{monto - neto:.2f}",
    ]


def _filas():
    if not os.path.exists(RUTA):
        return []
    try:
        with open(RUTA, mode="r", encoding="utf-8-sig") as archivo:
            lector = csv.reader(archivo)
            next(lector, None)
            return [fila for fila in lector if fila]
    except Exception:
        return []


def guardar(pagos):
    """Agrega pagos nuevos y corrige hora, nombre y tipo de los que ya estaban. No repite un id."""
    os.makedirs(os.path.dirname(RUTA), exist_ok=True)
    filas = _filas()
    por_id = {}
    for indice, fila in enumerate(filas):
        if len(fila) > 1:
            por_id[str(fila[1]).strip()] = indice
    nuevas = 0
    cambio = False
    for pago in pagos or []:
        id_pago = str((pago or {}).get("id", "")).strip()
        if not id_pago or "SIMULADO" in id_pago:
            continue
        fila = _fila_de(pago)
        if id_pago in por_id:
            vieja = filas[por_id[id_pago]]
            if len(vieja) > 5 and vieja[5].strip() == "OMITIDO":
                fila[5] = "OMITIDO"
            if len(vieja) > 6 and vieja[6].strip():
                fila[6] = vieja[6]
            if vieja != fila:
                filas[por_id[id_pago]] = fila
                cambio = True
            continue
        filas.append(fila)
        por_id[id_pago] = len(filas) - 1
        nuevas += 1
        cambio = True
    if not cambio:
        return 0
    try:
        with open(RUTA, mode="w", newline="", encoding="utf-8-sig") as archivo:
            escritor = csv.writer(archivo)
            escritor.writerow(COLUMNAS)
            escritor.writerows(filas)
        if nuevas:
            logger.info(f"Se sincronizaron y respaldaron {nuevas} pagos nuevos en CSV.")
    except Exception as error:
        logger.error(f"Fallo al escribir en CSV de Mercado Pago: {error}")
        return 0
    return nuevas


def leer():
    """Pagos del CSV y los totales del mes y de hoy. Salta filas simuladas."""
    pagos = []
    ahora = datetime.now()
    mes = ahora.strftime("%Y-%m")
    hoy = ahora.strftime("%Y-%m-%d")
    total_mes = 0.0
    neto_mes = 0.0
    total_hoy = 0.0
    cant_hoy = 0
    if not os.path.exists(RUTA):
        return _vacio(pagos, total_mes, neto_mes, total_hoy, cant_hoy)
    try:
        with open(RUTA, mode="r", encoding="utf-8-sig") as archivo:
            lector = csv.reader(archivo)
            next(lector, None)
            for fila in lector:
                if not fila or len(fila) <= 5 or "SIMULADO" in fila[1]:
                    continue
                try:
                    monto = float(fila[2])
                except (TypeError, ValueError):
                    monto = 0.0
                try:
                    neto = float(fila[8]) if len(fila) > 8 else monto
                except (TypeError, ValueError):
                    neto = monto
                email = fila[4].strip()
                if len(fila) > 7:
                    tipo = fila[7].strip()
                elif email == "cesar-th123@live.com":
                    tipo = "account_fund"
                else:
                    tipo = "regular_payment"
                fecha = _fecha_ar(fila[0].strip())
                estado = fila[5].strip()
                nombre = fila[3].strip()
                if nombre.lower() in ("none none", "none"):
                    if tipo == "pos_payment":
                        nombre = "Venta con Point Smart"
                    elif tipo == "transferencia":
                        nombre = "Transferencia recibida"
                    else:
                        nombre = "Cliente"
                pagos.append({
                    "fecha": fecha,
                    "id": fila[1].strip(),
                    "monto": monto,
                    "nombre": nombre,
                    "email": email,
                    "estado": estado,
                    "op_type": tipo,
                    "neto": neto,
                })
                if estado.upper() == "APPROVED" and tipo != "account_fund":
                    if fecha.startswith(mes):
                        total_mes += monto
                        neto_mes += neto
                    if fecha.startswith(hoy):
                        total_hoy += monto
                        cant_hoy += 1
    except Exception as error:
        print("Error cargando CSV local:", error)
    pagos.sort(key=lambda pago: pago["fecha"], reverse=True)
    return _vacio(pagos, total_mes, neto_mes, total_hoy, cant_hoy)


def omitir(id_pago):
    """Pasa un pago de APPROVED a OMITIDO, o al revés. False si no hay archivo."""
    if not os.path.exists(RUTA):
        return False
    filas = []
    try:
        with open(RUTA, mode="r", encoding="utf-8-sig") as archivo:
            lector = csv.reader(archivo)
            cabecera = next(lector, None)
            for fila in lector:
                if fila and len(fila) > 5 and fila[1].strip() == str(id_pago):
                    fila[5] = "APPROVED" if fila[5].strip() == "OMITIDO" else "OMITIDO"
                if fila:
                    filas.append(fila)
        with open(RUTA, mode="w", newline="", encoding="utf-8-sig") as archivo:
            escritor = csv.writer(archivo)
            if cabecera:
                escritor.writerow(cabecera)
            escritor.writerows(filas)
    except Exception as error:
        print("Error al toggle omitir pago:", error)
        return False
    return True


def _vacio(pagos, total_mes, neto_mes, total_hoy, cant_hoy):
    return {
        "pagos": pagos,
        "total_mes": total_mes,
        "neto_mes": neto_mes,
        "total_hoy": total_hoy,
        "cant_hoy": cant_hoy,
    }
