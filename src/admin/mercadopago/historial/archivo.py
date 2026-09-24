import csv
import os
from datetime import datetime

from src.logger import logger

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


def guardar(pagos):
    """Agrega pagos nuevos al CSV. No repite un id. Ignora los simulados."""
    os.makedirs(os.path.dirname(RUTA), exist_ok=True)
    vistos = _ids()
    nuevas = []
    for pago in pagos or []:
        id_pago = str(pago.get("id", "")).strip()
        if not id_pago or id_pago in vistos or "SIMULADO" in id_pago:
            continue
        fecha = str(pago.get("date_approved") or "").replace("T", " ").replace(".000Z", "").split("+")[0]
        if not fecha:
            fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            monto = float(pago.get("transaction_amount") or 0)
        except (TypeError, ValueError):
            monto = 0.0
        pagador = pago.get("payer") or {}
        nombre = f"{pagador.get('first_name', '')} {pagador.get('last_name', '')}".strip() or "Cliente"
        email = pagador.get("email") or "sin_email@mercadopago.com"
        detalles = pago.get("transaction_details") or {}
        neto = detalles.get("net_received_amount")
        try:
            neto = float(neto) if neto is not None else monto
        except (TypeError, ValueError):
            neto = monto
        nuevas.append([
            fecha,
            id_pago,
            f"{monto:.2f}",
            nombre,
            email,
            str(pago.get("status") or "approved").upper(),
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            pago.get("operation_type") or "regular_payment",
            f"{neto:.2f}",
            f"{monto - neto:.2f}",
        ])
        vistos.add(id_pago)
    if not nuevas:
        return 0
    nuevo = not os.path.exists(RUTA)
    try:
        with open(RUTA, mode="a", newline="", encoding="utf-8-sig") as archivo:
            escritor = csv.writer(archivo)
            if nuevo:
                escritor.writerow(COLUMNAS)
            escritor.writerows(nuevas)
        logger.info(f"Se sincronizaron y respaldaron {len(nuevas)} pagos nuevos en CSV.")
    except Exception as error:
        logger.error(f"Fallo al escribir en CSV de Mercado Pago: {error}")
        return 0
    return len(nuevas)


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
                fecha = fila[0].strip()
                estado = fila[5].strip()
                pagos.append({
                    "fecha": fecha,
                    "id": fila[1].strip(),
                    "monto": monto,
                    "nombre": fila[3].strip(),
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
