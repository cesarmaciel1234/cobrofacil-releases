"""Ventas a crédito que no tienen cargo en la cuenta."""
import unicodedata

from src.base_de_datos.database import db_manager


def _plegar(texto):
    base = unicodedata.normalize("NFD", str(texto or ""))
    sin = "".join(letra for letra in base if unicodedata.category(letra) != "Mn")
    return " ".join(sin.split()).casefold()


def _ficha(fila):
    if fila is None:
        return {}
    if isinstance(fila, dict):
        return fila
    try:
        return dict(fila)
    except Exception:
        return {}


def _dni_de_express(nombre):
    """El DNI de un alta Express. Un nombre real no entra por acá."""
    from src.repositories.cliente_repository import ClienteRepository

    texto = " ".join(str(nombre or "").split())
    partes = texto.split(" ", 1)
    if len(partes) != 2 or partes[0].casefold() != "express":
        return ""
    return ClienteRepository.normalizar_dni(partes[1])


def emparejar(ventas, clientes):
    """Une cada venta con un cliente solo si el nombre, o el DNI Express, coincide con uno solo."""
    from src.repositories.cliente_repository import ClienteRepository

    por_nombre = {}
    por_dni = {}
    for cliente in clientes or []:
        ficha = _ficha(cliente)
        clave = _plegar(ficha.get("nombre"))
        if clave:
            por_nombre.setdefault(clave, []).append(ficha)
        dni = ClienteRepository.normalizar_dni(str(ficha.get("dni") or ""))
        if dni:
            por_dni.setdefault(dni, []).append(ficha)
    salida = []
    for venta in ventas or []:
        ficha = _ficha(venta)
        clave = _plegar(ficha.get("cliente_nombre"))
        candidatos = por_nombre.get(clave, []) if clave else []
        unico = candidatos[0] if len(candidatos) == 1 else None
        if unico is None:
            dni_venta = _dni_de_express(ficha.get("cliente_nombre"))
            por_documento = por_dni.get(dni_venta, []) if dni_venta else []
            if len(por_documento) == 1:
                unico = por_documento[0]
        try:
            total = float(ficha.get("total") or 0)
        except (TypeError, ValueError):
            total = 0.0
        salida.append({
            "venta_id": ficha.get("id"),
            "fecha": str(ficha.get("fecha") or ""),
            "metodo": str(ficha.get("metodo_pago") or ""),
            "total": total,
            "cliente_nombre": str(ficha.get("cliente_nombre") or "").strip(),
            "cliente_id": None if unico is None else unico.get("id"),
            "nombre": "" if unico is None else str(unico.get("nombre") or "").strip(),
        })
    return salida


def ventas_sin_cargo():
    ventas = db_manager.execute_query(
        "SELECT v.id, v.fecha, v.total, v.metodo_pago, v.cliente_nombre "
        "FROM ventas v WHERE v.estado = 'COMPLETADA' "
        "AND v.metodo_pago IN ('Fiado', 'Clientes') "
        "AND NOT EXISTS ("
        "SELECT 1 FROM cuenta_corriente cc "
        "WHERE cc.venta_id = v.id AND cc.tipo = 'CARGO'"
        ") ORDER BY v.fecha ASC, v.id ASC"
    ) or []
    clientes = db_manager.execute_query("SELECT id, nombre, dni FROM clientes") or []
    return emparejar(ventas, clientes)


def anotar(venta_id):
    """Carga en la cuenta un ticket que ya se vendió y no tiene cargo."""
    from src.base_de_datos.repos.ventas import _aplicar_fiado

    conn = None
    try:
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        bloqueo = " FOR UPDATE" if type(cursor).__name__ == "MariaDBCursorWrapper" else ""
        cursor.execute(
            "SELECT id, total, metodo_pago, cliente_nombre, estado "
            f"FROM ventas WHERE id = ?{bloqueo}",
            (venta_id,),
        )
        venta = _ficha(cursor.fetchone())
        if not venta:
            conn.rollback()
            return False, "No está esa venta"
        if str(venta.get("estado") or "") != "COMPLETADA":
            conn.rollback()
            return False, "Esa venta no está abierta"
        if str(venta.get("metodo_pago") or "") not in ("Fiado", "Clientes"):
            conn.rollback()
            return False, "Esa venta no es crédito"
        cursor.execute(
            "SELECT id FROM cuenta_corriente WHERE venta_id = ? AND tipo = 'CARGO' LIMIT 1",
            (venta_id,),
        )
        if cursor.fetchone():
            conn.rollback()
            return False, "Ese ticket ya está en la cuenta"
        cursor.execute("SELECT id, nombre, dni FROM clientes")
        pares = emparejar([venta], cursor.fetchall() or [])
        elegido = pares[0] if pares else {}
        if not elegido.get("cliente_id"):
            conn.rollback()
            return False, "No hay un solo cliente con ese nombre"
        _aplicar_fiado(
            cursor,
            {
                "cliente_id": elegido["cliente_id"],
                "total": float(venta.get("total") or 0),
                "ya_vendido": True,
                "nota": "cuadre",
            },
            venta_id,
        )
        conn.commit()
        return True, elegido.get("nombre") or ""
    except Exception:
        if conn:
            try:
                conn.rollback()
            except Exception:
                pass
        return False, "No se pudo cargar"
    finally:
        if conn:
            try:
                conn.close()
            except Exception:
                pass
