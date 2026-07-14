from src.utils.qt_compat import qt_exec
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QFrame, QPushButton, QMessageBox, QDialog,
    QSplitter, QComboBox, QCheckBox, QRadioButton
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer

# Removed db_manager import
from src.motor_descuentos.motor_ofertas import MotorOfertas
from src.carteleria.motor_descuentos_ui.componentes.tabla_ofertas import TablaOfertas
from src.carteleria.motor_descuentos_ui.componentes.creador_promociones import CreadorPromociones

def _parse_precio_texto(text, default=0.0):
    if text is None: return default
    s = str(text).strip().replace("$", "").replace(" ", "")
    if not s: return default
    if "," in s: s = s.replace(".", "").replace(",", ".")
    elif s.count(".") == 1:
        left, right = s.split(".")
        if len(right) == 3 and left.isdigit() and right.isdigit():
            s = left + right
    elif s.count(".") > 1:
        partes = s.split(".")
        s = "".join(partes[:-1]) + "." + partes[-1]
    try: return max(0.0, float(s))
    except (ValueError, TypeError): return default

def _format_precio_pdf(valor):
    return f"{_parse_precio_texto(valor):.2f}"

def _unidad_oferta_producto(producto):
    tipo = str(producto.get("tipo_unidad_oferta") or "").strip().lower()
    if tipo == "kilos": return "kilos"
    unidad = str(producto.get("unidad") or "").strip().upper()
    if unidad == "KG": return "kilos"
    return "unidades"

def _condicion_venta_texto(producto, cant_oferta):
    if _unidad_oferta_producto(producto) == "kilos":
        return f"Llevando {cant_oferta:g} Kilos"
    cant = max(1, int(cant_oferta)) if cant_oferta else 1
    return f"Llevando {cant} Unidades"



