from PyQt6.QtWidgets import QMessageBox, QTableWidgetItem, QAbstractItemView, QListWidgetItem
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QColor
from src.base_de_datos.database import db_manager
from src.config import config
from src.cajero.paso5_terminal import parse_float_safe, fmt_moneda_sin_centavos, AUDIO_ENABLED
import logging
import threading
logger = logging.getLogger(__name__)
try:
    from src.ui_components.toast import Toast
except:
    pass

class TerminalBuscadorMixin:
    def actualizar_busqueda(self):
        # En lugar de buscar en cada tecla, esperamos 250ms.
        # Si entra otra tecla (como hace un escáner), el timer se reinicia.
        if not hasattr(self, 'search_timer'):
            self.search_timer = QTimer(self)
            self.search_timer.setSingleShot(True)
            self.search_timer.timeout.connect(self._do_busqueda)
        self.search_timer.start(250)
    def _do_busqueda(self):
        txt = self.txt_scan.text().strip()
        if not txt or txt.startswith('+'):
            self.list_results.hide()
            return
            
        # Ignorar la parte del multiplicador en la búsqueda visual para que no falle
        if '*' in txt:
            partes = txt.split('*', 1)
            txt = partes[1].strip()
            if not txt:
                self.list_results.hide()
                return
                
        res = db_manager.execute_query("SELECT id, nombre, precio, stock, cant_oferta, precio_oferta FROM productos WHERE id = ? OR nombre LIKE ? LIMIT 5", (txt, f"%{txt}%"))
        self.list_results.clear()
        
        if res:
            for r in res:
                stk = float(r['stock'] or 0.0)
                stk_str = f"{int(stk)}" if stk.is_integer() else f"{stk:.2f}"
                item = QListWidgetItem(f"📦 Stock: {stk_str}  |  {r['id']} - {r['nombre']} - ${r['precio']:.2f}")
                item.setData(Qt.UserRole, r)
                self.list_results.addItem(item)
            self.list_results.setCurrentRow(0)
            self.list_results.show()
            self.list_results.raise_()
        else:
            item = QListWidgetItem(f"🚫 No hay resultados para '{txt}'")
            item.setData(Qt.UserRole, None)
            item.setForeground(QColor("#FF0000"))
            self.list_results.addItem(item)
            self.list_results.clearSelection()
            self.list_results.show()
            self.list_results.raise_()
    def seleccionar_item_busqueda(self):
        current = self.list_results.currentItem()
        if current:
            p = current.data(Qt.UserRole)
            if p:
                # Si el usuario había ingresado un multiplicador en el texto, lo rescatamos
                txt_raw = self.txt_scan.text().strip()
                cant_multi = 1.0
                if '*' in txt_raw:
                    try: cant_multi = float(txt_raw.split('*')[0].replace(',', '.'))
                    except: pass
                self.agregar_a_tabla(p, cant_multi)
                self.txt_scan.clear()
                self.list_results.hide()
                self.txt_scan.setFocus()
    def procesar_scan(self):
        from src.utils.barcode_parser import BarcodeParser
        txt_raw = self.txt_scan.text()
        
        txt, cantidad_multiplicador = BarcodeParser.parse_scan_text(txt_raw)
        
        if not txt: 
            self.finalizar_venta()
            return

        # Lógica PRO: Artículo Común intencional usando el prefijo '+'
        p_manual, success = BarcodeParser.try_parse_manual_item(txt_raw.strip())
        if success:
            self.agregar_a_tabla(p_manual, cantidad_multiplicador)
            self.txt_scan.clear()
            self.list_results.hide()
            self.txt_scan.setFocus()
            return
        
        # Si hay lista de búsqueda abierta
        if not self.list_results.isHidden():
            current = self.list_results.currentItem()
            if current:
                p = current.data(Qt.UserRole)
                if p:
                    self.agregar_a_tabla(p, cantidad_multiplicador)
                    self.txt_scan.clear()
                    self.list_results.hide()
                    self.txt_scan.setFocus()
                    return

        # --- BUSQUEDA DE PRODUCTO ---
        # 1. Intentar búsqueda por ID exacto usando el nuevo Patrón de Repositorio
        from src.repositories.producto_repository import ProductoRepository
        p = ProductoRepository.obtener_por_id(txt)
        if p:
            self.agregar_a_tabla(p, cantidad_multiplicador)
            self.txt_scan.clear()
            self.list_results.hide()
            self.txt_scan.setFocus()
            return

        # 2. Lógica PRO: Códigos de Balanza (Configuración Dinámica)
        if len(txt) == 13 and txt.isdigit() and config.get("balanza_habilitada", True):
            # Try to get PLU to see if it exists
            prefijo_balanza = str(config.get("balanza_prefijo", "20"))
            if txt.startswith(prefijo_balanza) or txt.startswith("21"):
                p_start = max(0, int(config.get("balanza_plu_inicio", 3)) - 1)
                p_len   = int(config.get("balanza_plu_largo", 5))
                plu     = txt[p_start : p_start + p_len]
                plu_limpio = plu.lstrip('0') or '0'
                
                res = db_manager.execute_query(
                    "SELECT id, nombre, precio, cant_oferta, precio_oferta, precio_oferta_relampago, precio_oferta_promedio FROM productos WHERE id = ? OR id = ?",
                    (plu, plu_limpio)
                )
                if res:
                    p = res[0]
                    precio_unitario = float(p['precio'])
                    
                    _, cantidad_balanza = BarcodeParser.parse_balanza_code(txt, precio_unitario)
                    
                    if cantidad_balanza is not None:
                        self.agregar_a_tabla(p, cantidad_balanza)
                        self.txt_scan.clear()
                        self.list_results.hide()
                        self.txt_scan.setFocus()
                        return
                else:
                    # Si el PLU no existe, avisar específicamente
                    from PyQt6.QtWidgets import QMessageBox
                    QMessageBox.warning(self, "Balanza: Producto no encontrado", 
                        f"El código de balanza es correcto, pero el producto con PLU '{plu}' no existe en el sistema.\n\n"
                        "Por favor, asegúrate de crear el producto con ese código en el inventario.")
                    self.txt_scan.selectAll()
                    self.txt_scan.setFocus()
                    return

        # 3. Escaneo directo o búsqueda por nombre (Productos Normales)
        res = db_manager.execute_query("SELECT id, nombre, precio, cant_oferta, precio_oferta, precio_oferta_relampago, precio_oferta_promedio FROM productos WHERE id = ? OR nombre LIKE ?", (txt, f"%{txt}%"))

        if res:
            p = res[0]
            self.agregar_a_tabla(p, cantidad_multiplicador)
            self.txt_scan.clear()
            self.list_results.hide()
            self.txt_scan.setFocus()
        else:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "No Encontrado", f"No se encontró ningún producto con el código o nombre: '{txt}'")
            self.txt_scan.selectAll()
            self.txt_scan.setFocus()
    def agregar_a_tabla(self, p, cantidad=1.0):
        try:
            import os
            from datetime import datetime
            from src.utils.paths import get_base_path
            with open(os.path.join(get_base_path(), "logs", "cajero_espia.log"), "a", encoding="utf-8") as f:
                f.write(f"[{datetime.now().strftime('%H:%M:%S')}] agregar_a_tabla llamado para {p.get('nombre', 'Desconocido')}\n")
        except: pass

        # OPTIMIZACION: Congelar el renderizado de la tabla hasta que terminen todos los calculos
        self.setUpdatesEnabled(False)
        self.en_venta = True
        p_id = str(p['id'])
        precio_base = float(p['precio'])
        
        cant_of = 0.0
        precio_of = 0.0
        if hasattr(p, 'keys'):
            if 'cant_oferta' in p.keys(): cant_of = float(p['cant_oferta'] or 0.0)
            
            ofertas = [float(p.get(k) or 0) for k in ('precio_oferta', 'precio_oferta_relampago', 'precio_oferta_promedio')]
            validas = [x for x in ofertas if x > 0]
            precio_of = min(validas) if validas else 0.0
        
        # IA ROI Tracker: Verificar sugerencia activa
        vendido_por_ia = False
        prefix = ""
        try:
            import json, os, time
            from src.utils.paths import get_base_path
            path_sug = os.path.join(get_base_path(), "sugerencia_activa.json")
            if os.path.exists(path_sug):
                with open(path_sug, "r", encoding="utf-8") as f:
                    sug = json.load(f)
                    if time.time() - sug.get("timestamp", 0) < 180: # 3 mins TTL
                        if p['nombre'] in sug.get("productos", []):
                            vendido_por_ia = True
                            prefix = "🌟 "
        except: pass

        # 1. Agrupar si el producto ya existe en la tabla (Auto-Suma), excepto Artículos Comunes
        if p_id != "000":
            for i in range(self.tabla.rowCount()):
                if self.tabla.item(i, 0).text() == p_id:
                    old_cant = float(self.tabla.item(i, 3).text())
                    new_cant = old_cant + cantidad
                    
                    # Verificamos si alcanza o supera la cantidad de oferta
                    if cant_of > 0 and precio_of > 0 and new_cant >= cant_of:
                        p_aplicar = precio_of
                        desc_total = (precio_base - precio_of) * new_cant
                        display_name = f"{prefix}🔥 [OFERTA] {p['nombre']}"
                    else:
                        p_aplicar = precio_base
                        desc_total = 0.0
                        display_name = f"{prefix}{p['nombre']}"
                        
                    # Guardamos el flag en el item del nombre
                    it_name = self.tabla.item(i, 1)
                    it_name.setText(display_name)
                    if vendido_por_ia:
                        it_name.setData(Qt.UserRole, 1)
                    # Actualizar Precio Unitario Aplicado
                    self.tabla.item(i, 2).setText(fmt_moneda_sin_centavos(p_aplicar))
                    # Actualizar cantidad
                    self.tabla.item(i, 3).setText(f"{new_cant:.2f}" if new_cant % 1 != 0 else f"{int(new_cant)}")
                    # Actualizar Descuento Total
                    self.tabla.item(i, 4).setText(fmt_moneda_sin_centavos(desc_total))
                    # Actualizar Subtotal
                    self.tabla.item(i, 5).setText(fmt_moneda_sin_centavos(new_cant * p_aplicar))
                    self.last_active_row = i
                    self._reaplicar_estilo_fila(i)
                    
                    # Foco visual sutil centrado en el duplicado
                    self.tabla.selectRow(i)
                    self.actualizar_totales()
                    self.setUpdatesEnabled(True)
                    self.repaint()
                    if hasattr(self, 'timer_ia_carteleria'):
                        self.timer_ia_carteleria.start(500)
                    return

        # 2. Si no existe, calculamos para la inserción de la fila nueva
        if cant_of > 0 and precio_of > 0 and cantidad >= cant_of:
            p_aplicar = precio_of
            desc_total = (precio_base - precio_of) * cantidad
            display_name = f"{prefix}🔥 [OFERTA] {p['nombre']}"
        else:
            p_aplicar = precio_base
            desc_total = 0.0
            display_name = f"{prefix}{p['nombre']}"

        row = self.tabla.rowCount()
        self.tabla.insertRow(row)
        
        items = [p_id, display_name, fmt_moneda_sin_centavos(p_aplicar), f"{cantidad:.2f}" if cantidad % 1 != 0 else f"{int(cantidad)}", fmt_moneda_sin_centavos(desc_total), fmt_moneda_sin_centavos(p_aplicar * cantidad)]
        for idx, v in enumerate(items):
            it = QTableWidgetItem(v)
            it.setTextAlignment(Qt.AlignCenter)
            
            font = it.font()
            font.setBold(True) # Inquebrantable para toda la fila
            it.setFont(font)
            
            if idx == 1:
                it.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
                if vendido_por_ia:
                    it.setData(Qt.UserRole, 1)
            elif idx in (2, 3, 4, 5):
                it.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            
            if idx == 5: 
                it.setForeground(QColor("#059669")) # Esmeralda fuerte
                it.setFlags(it.flags() & ~Qt.ItemIsSelectable) # Deshabilitar selección para blindar su fondo verde agua
            
            self.tabla.setItem(row, idx, it)

        self.last_active_row = row
        self._reaplicar_estilo_fila(row)
        self.tabla.selectRow(row)
        self.actualizar_totales()
        
        # Sonido BEEP de Escáner ultra rápido
        if AUDIO_ENABLED:
            def fast_beep():
                try: import winsound; winsound.Beep(2500, 50)
                except: pass
            threading.Thread(target=fast_beep, daemon=True).start()
            
        # OPTIMIZACION: Liberar la pantalla para que dibuje el resultado final en 1 solo cuadro
        self.setUpdatesEnabled(True)
        self.repaint()
        if hasattr(self, 'timer_ia_carteleria'):
            self.timer_ia_carteleria.start(500)
