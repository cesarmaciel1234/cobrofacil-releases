from PyQt6.QtCore import QObject, pyqtSignal, QTimer
import logging
import threading


def _ficha(fila):
    if isinstance(fila, dict):
        return fila
    if hasattr(fila, "keys"):
        try:
            return {k: fila[k] for k in fila.keys()}
        except Exception:
            return {}
    return {}


import unicodedata


def _plegar(texto):
    base = unicodedata.normalize("NFD", str(texto or ""))
    sin = "".join(letra for letra in base if unicodedata.category(letra) != "Mn")
    return " ".join(sin.split()).casefold()


def _dni_digitos(valor):
    return "".join(c for c in str(valor or "") if c.isdigit())


def _coincide_mostrador(ficha, texto):
    q = (texto or "").strip()
    if not q:
        return False
    dni = _dni_digitos(ficha.get("dni"))
    solo_num = q.replace(".", "").replace(" ", "").replace("-", "")
    if solo_num.isdigit():
        return dni.startswith(_dni_digitos(q))
    tokens = _plegar(q).split()
    palabras = _plegar(str(ficha.get("nombre") or "")).replace("-", " ").split()
    if not tokens or not palabras:
        return False
    if len(tokens) == 1:
        t = tokens[0]
        return any(p.startswith(t) for p in palabras[:2])
    if len(palabras) < len(tokens):
        return False
    return all(palabras[k].startswith(tokens[k]) for k in range(len(tokens)))