class Admin2Ofertas(QWidget):
    request_dashboard = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.checked_product_ids = set()
        self.all_rows = []
        self.loaded_count = 0
        self._setup_ui()
        self._apply_ofertas_theme()
        QTimer.singleShot(50, self._inicializar_datos)

    def showEvent(self, event):
        super().showEvent(event)
        self._apply_ofertas_theme()

    def _apply_ofertas_theme(self):
        self.tabla.aplicar_tema()
        self.panel_control.aplicar_tema()
        
        self.txt_buscar.setStyleSheet(
            "QLineEdit { background: #FFFFFF; color: #0F172A; border: 1px solid #CBD5E1; border-radius: 8px; padding: 10px 14px; }"
            "QLineEdit:focus { border: 2px solid #3B82F6; }"
        )
        self.cmb_depto.setStyleSheet(
            "QComboBox { background: #FFFFFF; color: #0F172A; border: 1px solid #CBD5E1; border-radius: 8px; padding: 8px 12px; }"
            "QComboBox:focus { border: 2px solid #3B82F6; }"
        )
        self.btn_imprimir_masivo.setProperty("class", "primary-btn")
        self.btn_crear_folleto.setProperty("class", "success-btn")
        self.btn_asistente_promo.setProperty("class", "warn-btn")

    def _inicializar_datos(self):
        self._cargar_deptos()
        self.cargar_datos()

    def _setup_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── HEADER ────────────────────────────────────────
        hdr = QFrame(); hdr.setObjectName("header"); hdr.setFixedHeight(85)
        hl = QHBoxLayout(hdr); hl.setContentsMargins(25, 0, 25, 0)
        
        btn_back = QPushButton("🔙 VOLVER AL PANEL")
        btn_back.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_back.setStyleSheet("QPushButton { background: #FFFFFF; color: #0F172A; font-weight: 800; border-radius: 10px; padding: 10px 25px; border: 1px solid #CBD5E1; font-size: 11px; letter-spacing: 1px; } QPushButton:hover { background: #EFF6FF; border-color: #3B82F6; color: #1D4ED8; }")
        btn_back.clicked.connect(self.request_dashboard.emit)
        hl.addWidget(btn_back)
        hl.addSpacing(20)
        
        tit = QLabel("🏷️ MOTOR DE PROMOCIONES INTELIGENTE <span id='titulo-ofertas-year'>2026</span>")
        tit.setObjectName("titulo")
        hl.addWidget(tit); hl.addStretch()
        root.addWidget(hdr)

        # ── FILTRO SUPERIOR ──────────────────────────────
        fb = QFrame(); fb.setFixedHeight(60)
        fb.setStyleSheet("QFrame { background: #FFFFFF; border-bottom: 1px solid #E2E8F0; }")
        fl = QHBoxLayout(fb); fl.setContentsMargins(15, 6, 15, 6); fl.setSpacing(12)
        
        ico_search = QLabel("🔍")
        self.txt_buscar = QLineEdit()
        self.txt_buscar.setPlaceholderText("Buscar por nombre, código o ID...")
        self.txt_buscar.setMinimumWidth(350)
        
        self.search_timer = QTimer()
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(self.cargar_datos)
        self.txt_buscar.textChanged.connect(lambda: self.search_timer.start(300))

        lbl_dep = QLabel("DEPARTAMENTO:")
        lbl_dep.setStyleSheet("font-weight:800;font-size:10px;letter-spacing:1px; background: transparent;")
        self.cmb_depto = QComboBox()
        self.cmb_depto.setMinimumWidth(180)
        self.cmb_depto.currentIndexChanged.connect(self.cargar_datos)

        fl.addWidget(ico_search)
        fl.addWidget(self.txt_buscar)
        fl.addSpacing(15)
        fl.addWidget(lbl_dep); fl.addWidget(self.cmb_depto)
        
        fl.addSpacing(15)
        self.chk_ver_promos = QCheckBox("🔥 Ver Solo Promos")
        self.chk_ver_promos.stateChanged.connect(self.cargar_datos)
        fl.addWidget(self.chk_ver_promos)
        
        fl.addSpacing(15)
        self.btn_imprimir_masivo = QPushButton("📚 IMPRIMIR MASIVO (A4)")
        self.btn_imprimir_masivo.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_imprimir_masivo.setEnabled(False)
        self.btn_imprimir_masivo.clicked.connect(self._imprimir_cartelera_masiva)
        fl.addWidget(self.btn_imprimir_masivo)

        self.btn_crear_folleto = QPushButton("📰 CREAR FOLLETO (PDF)")
        self.btn_crear_folleto.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_crear_folleto.clicked.connect(self._crear_folleto_pdf)
        fl.addWidget(self.btn_crear_folleto)
        
        self.btn_asistente_promo = QPushButton("🔥 ASISTENTE PROMO (A4)")
        self.btn_asistente_promo.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_asistente_promo.setEnabled(False)
        self.btn_asistente_promo.clicked.connect(self._configurar_ofertas_secuencial)
        fl.addWidget(self.btn_asistente_promo)
        
        self.btn_combos = QPushButton("🎁 GESTIONAR COMBOS")
        self.btn_combos.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_combos.clicked.connect(self._gestionar_combos)
        fl.addWidget(self.btn_combos)
        
        fl.addStretch()
        root.addWidget(fb)

        # ── CUERPO PRINCIPAL CON SPLITTER ──────────────────
        cuerpo = QWidget()
        lay_body = QVBoxLayout(cuerpo)
        lay_body.setContentsMargins(12, 8, 12, 8)
        lay_body.setSpacing(0)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setStyleSheet("QSplitter::handle {  width: 1px; }")

        # Componente Tabla
        self.tabla = TablaOfertas()
        self.tabla.item_checked.connect(self._on_item_checked)
        self.tabla.necesita_mas_datos.connect(self._cargar_siguiente_pagina)
        self.tabla.itemSelectionChanged.connect(self._on_tabla_selection_changed)
        splitter.addWidget(self.tabla)

        # Componente Creador Promociones
        self.panel_control = CreadorPromociones()
        self.panel_control.activar_promo.connect(self._on_activar_promo)
        self.panel_control.quitar_promo.connect(self._on_quitar_promo)
        self.panel_control.imprimir_cartel.connect(self._on_imprimir_cartel_rapido)
        splitter.addWidget(self.panel_control)
        
        splitter.setSizes([780, 420])
        lay_body.addWidget(splitter)
        root.addWidget(cuerpo)

        # ── Footer ───────────────────────────────────────
        ft = QFrame(); ft.setFixedHeight(38)
        ft.setStyleSheet("QFrame { background: #FFFFFF; border-top: 1px solid #E2E8F0; }")
        fl2 = QHBoxLayout(ft); fl2.setContentsMargins(12, 0, 12, 0)
        self.lbl_total   = QLabel("0 productos")
        self.lbl_stock0  = QLabel("")
        self.lbl_sel     = QLabel("")
        for lbl in [self.lbl_total, self.lbl_stock0, self.lbl_sel]:
            lbl.setStyleSheet("font-size:11px; background: transparent;")
        fl2.addWidget(self.lbl_total)
        fl2.addSpacing(20); fl2.addWidget(self.lbl_stock0)
        fl2.addStretch();   fl2.addWidget(self.lbl_sel)
        root.addWidget(ft)
        
        self.panel_control.set_enabled(False)

    def _cargar_deptos(self):
        self.cmb_depto.blockSignals(True)
        self.cmb_depto.clear()
        try:
            motor = MotorOfertas()
            rows = motor.obtener_departamentos()
            self.cmb_depto.addItem("— Todos los departamentos —", None)
            for r in rows:
                dep = r['departamento']
                if dep:
                    self.cmb_depto.addItem(dep, dep)
        except Exception as e:
            print(f"Error cargando deptos en ofertas: {e}")
        self.cmb_depto.blockSignals(False)

    def cargar_datos(self):
        buscar = self.txt_buscar.text().strip()
        depto  = self.cmb_depto.currentData()
        solo_promos = self.chk_ver_promos.isChecked()

        motor = MotorOfertas()
        self.all_rows = motor.buscar_productos(buscar, depto, solo_promos) or []
        self.loaded_count = 0
        self.tabla.setRowCount(0)
        
        self._cargar_siguiente_pagina()

        sin_stock = sum(1 for r in self.all_rows if (r['stock'] or 0.0) <= 0)
        n = len(self.all_rows)
        self.lbl_total.setText(f"📦 {n} PRODUCTOS EN LISTA")
        self.lbl_total.setStyleSheet(" font-weight: 800; background: transparent;")
        self.lbl_stock0.setText(f"⚠️ Stock Crítico: {sin_stock}" if sin_stock else "✅ Stock Saludable")
        self.lbl_stock0.setStyleSheet(f"color:{'#ef4444' if sin_stock else '#10b981'}; font-size:11px; font-weight:bold; background: transparent;")

    def _cargar_siguiente_pagina(self):
        if self.loaded_count >= len(self.all_rows):
            return
            
        inicio = self.loaded_count
        fin = min(inicio + 50, len(self.all_rows))
        
        filas_nuevas = self.all_rows[inicio:fin]
        self.tabla.popular_datos(filas_nuevas, inicio, self.checked_product_ids)
        self.loaded_count = fin

    def _on_item_checked(self, id_p, is_checked):
        if is_checked:
            self.checked_product_ids.add(id_p)
        else:
            self.checked_product_ids.discard(id_p)
            
        num_sel = len(self.checked_product_ids)
        self.btn_imprimir_masivo.setEnabled(num_sel > 0)
        self.btn_asistente_promo.setEnabled(num_sel > 0)
        self.lbl_sel.setText(f"Seleccionados (Checks): {num_sel}" if num_sel else "")

    def _on_tabla_selection_changed(self):
        row = self.tabla.currentRow()
        if row == -1:
            self.panel_control.cargar_producto(None)
            return
            
        item_id = self.tabla.item(row, 1)
        if not item_id:
            self.panel_control.cargar_producto(None)
            return
            
        id_p = item_id.data(Qt.ItemDataRole.UserRole)
        if not id_p: id_p = item_id.text()
        
        motor = MotorOfertas()
        p = motor.obtener_producto(id_p)
        if not p:
            self.panel_control.cargar_producto(None)
            return
            
        self.panel_control.cargar_producto(p)


    def _on_activar_promo(self, data):
        if data['cant_oferta'] <= 0 and data['precio_oferta'] <= 0 and data['precio_oferta_relampago'] <= 0 and data['precio_oferta_promedio'] <= 0:
            QMessageBox.warning(self, "Error", "Debe configurar al menos un precio de oferta mayor a cero.")
            return
            
        motor = MotorOfertas()
        ok = motor.aplicar_oferta(
            data['id'],
            data['cant_oferta'],
            data['precio_oferta'],
            data.get('precio_oferta_relampago', 0),
            data.get('precio_oferta_promedio', 0),
            data.get('limite_oferta_relampago', 0)
        )
        if ok:
            try:
                from src.central_red_global.network_engine import get_network_engine
                e = get_network_engine()
                if e: e.broadcast_message("PRECIOS_ACTUALIZADOS", {})
            except: pass
            self.cargar_datos()
            self.tabla.select_product_by_id(data['id'])
            QMessageBox.information(self, "Oferta Activada", "¡Promociones guardadas y sincronizadas!")
        else:
            QMessageBox.warning(self, "Error", "No se pudieron activar las promociones.")

    def _on_quitar_promo(self, id_p):
        motor = MotorOfertas()
        ok = motor.limpiar_oferta(id_p)
        if ok:
            try:
                from src.central_red_global.network_engine import get_network_engine
                e = get_network_engine()
                if e: e.broadcast_message("PRECIOS_ACTUALIZADOS", {})
            except: pass
            self.cargar_datos()
            self.tabla.select_product_by_id(id_p)
            QMessageBox.information(self, "Oferta Quitada", "Promociones removidas con éxito.")
        else:
            QMessageBox.warning(self, "Error", "No se pudo quitar la promoción.")

    def _on_imprimir_cartel_rapido(self, id_p, cant_oferta, precio_oferta):
        motor = MotorOfertas()
        p = motor.obtener_producto(id_p)
        if not p: return
        
        if cant_oferta <= 0 or precio_oferta <= 0:
            QMessageBox.warning(self, "Aviso", "⚠️ Para imprimir un cartel, el producto debe tener una promoción activa (Cantidad y Precio de Oferta mayores a cero).")
            return
            
        t_u = "Kilos" if _unidad_oferta_producto(p) == "kilos" else "Unidades"
        if t_u.lower() == "kilos":
            c_of_str = f"Llevando {cant_oferta:g} Kilos"
            es_kilos = True
        else:
            c_of_str = f"Llevando {int(cant_oferta)} Unidades"
            es_kilos = False

        dlg = QDialog(self)
        dlg.setWindowTitle("Opciones de Impresión de Cartel")
        dlg.setFixedSize(400, 260)
        dlg.setStyleSheet("QDialog { background: white; font-family: 'Segoe UI'; font-size: 13px; } QPushButton { background-color: #3b82f6; color: white; font-weight: bold; padding: 10px; border-radius: 6px; border: none; } QLineEdit, QComboBox { padding: 8px; border: 1px solid #cbd5e1; border-radius: 6px; background: white; }")
        lay = QVBoxLayout(dlg)
        lay.addWidget(QLabel(f"<b>Producto:</b> {p['nombre']}"))
        
        cmb_formato = QComboBox()
        cmb_formato.addItem("🎴 A6 Chico (4 por hoja - Recomendado)", "a6_grid")
        cmb_formato.addItem("🏷️ A8 Mini (8 por hoja - Especial Góndola)", "a8_grid")
        cmb_formato.addItem("📑 A5 Mediano (2 por hoja)", "a5_horizontal")
        cmb_formato.addItem("📄 A4 Grande (1 por hoja)", "a4_vertical")
        lay.addWidget(QLabel("<b>Tamaño / Distribución (Ahorro de papel):</b>"))
        lay.addWidget(cmb_formato)
        
        lay.addWidget(QLabel("<b>Leyenda de Promoción:</b>"))
        sug_leyenda = "¡OFERTA X KILO!" if es_kilos else (f"x{int(cant_oferta)}" if cant_oferta >= 2 else "¡OFERTA ESPECIAL!")
        txt_leyenda = QLineEdit(sug_leyenda)
        lay.addWidget(txt_leyenda)
        
        btn_ok = QPushButton("✔ Generar y Abrir Cartel")
        btn_ok.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_ok.clicked.connect(dlg.accept)
        lay.addSpacing(10); lay.addWidget(btn_ok)

        if qt_exec(dlg):
            try:
                from src.creador_pdf_global.motor_pdf import EtiquetaRenderer, abrir_archivo_pdf
            except ImportError:
                try: from creador_pdf_global.motor_pdf import EtiquetaRenderer, abrir_archivo_pdf
                except ImportError: return QMessageBox.critical(self, "Error", "No se pudo cargar el generador de etiquetas.")

            formato_sel = cmb_formato.currentData()
            repeticiones = {"a5_horizontal": 2, "a6_grid": 4, "a8_grid": 8}.get(formato_sel, 1)

            item_oferta = {
                "id": str(p['id']),
                "nombre": p['nombre'],
                "precio_regular": _format_precio_pdf(p['precio']),
                "tipo_promo": txt_leyenda.text().upper().strip(),
                "condicion_venta": c_of_str,
                "precio_oferta": _format_precio_pdf(precio_oferta),
                "formato": formato_sel
            }
            
            try:
                ren = EtiquetaRenderer()
                pdf_path = ren.generar_pdf_ofertas([item_oferta] * repeticiones)
                abrir_archivo_pdf(pdf_path)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo generar ni abrir el cartel: {e}")

    def _imprimir_cartelera_masiva(self):
        if not self.checked_product_ids: return QMessageBox.warning(self, "Aviso", "Por favor, marque al menos un producto.")
            
        motor = MotorOfertas()
        productos_promos = motor.obtener_productos_por_ids(list(self.checked_product_ids))
                        
        if not productos_promos:
            return QMessageBox.warning(self, "Aviso", "⚠️ Ninguno de los productos marcados tiene una promoción activa en la base de datos.")
            
        dlg = QDialog(self)
        dlg.setWindowTitle("Impresión de Cartelera Masiva (Libro)")
        dlg.setFixedSize(450, 320)
        dlg.setStyleSheet("QDialog { background: white; font-family: 'Segoe UI'; font-size: 13px; } QPushButton { background-color: #3b82f6; color: white; font-weight: bold; padding: 10px; border-radius: 6px; border: none; } QLineEdit, QComboBox { padding: 8px; border: 1px solid #cbd5e1; border-radius: 6px; background: white; }")
        lay = QVBoxLayout(dlg)
        lbl_info = QLabel(f"📚 <b>Se detectaron {len(productos_promos)} promociones activas</b> de los productos seleccionados.")
        lbl_info.setWordWrap(True)
        lay.addWidget(lbl_info)
        
        lay.addWidget(QLabel("<b>Tamaño y Distribución de los Carteles:</b>"))
        cmb_formato = QComboBox()
        cmb_formato.addItem("🎴 A6 Chico (4 por hoja - Recomendado)", "a6_grid")
        cmb_formato.addItem("🏷️ A8 Mini (8 por hoja - Especial Góndola)", "a8_grid")
        cmb_formato.addItem("📑 A5 Mediano (2 por hoja)", "a5_horizontal")
        cmb_formato.addItem("📄 A4 Grande (1 por hoja)", "a4_vertical")
        lay.addWidget(cmb_formato)
        
        lay.addWidget(QLabel("<b>Leyenda Comercial por Defecto:</b>"))
        txt_leyenda = QLineEdit("🔥 SUPER OFERTA")
        lay.addWidget(txt_leyenda)
        
        btn_ok = QPushButton(f"✔ Generar Libro de {len(productos_promos)} Páginas y Abrir")
        btn_ok.clicked.connect(dlg.accept)
        lay.addWidget(btn_ok)
        
        if qt_exec(dlg):
            try: from src.creador_pdf_global.motor_pdf import EtiquetaRenderer, abrir_archivo_pdf
            except ImportError: return
            
            formato_sel = cmb_formato.currentData()
            lote_ofertas = []
            for p in productos_promos:
                lote_ofertas.append({
                    "id": str(p['id']),
                    "nombre": p['nombre'],
                    "precio_regular": _format_precio_pdf(p['precio']),
                    "tipo_promo": txt_leyenda.text().upper().strip(),
                    "condicion_venta": _condicion_venta_texto(p, float(p['cant_oferta'] or 0.0)),
                    "precio_oferta": _format_precio_pdf(p['precio_oferta']),
                    "formato": formato_sel
                })

            try:
                ren = EtiquetaRenderer()
                pdf_path = ren.generar_pdf_ofertas(lote_ofertas)
                abrir_archivo_pdf(pdf_path)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo generar ni abrir la cartelera: {e}")

    def _crear_folleto_pdf(self):
        motor = MotorOfertas()
        rows_db = motor.obtener_productos_en_oferta()
        has_checked = len(self.checked_product_ids) > 0
        
        dlg = QDialog(self)
        dlg.setWindowTitle("Creación de Folleto de Ofertas (PDF)")
        dlg.setFixedSize(480, 360)
        dlg.setStyleSheet("QDialog { background: white; font-family: 'Segoe UI'; font-size: 13px; } QPushButton { background-color: #3b82f6; color: white; font-weight: bold; padding: 10px; border-radius: 6px; border: none; font-size: 12px; } QLineEdit, QComboBox { padding: 8px; border: 1px solid #cbd5e1; border-radius: 6px; background: white; } QRadioButton { spacing: 8px; font-weight: bold; }")
        lay = QVBoxLayout(dlg)
        
        lbl_tit = QLabel("📰 CREAR VOLANTE PUBLICITARIO (PDF)")
        lbl_tit.setStyleSheet(" font-size: 15px; font-weight: 900; letter-spacing: 0.5px;")
        lay.addWidget(lbl_tit)
        
        form = QFormLayout()
        txt_titulo = QLineEdit("🔥 GRAN BARATILLO DE OFERTAS 🔥")
        txt_negocio = QLineEdit("MINI-SÚPER ELITE")
        try:
            from src.config import config as _cfg
            if _cfg.get("business_name", ""): txt_negocio.setText(_cfg.get("business_name", "").upper())
        except: pass
            
        cmb_diseno = QComboBox()
        cmb_diseno.addItem("🖼️ Grilla de Tarjetas (6 por Pág.)", "grilla")
        cmb_diseno.addItem("📋 Lista de Precios Compacta", "lista")
        
        form.addRow("<b>Título Principal:</b>", txt_titulo)
        form.addRow("<b>Nombre del Negocio:</b>", txt_negocio)
        form.addRow("<b>Diseño del PDF:</b>", cmb_diseno)
        lay.addLayout(form)
        
        lay.addWidget(QLabel("<b>¿Qué productos incluir?</b>"))
        rb_all = QRadioButton(f"Todas las promociones vigentes ({len(rows_db)} detectadas)")
        rb_all.setChecked(True)
        rb_sel = QRadioButton(f"Solo los productos marcados [🗹] ({len(self.checked_product_ids)} seleccionados)")
        rb_sel.setEnabled(has_checked)
        if has_checked: rb_sel.setChecked(True)
            
        lay.addWidget(rb_all)
        lay.addWidget(rb_sel)
        
        btn_ok = QPushButton("✔ Generar Volante PDF y Abrir")
        btn_ok.clicked.connect(dlg.accept)
        lay.addWidget(btn_ok)
        
        if qt_exec(dlg):
            if rb_sel.isChecked():
                productos_a_procesar = motor.obtener_productos_por_ids(list(self.checked_product_ids))
            else:
                productos_a_procesar = rows_db
                
            if not productos_a_procesar: return QMessageBox.warning(self, "Aviso", "⚠️ No hay productos con ofertas activas.")
                
            lote_ofertas = []
            for p in productos_a_procesar:
                lote_ofertas.append({
                    "id": str(p['id']),
                    "nombre": p['nombre'],
                    "precio_regular": _format_precio_pdf(p['precio']),
                    "condicion_venta": _condicion_venta_texto(p, float(p['cant_oferta'] or 0.0)),
                    "precio_oferta": _format_precio_pdf(p['precio_oferta'])
                })
                
            try:
                from src.creador_pdf_global.motor_pdf import EtiquetaRenderer, abrir_archivo_pdf
                ren = EtiquetaRenderer()
                pdf_path = ren.generar_pdf_folleto_ofertas(
                    lote_ofertas=lote_ofertas,
                    titulo_folleto=txt_titulo.text().strip(),
                    negocio=txt_negocio.text().strip(),
                    diseno_tipo=cmb_diseno.currentData()
                )
                abrir_archivo_pdf(pdf_path)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Fallo al generar folleto PDF: {e}")

    def _configurar_ofertas_secuencial(self):
        if not self.checked_product_ids: return QMessageBox.warning(self, "Aviso", "Por favor, marque al menos un producto.")
            
        motor = MotorOfertas()
        seleccionados = motor.obtener_productos_por_ids(list(self.checked_product_ids))
        
        if not seleccionados: return QMessageBox.warning(self, "Aviso", "No se encontraron los productos seleccionados.")

        LIMIT_MAX = 50
        if len(seleccionados) > LIMIT_MAX:
            return QMessageBox.warning(self, "Límite de Impresión Excedido", f"⚠️ Límite de seguridad es de {LIMIT_MAX} etiquetas.\nSeleccionaste: {len(seleccionados)} etiquetas.")

        negocio_default = "MACIEL"
        try:
            from src.config import config as _cfg
            if _cfg.get("business_name", ""): negocio_default = _cfg.get("business_name", "").upper()
        except: pass

        dlg_marca = QDialog(self)
        dlg_marca.setWindowTitle("Configuración de Marca")
        dlg_marca.setFixedSize(380, 200)
        dlg_marca.setStyleSheet("QDialog { background: white; font-family: 'Segoe UI'; font-size: 13px; } QPushButton { background-color: #3b82f6; color: white; font-weight: bold; padding: 8px; border-radius: 6px; } QLineEdit { padding: 6px; border: 1px solid #cbd5e1; border-radius: 4px; }")
        lay_m = QVBoxLayout(dlg_marca)
        lay_m.addWidget(QLabel("<b>Rubro Comercial:</b>"))
        txt_rub = QLineEdit("CARNICERÍA")
        lay_m.addWidget(txt_rub)
        lay_m.addWidget(QLabel("<b>Nombre de Negocio:</b>"))
        txt_neg = QLineEdit(negocio_default)
        lay_m.addWidget(txt_neg)
        btn_m_ok = QPushButton("✔ Siguiente")
        btn_m_ok.clicked.connect(dlg_marca.accept)
        lay_m.addWidget(btn_m_ok)
        
        if not qt_exec(dlg_marca): return
            
        rubro = txt_rub.text().strip().upper() or "CARNICERÍA"
        negocio = txt_neg.text().strip().upper() or "MACIEL"

        lote_ofertas = []
        for idx, prod in enumerate(seleccionados, 1):
            dlg = QDialog(self)
            dlg.setWindowTitle(f"Calibrador de Oferta ({idx}/{len(seleccionados)})")
            dlg.setFixedSize(480, 360)
            dlg.setStyleSheet("QDialog { font-family: 'Segoe UI', sans-serif; } QLineEdit, QComboBox { background-color: white; padding: 10px; border: 1px solid #cbd5e1; border-radius: 6px; font-size: 13px; } QLineEdit:focus, QComboBox:focus { border: 2px solid #ea580c; } QPushButton { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #ea580c, stop:1 #f97316); color: white; font-weight: bold; padding: 12px 24px; border-radius: 8px; border: none; font-size: 13px; }")
            
            lay = QVBoxLayout(dlg)
            hf_lay = QVBoxLayout(QFrame())
            lbl_prod = QLabel(f"<span style='font-size:16px; font-weight:900;'>{prod['nombre']}</span>")
            hf_lay.addWidget(lbl_prod)
            lay.addWidget(hf_lay.parentWidget())
            
            from PyQt6.QtWidgets import QFormLayout
            form = QFormLayout()
            cmb_tipo = QComboBox()
            cmb_tipo.addItems(["OFERTA", "SUPER OFERTA", "x2", "x3", "LLEVAS 2 PAGAS 1", "LLEVAS 3 PAGAS 2", "PROMO ESPECIAL"])
            cmb_tipo.setEditable(True)
            
            sug_p = prod['precio_oferta'] if (prod['precio_oferta'] and prod['precio_oferta'] > 0) else prod['precio']
            txt_precio_of = QLineEdit(f"{sug_p:.2f}")
            
            cmb_formato = QComboBox()
            cmb_formato.addItem("🎴 A6 Chico (4 por hoja - Recomendado)", "a6_grid")
            cmb_formato.addItem("📄 A4 Grande (1 por hoja)", "a4_vertical")
            
            form.addRow("Tipo de Promoción:", cmb_tipo)
            form.addRow("Precio de Oferta ($):", txt_precio_of)
            form.addRow("Tamaño / Distribución:", cmb_formato)
            lay.addLayout(form)
            
            btn_ok = QPushButton("Calibrar Siguiente ➡" if idx < len(seleccionados) else "🏭 Iniciar Prensa PDF")
            btn_ok.clicked.connect(dlg.accept)
            lay.addWidget(btn_ok)
            
            if qt_exec(dlg):
                precio_of = _parse_precio_texto(txt_precio_of.text(), default=float(prod['precio'] or 0))
                if precio_of <= 0: return QMessageBox.warning(self, "Precio inválido", "Use solo números, por ejemplo: 1299.50")
                lote_ofertas.append({
                    "id": str(prod["id"]),
                    "nombre": prod["nombre"],
                    "precio_regular": _format_precio_pdf(prod['precio']),
                    "tipo_promo": cmb_tipo.currentText().upper(),
                    "condicion_venta": _condicion_venta_texto(prod, float(prod.get('cant_oferta') or 0.0) if float(prod.get('cant_oferta') or 0.0) > 0 else 1),
                    "precio_oferta": _format_precio_pdf(precio_of),
                    "formato": cmb_formato.currentData()
                })
            else: return
            
        if lote_ofertas:
            try:
                from src.creador_pdf_global.motor_pdf import EtiquetaRenderer, abrir_archivo_pdf
                renderer = EtiquetaRenderer()
                pdf_path = renderer.generar_pdf_ofertas(lote_ofertas, rubro=rubro, negocio=negocio)
                abrir_archivo_pdf(pdf_path)
            except Exception as ex:
                QMessageBox.critical(self, "Error", f"Fallo al construir PDF de ofertas: {ex}")

    def _gestionar_combos(self):
        from src.carteleria.motor_descuentos_ui.componentes.dialogo_combos import DialogoCombos
        dlg = DialogoCombos(self)
        dlg.exec()

