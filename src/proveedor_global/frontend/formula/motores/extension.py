"""El enlace copia el stock del original. El pollo entero suma los kilos útiles.

No entra en la fórmula y no suma al total del remito.
"""

import re


_ESPEJO = re.compile(r"Espejo:\s*(.+)")
_ENTERO = re.compile(r"Entero:\s*(.+)")


def texto(items) -> str:
    """La anulación lee estas líneas. No son renglones de plata."""
    espejos = []
    enteros = []
    for item in items or []:
        if item.get("extension") == "enlace" and item.get("origen_id"):
            espejos.append(f"{item.get('id')}={item.get('origen_id')}")
        elif item.get("extension") == "entero":
            kilos = _num(item.get("cantidad"))
            if kilos:
                enteros.append(f"{item.get('nombre')} {kilos:g}")
    lineas = []
    if espejos:
        lineas.append("Espejo: " + ", ".join(espejos))
    if enteros:
        lineas.append("Entero: " + ", ".join(enteros))
    if not lineas:
        return ""
    return "\n".join(lineas) + "\n"


def escribir_db(db, items) -> None:
    """La nutrición no tiene el cursor de la recepción. Usa la misma escritura."""

    class _Cur:
        description = None

        def __init__(self):
            self._rows = []
            self._n = 0

        def execute(self, sql, params=()):
            if str(sql).lstrip().upper().startswith("SELECT"):
                self._rows = db.execute_query(sql, params) or []
                self._n = 0
            else:
                db.execute_non_query(sql, params)
                self._rows = []
                self._n = 0

        def fetchone(self):
            if self._n >= len(self._rows):
                return None
            fila = self._rows[self._n]
            self._n += 1
            return fila

    escribir(_Cur(), items)


def seguir(db, producto_id) -> None:
    """El inventario ya fijó el stock. El corte y las ofertas quedan en ese número.

    No suma. La carga sigue sumando por su propio camino.
    """
    ident = str(producto_id or "").strip()
    if not ident or db is None:
        return
    try:
        filas = db.execute_query(
            "SELECT producto_id, es_base, destino_id, corte, modulo FROM formula_pieza "
            "WHERE producto_id = ? OR destino_id = ?",
            (ident, ident),
        ) or []
    except Exception:
        return
    if not filas:
        return
    stock = _stock_id(db, ident)
    try:
        from src.proveedor_global.frontend.formula.motores.carne_stock import _stock_casa
        stock = _stock_casa(ident, stock)
    except Exception:
        pass
    if stock is None:
        return
    filas = [_como_pieza(f) for f in filas]
    propia = _fila_de(filas, ident)
    if not propia:
        for fila in filas:
            if str(fila.get("destino_id") or "") == ident:
                propia = fila
                break
    original = ident
    if propia and not int(propia.get("es_base") or 0):
        destino = str(propia.get("destino_id") or "").strip()
        if destino:
            original = destino
    corte = str((propia or {}).get("corte") or "").strip()
    modulo = str((propia or {}).get("modulo") or "").strip()
    try:
        db.execute_non_query("UPDATE productos SET stock = ? WHERE id = ?", (stock, original))
        _publicar(db, original, stock)
        ofertas = db.execute_query(
            "SELECT producto_id FROM formula_pieza "
            "WHERE modulo = ? AND UPPER(corte) = UPPER(?) AND es_base = 0",
            (modulo, corte),
        ) or []
    except Exception:
        return
    for cruda in ofertas:
        fila = cruda if isinstance(cruda, dict) else {}
        destino = str(fila.get("producto_id") or "").strip()
        if destino and destino != original:
            db.execute_non_query(
                "UPDATE productos SET stock = ? WHERE id = ?",
                (stock, destino),
            )
            _publicar(db, destino, stock)


def _publicar(db, ident, stock) -> None:
    try:
        from src.proveedor_global.frontend.formula.motores.inventario import _publicar_stock
        _publicar_stock(db, ident, stock)
    except Exception:
        return


def _stock_id(db, ident):
    try:
        filas = db.execute_query(
            "SELECT stock FROM productos WHERE id = ? LIMIT 1",
            (ident,),
        ) or []
    except Exception:
        return None
    if not filas:
        return None
    fila = filas[0]
    valor = fila.get("stock") if isinstance(fila, dict) else fila[0]
    try:
        return float(valor or 0)
    except (TypeError, ValueError):
        return 0.0