class MotorBusquedaClientes(QObject):
    sugerencias_listas = pyqtSignal(list)
    limite_aprobado = pyqtSignal(dict)
    error_busqueda = pyqtSignal(str)
    _indice_listo = pyqtSignal()
    _consulta_lista = pyqtSignal(str, list)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger("PunPro")
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self._filtrar)
        self._ultimo_texto = ""
        self._monto_venta = 0.0
        self._indice = None
        self._cargando = False
        self._lock = threading.Lock()
        self._indice_listo.connect(self._on_indice_listo)
        self._consulta_lista.connect(self._aplicar_consulta)
        QTimer.singleShot(0, self.precargar)

    def set_monto_venta(self, monto):
        self._monto_venta = float(monto or 0.0)

    def precargar(self, forzar: bool = False):
        if (self._indice is not None and not forzar) or self._cargando:
            return
        self._cargando = True

        def trabajo():
            filas = []
            try:
                from src.base_de_datos.database import db_manager
                crudo = db_manager.execute_query(
                    "SELECT id, nombre, dni, limite_credito, deuda_actual FROM clientes"
                ) or []
                filas = [_ficha(r) for r in crudo]
            except Exception as e:
                self.logger.debug("Indice clientes: %s", e)
            with self._lock:
                self._indice = filas
            self._indice_listo.emit()

        threading.Thread(target=trabajo, name="indice-clientes", daemon=True).start()

    def _on_indice_listo(self):
        self._cargando = False
        if self._ultimo_texto:
            self._filtrar()

    def ficha(self, cliente_id):
        try:
            cid = int(cliente_id or 0)
        except (TypeError, ValueError):
            return None
        with self._lock:
            filas = self._indice or []
        for fila in filas:
            try:
                if int(fila.get("id") or 0) == cid:
                    return fila
            except (TypeError, ValueError):
                continue
        return None

    def buscar_texto(self, texto):
        self._ultimo_texto = (texto or "").strip()
        q = self._ultimo_texto
        solo_num = q.replace(".", "").replace(" ", "").replace("-", "")
        minimo = 3 if not solo_num.isdigit() else 3
        if len(q) < minimo:
            self.sugerencias_listas.emit([])
            return
        self._timer.start(60)

    def _filtrar(self):
        q = self._ultimo_texto
        if not q:
            self.sugerencias_listas.emit([])
            return
        with self._lock:
            indice = self._indice
        if indice is not None:
            coincidencias = self._recortar(q, indice)
            if coincidencias:
                self.sugerencias_listas.emit(coincidencias)
                return
        if self._cargando:
            return
        self._consultar_red(q)

    def _recortar(self, q, filas):
        salida = []
        for fila in filas:
            if _coincide_mostrador(fila, q):
                salida.append(fila)
            if len(salida) >= 5:
                break
        return salida

    def _consultar_red(self, texto):
        pedido = texto

        def trabajo():
            filas = []
            try:
                from src.base_de_datos.database import db_manager
                pref = f"{pedido}%"
                palabra = f"% {pedido}%"
                crudo = db_manager.execute_query(
                    "SELECT id, nombre, dni, limite_credito, deuda_actual FROM clientes "
                    "WHERE nombre LIKE ? OR nombre LIKE ? OR COALESCE(dni,'') LIKE ? "
                    "LIMIT 24",
                    (pref, palabra, pref),
                ) or []
                filas = [_ficha(r) for r in crudo]
            except Exception as e:
                self.logger.error("Error en MotorBusquedaClientes: %s", e)
            self._consulta_lista.emit(pedido, filas)

        threading.Thread(target=trabajo, name="busca-clientes", daemon=True).start()

    def _aplicar_consulta(self, pedido, filas):
        if pedido != self._ultimo_texto:
            return
        if filas:
            with self._lock:
                if self._indice is not None:
                    existentes_ids = {int(f.get("id") or 0) for f in self._indice}
                    for f in filas:
                        if int(f.get("id") or 0) not in existentes_ids:
                            self._indice.append(f)
        self.sugerencias_listas.emit(self._recortar(pedido, filas))

    def buscar_estricto(self, texto):
        try:
            texto_limpio = texto.replace(".", "").replace("-", "").replace(" ", "")
            es_dni = texto_limpio.isdigit() and len(texto_limpio) >= 7
            if texto_limpio.isdigit() and not es_dni:
                self.error_busqueda.emit("DNI invalido. Minimo 7 digitos.")
                return
            from src.clientes_fiado.cerebro.cerebro import cerebro
            if es_dni:
                cliente = cerebro.buscar_por_dni(texto)
            else:
                cliente = cerebro.buscar_por_nombre(texto)
            if not cliente:
                self.error_busqueda.emit("Cliente no encontrado.")
                return
            self.aprobar_credito(_ficha(cliente))
        except Exception as e:
            self.logger.error(f"Error buscar_estricto: {e}")
            self.error_busqueda.emit("Error de base de datos al buscar cliente.")

    def identificar_o_crear(self, texto):
        try:
            texto_limpio = texto.replace(".", "").replace("-", "").replace(" ", "")
            es_dni = texto_limpio.isdigit() and len(texto_limpio) >= 7
            if texto_limpio.isdigit() and not es_dni:
                self.error_busqueda.emit("DNI invalido. Minimo 7 digitos.")
                return
            from src.clientes_fiado.cerebro.cerebro import cerebro
            if es_dni:
                cliente, estado, msg = cerebro.identificar_dni(texto)
            else:
                cliente, estado, msg = cerebro.identificar_nombre(texto)
            if estado == "error" or not cliente:
                self.error_busqueda.emit(msg or "No se pudo identificar al cliente.")
                return
            self.aprobar_credito(_ficha(cliente))
        except Exception as e:
            self.logger.error(f"Error identificar_o_crear: {e}")
            self.error_busqueda.emit("Error de base de datos al crear cliente.")

    def aprobar_credito(self, cliente):
        try:
            from src.clientes_fiado.cerebro.cerebro import cerebro
            cartel = cerebro.cartel(cliente)
            disp = cartel.get("disponible") or 0.0
            saludo = str(cartel.get("saludo") or "").replace("Hola, ", "")
            datos = {
                "id": cliente.get("id"),
                "nombre": saludo,
                "limite": disp,
                "compra": self._monto_venta,
                "deuda": cartel.get("saldo") or 0.0,
            }
            self.limite_aprobado.emit(datos)
        except Exception as e:
            self.logger.error(f"Error aprobando credito: {e}")
            self.error_busqueda.emit("No se pudo calcular el crédito del cliente")