def _fila_de(filas, ident) -> dict:
    for cruda in filas or []:
        fila = _como_pieza(cruda)
        if str(fila.get("producto_id") or "") == ident:
            return fila
    return {}


def _como_pieza(cruda) -> dict:
    if isinstance(cruda, dict):
        return cruda
    claves = ("producto_id", "es_base", "destino_id", "corte", "modulo")
    try:
        return {claves[i]: cruda[i] for i in range(min(len(claves), len(cruda)))}
    except Exception:
        return {}


def escribir(cursor, items) -> None:
    """Después de los cortes. El enlace queda igual que el original. El entero suma sus kilos."""
    for item in items or []:
        tipo = str((item or {}).get("extension") or "")
        if tipo == "enlace":
            _copiar(cursor, item.get("origen_id"), item.get("id"))
        elif tipo == "entero":
            _sumar(cursor, item.get("id"), item.get("cantidad"), item.get("costo"))


def devolver(cursor, desc: str) -> None:
    """La anulación deja el enlace otra vez igual al original y resta el pollo entero."""
    for linea in _ESPEJO.findall(desc or ""):
        for par in linea.split(","):
            lados = par.strip().split("=")
            if len(lados) != 2:
                continue
            _copiar(cursor, lados[1].strip(), lados[0].strip())
    for linea in _ENTERO.findall(desc or ""):
        for trozo in linea.split(","):
            nombre, kilos = _trozo(trozo)
            if nombre and kilos:
                _sumar(cursor, _id_por_nombre(cursor, nombre), -kilos, 0)


def _copiar(cursor, origen, destino) -> None:
    origen = str(origen or "").strip()
    destino = str(destino or "").strip()
    if not origen or not destino or origen == destino:
        return
    try:
        cursor.execute(
            "SELECT stock, costo FROM productos WHERE id = ? LIMIT 1",
            (origen,),
        )
        cruda = cursor.fetchone()
    except Exception:
        return
    if not cruda:
        return
    fila = _fila(cruda, cursor)
    try:
        cursor.execute(
            "UPDATE productos SET stock = ?, costo = ? WHERE id = ?",
            (_num(fila.get("stock")), _num(fila.get("costo")), destino),
        )
    except Exception:
        return


def _sumar(cursor, ident, kilos, costo) -> None:
    ident = str(ident or "").strip()
    kilos = _num(kilos)
    costo = _num(costo)
    if not ident or kilos == 0:
        return
    try:
        if costo > 0 and kilos > 0:
            cursor.execute(
                "UPDATE productos SET stock = COALESCE(stock, 0) + ?, costo = ? WHERE id = ?",
                (kilos, costo, ident),
            )
        else:
            cursor.execute(
                "UPDATE productos SET stock = COALESCE(stock, 0) + ? WHERE id = ?",
                (kilos, ident),
            )
    except Exception:
        return


def _id_por_nombre(cursor, nombre: str) -> str:
    try:
        cursor.execute(
            "SELECT id FROM productos WHERE UPPER(TRIM(nombre)) = UPPER(TRIM(?)) LIMIT 1",
            (nombre,),
        )
        cruda = cursor.fetchone()
    except Exception:
        return ""
    if not cruda:
        return ""
    fila = _fila(cruda, cursor)
    return str(fila.get("id") or "")


def _trozo(texto: str):
    partes = str(texto or "").strip().rsplit(" ", 1)
    if len(partes) != 2:
        return "", 0.0
    return partes[0].strip(), _num(partes[1].replace(",", "."))


def _num(valor) -> float:
    try:
        return float(valor or 0)
    except (TypeError, ValueError):
        return 0.0


def _fila(cruda, cursor) -> dict:
    if isinstance(cruda, dict):
        return {str(k).lower(): cruda[k] for k in cruda.keys()}
    try:
        return {str(k).lower(): cruda[k] for k in cruda.keys()}
    except Exception:
        pass
    cols = []
    try:
        cols = [d[0] for d in (cursor.description or [])]
    except Exception:
        cols = []
    if not cols:
        return {}
    return {str(cols[i]).lower(): cruda[i] for i in range(min(len(cols), len(cruda)))}
