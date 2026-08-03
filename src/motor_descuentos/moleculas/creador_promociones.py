from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QDoubleSpinBox, 
    QFrame, QPushButton, QFormLayout, QScrollArea, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal

class CreadorPromociones(QWidget):
    activar_promo = pyqtSignal(dict)
    quitar_promo = pyqtSignal(str) # ID del producto
    imprimir_cartel = pyqtSignal(str, float, float) # ID, cant_oferta, precio_oferta
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.producto_id = None
        self._setup_ui()

    def _setup_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("QScrollArea { border: none; background: #F8FAFC; }")
        
        self.panel = QFrame()
        self.panel.setObjectName("ControlCenter")
        self.panel.setStyleSheet("""
            QFrame#ControlCenter {
                background-color: #FFFFFF;
                border-left: 1px solid #E2E8F0;
            }
            QLabel { background: transparent; color: #334155; }
            QDoubleSpinBox, QLineEdit {
                background-color: #F8FAFC;
                color: #0F172A;
                border: 1px solid #CBD5E1;
            }
        """)
        lay_ctrl = QVBoxLayout(self.panel)
        lay_ctrl.setContentsMargins(20, 20, 20, 20)
        lay_ctrl.setSpacing(15)
        
        # Encabezado
        lbl_head = QLabel("⚙️ REGLAS DEL PRODUCTO")
        lbl_head.setStyleSheet("color: #64748B; font-size: 13px; font-weight: 900; letter-spacing: 1px;")
        lay_ctrl.addWidget(lbl_head)
        
        self.lbl_prod_nombre = QLabel("Seleccione un producto...")
        self.lbl_prod_nombre.setStyleSheet("color: #1D4ED8; font-size: 18px; font-weight: 900;")
        self.lbl_prod_nombre.setWordWrap(True)
        lay_ctrl.addWidget(self.lbl_prod_nombre)
        
        self.lbl_prod_detalles = QLabel("ID: —  |  PLU: —")
        self.lbl_prod_detalles.setStyleSheet("color: #64748B; font-size: 12px; font-family: 'Consolas', monospace; font-weight: bold;")
        lay_ctrl.addWidget(self.lbl_prod_detalles)
        
        sep = QFrame(); sep.setFrameShape(QFrame.Shape.HLine); sep.setFrameShadow(QFrame.Shadow.Sunken)
        sep.setStyleSheet("max-height: 1px; background: #E2E8F0;")
        lay_ctrl.addWidget(sep)
        
        # Sección A
        lbl_sec_a = QLabel("📦 CONTROL DE STOCK")
        lbl_sec_a.setStyleSheet("color: #64748B; font-weight: 800; font-size: 11px; letter-spacing: 1px;")
        lay_ctrl.addWidget(lbl_sec_a)
        
        form_a = QFormLayout()
        form_a.setSpacing(8)
        
        self.txt_quick_precio = QDoubleSpinBox()
        self.txt_quick_precio.setRange(0, 9999999)
        self.txt_quick_precio.setDecimals(2)
        self.txt_quick_precio.setStyleSheet("font-size: 13px; padding: 6px; font-weight: bold;")
        
        self.txt_quick_costo = QDoubleSpinBox()
        self.txt_quick_costo.setRange(0, 9999999)
        self.txt_quick_costo.setDecimals(2)
        self.txt_quick_costo.setStyleSheet("font-size: 13px; padding: 6px;")
        
        self.txt_quick_stock = QDoubleSpinBox()
        self.txt_quick_stock.setRange(-9999, 999999)
        self.txt_quick_stock.setDecimals(2)
        self.txt_quick_stock.setStyleSheet("font-size: 13px; padding: 6px; font-weight: bold; ")
        
        form_a.addRow(QLabel("Precio Venta ($):"), self.txt_quick_precio)
        form_a.addRow(QLabel("Costo Compra ($):"), self.txt_quick_costo)
        form_a.addRow(QLabel("Stock Actual:"), self.txt_quick_stock)
        lay_ctrl.addLayout(form_a)
        
        
        # Sección B: Promociones
        lbl_sec_b = QLabel("🏷️ REGLAS MATEMÁTICAS DE PROMOCIÓN")
        lbl_sec_b.setStyleSheet("color: #64748B; font-weight: 800; font-size: 11px; letter-spacing: 1px;")
        lay_ctrl.addWidget(lbl_sec_b)
        
        form_b = QFormLayout()
        form_b.setSpacing(8)
        
        self.sp_quick_cant_oferta = QDoubleSpinBox()
        self.sp_quick_cant_oferta.setRange(0, 99999)
        self.sp_quick_cant_oferta.setDecimals(2)
        self.sp_quick_cant_oferta.setStyleSheet("font-size: 13px; padding: 6px;")
        
        self.sp_quick_precio_oferta = QDoubleSpinBox()
        self.sp_quick_precio_oferta.setRange(0, 9999999)
        self.sp_quick_precio_oferta.setDecimals(2)
        self.sp_quick_precio_oferta.setStyleSheet("font-size: 13px; padding: 6px;  font-weight: bold;")

        self.sp_quick_oferta_relampago = QDoubleSpinBox()
        self.sp_quick_oferta_relampago.setRange(0, 9999999)
        self.sp_quick_oferta_relampago.setDecimals(2)
        self.sp_quick_oferta_relampago.setStyleSheet("font-size: 13px; padding: 6px;")

        self.sp_quick_oferta_promedio = QDoubleSpinBox()
        self.sp_quick_oferta_promedio.setRange(0, 9999999)
        self.sp_quick_oferta_promedio.setDecimals(2)
        self.sp_quick_oferta_promedio.setStyleSheet("font-size: 13px; padding: 6px;")
        
        self.sp_limite_relampago = QDoubleSpinBox()
        self.sp_limite_relampago.setRange(0, 9999999)
        self.sp_limite_relampago.setDecimals(0)
        self.sp_limite_relampago.setStyleSheet("font-size: 13px; padding: 6px;")
        self.lbl_ventas_relampago = QLabel("Vendidos: 0 / 0")
        self.lbl_ventas_relampago.setStyleSheet("color: #D97706; font-weight: bold;")
        
        form_b.addRow(QLabel("Oferta desde (Cant):"), self.sp_quick_cant_oferta)
        form_b.addRow(QLabel("Precio Of. Manual ($):"), self.sp_quick_precio_oferta)
        form_b.addRow(QLabel("Of. Relámpago ($):"), self.sp_quick_oferta_relampago)
        form_b.addRow(QLabel("Límite (uds):"), self.sp_limite_relampago)
        form_b.addRow(QLabel(""), self.lbl_ventas_relampago)
        form_b.addRow(QLabel("Of. Promedio ($):"), self.sp_quick_oferta_promedio)
        lay_ctrl.addLayout(form_b)
        
        # Simulador
        self.group_simulador = QFrame()
        self.group_simulador.setStyleSheet("""
            QFrame {
                background-color: #F8FAFC;
                border: 1px solid #E2E8F0;
                border-radius: 12px;
                padding: 15px;
                margin-top: 5px;
            }
        """)
        lay_sim = QVBoxLayout(self.group_simulador)
        lay_sim.setSpacing(6)
        
        lbl_sim_tit = QLabel("📊 SIMULADOR DE MARGEN INDUSTRIAL")
        lbl_sim_tit.setStyleSheet("color: #475569; font-weight: 900; font-size: 12px; letter-spacing: 1px; border: none;")
        lay_sim.addWidget(lbl_sim_tit)
        
        self.lbl_margen_reg = QLabel("Margen Regular: —")
        self.lbl_margen_reg.setStyleSheet("color: #64748B; font-size: 13px; font-weight: bold; border: none;")
        lay_sim.addWidget(self.lbl_margen_reg)
        
        self.lbl_margen_promo = QLabel("Margen Promo: —")
        self.lbl_margen_promo.setStyleSheet("color: #059669; font-size: 18px; font-weight: 900; border: none;")
        lay_sim.addWidget(self.lbl_margen_promo)
        
        self.lbl_ahorro_total = QLabel("Ahorro de Cliente: —")
        self.lbl_ahorro_total.setStyleSheet("color: #D97706; font-size: 16px; font-weight: bold; border: none;")
        lay_sim.addWidget(self.lbl_ahorro_total)
        
        self.lbl_semaforo = QLabel("Seleccione un producto...")
        self.lbl_semaforo.setStyleSheet("color: #475569; font-size: 11px; font-weight: 800; border: none;")
        self.lbl_semaforo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay_sim.addWidget(self.lbl_semaforo)
        
        lay_ctrl.addWidget(self.group_simulador)
        
        lay_promo_btns = QHBoxLayout()
        self.btn_activar_promo = QPushButton("🚀 ACTIVAR PROMO")
        self.btn_activar_promo.setStyleSheet("""
            QPushButton {
                background-color: #2563EB; color: white; font-weight: 900; font-size: 12px;
                padding: 12px; border-radius: 8px; border: none; letter-spacing: 1px;
            }
            QPushButton:hover { background-color: #1D4ED8; }
            QPushButton:pressed { background-color: #1E40AF; }
        """)
        self.btn_activar_promo.clicked.connect(self._emit_activar_promo)
        
        self.btn_quitar_promo = QPushButton("❌ QUITAR PROMO")
        self.btn_quitar_promo.setStyleSheet("""
            QPushButton {
                color: #EF4444; background: transparent; font-weight: bold; font-size: 12px;
                padding: 12px; border-radius: 8px; border: 2px solid #EF4444; letter-spacing: 1px;
            }
            QPushButton:hover { background-color: #EF4444; color: white; }
        """)
        self.btn_quitar_promo.clicked.connect(self._emit_quitar_promo)
        
        lay_promo_btns.addWidget(self.btn_activar_promo)
        lay_promo_btns.addWidget(self.btn_quitar_promo)
        lay_ctrl.addLayout(lay_promo_btns)
        
        self.btn_imprimir_quick_cartel = QPushButton("🖨️ IMPRIMIR CARTEL (A4)")
        self.btn_imprimir_quick_cartel.setStyleSheet("""
            QPushButton {
                background-color: #EA580C; color: #FFFFFF; font-weight: 800; font-size: 11px;
                padding: 8px 15px; border-radius: 8px; border: none;
            }
            QPushButton:hover { background-color: #C2410C; }
        """)
        self.btn_imprimir_quick_cartel.clicked.connect(self._emit_imprimir_cartel)
        lay_ctrl.addWidget(self.btn_imprimir_quick_cartel)
        
        lay_ctrl.addStretch()
        
        self.scroll.setWidget(self.panel)
        root.addWidget(self.scroll)

        # Conectar simulador
        self.txt_quick_precio.valueChanged.connect(self._recargar_simulador)
        self.txt_quick_costo.valueChanged.connect(self._recargar_simulador)
        self.sp_quick_cant_oferta.valueChanged.connect(self._recargar_simulador)
        self.sp_quick_precio_oferta.valueChanged.connect(self._recargar_simulador)
        self.sp_quick_oferta_relampago.valueChanged.connect(self._recargar_simulador)
        self.sp_quick_oferta_promedio.valueChanged.connect(self._recargar_simulador)

    def aplicar_tema(self):
        self.panel.setStyleSheet("""
            QFrame#ControlCenter {
                background-color: #FFFFFF;
                border-left: 1px solid #E2E8F0;
            }
            QLabel { background: transparent; color: #334155; }
            QDoubleSpinBox, QLineEdit {
                background-color: #F8FAFC;
                color: #0F172A;
                border: 1px solid #CBD5E1;
            }
        """)

    def cargar_producto(self, p):
        if not p:
            self.producto_id = None
            self.lbl_prod_nombre.setText("Seleccione un producto...")
            self.lbl_prod_detalles.setText("ID: —  |  PLU: —")
            self.set_enabled(False)
            self._recargar_simulador()
            return
            
        self.producto_id = str(p['id'])
        self.lbl_prod_nombre.setText(p['nombre'])
        self.lbl_prod_detalles.setText(f"ID: {p['id']}  |  PLU: {p['codigo'] or 'Sin Código'}")
        
        self.txt_quick_precio.blockSignals(True)
        self.txt_quick_costo.blockSignals(True)
        self.sp_quick_cant_oferta.blockSignals(True)
        self.sp_quick_precio_oferta.blockSignals(True)
        self.sp_quick_oferta_relampago.blockSignals(True)
        self.sp_quick_oferta_promedio.blockSignals(True)
        
        self.txt_quick_precio.setValue(float(p['precio'] if p['precio'] is not None else 0.0))
        self.txt_quick_costo.setValue(float(p['costo'] if p['costo'] is not None else 0.0))
        self.txt_quick_stock.setValue(float(p['stock'] if p['stock'] is not None else 0.0))
        
        self.sp_quick_cant_oferta.setValue(float(p['cant_oferta'] if p['cant_oferta'] is not None else 0.0))
        self.sp_quick_precio_oferta.setValue(float(p['precio_oferta'] if p['precio_oferta'] is not None else 0.0))
        self.sp_quick_oferta_relampago.setValue(float(p.get('precio_oferta_relampago') if p.get('precio_oferta_relampago') is not None else 0.0))
        self.sp_quick_oferta_promedio.setValue(float(p.get('precio_oferta_promedio') if p.get('precio_oferta_promedio') is not None else 0.0))
        self.sp_limite_relampago.blockSignals(True)
        self.sp_limite_relampago.setValue(float(p.get('limite_oferta_relampago') if p.get('limite_oferta_relampago') is not None else 0.0))
        
        ventas = p.get('ventas_oferta_relampago') or 0
        limite = p.get('limite_oferta_relampago') or 0
        self.lbl_ventas_relampago.setText(f"Vendidos: {int(ventas)} / {int(limite) if limite > 0 else '∞'}")
        self.sp_limite_relampago.blockSignals(False)
        
        self.txt_quick_precio.blockSignals(False)
        self.txt_quick_costo.blockSignals(False)
        self.sp_quick_cant_oferta.blockSignals(False)
        self.sp_quick_precio_oferta.blockSignals(False)
        self.sp_quick_oferta_relampago.blockSignals(False)
        self.sp_quick_oferta_promedio.blockSignals(False)
            
        self.set_enabled(True)
        self._recargar_simulador()

    def set_enabled(self, val):
        self.panel.setEnabled(val)

    def _recargar_simulador(self):
        if not self.producto_id:
            self.lbl_margen_reg.setText("Margen Regular: —")
            self.lbl_margen_promo.setText("Margen Promo: —")
            self.lbl_ahorro_total.setText("Ahorro de Cliente: —")
            self.lbl_semaforo.setText("Seleccione un producto...")
            self.lbl_semaforo.setStyleSheet("font-size: 11px; font-weight: 800;  border: none; background-color: transparent; padding: 0;")
            return
            
        costo = self.txt_quick_costo.value()
        reg_precio = self.txt_quick_precio.value()
        promo_precio = self.sp_quick_precio_oferta.value()
        promo_cant = self.sp_quick_cant_oferta.value()
        
        if reg_precio > 0:
            margen_reg = ((reg_precio - costo) / reg_precio) * 100
            self.lbl_margen_reg.setText(f"Margen Regular: {margen_reg:.1f}%")
        else:
            self.lbl_margen_reg.setText("Margen Regular: 0.0%")
            
        if promo_precio > 0:
            margen_promo = ((promo_precio - costo) / promo_precio) * 100
            self.lbl_margen_promo.setText(f"Margen Promo: {margen_promo:.1f}%")
            
            ahorro = max(0.0, reg_precio - promo_precio) * promo_cant
            self.lbl_ahorro_total.setText(f"Ahorro Cliente por Compra: ${ahorro:.2f}")
            
            if promo_precio <= costo:
                self.lbl_semaforo.setText("🚨 PÉRDIDA: ¡OFERTA POR DEBAJO DEL COSTO!")
                self.lbl_semaforo.setStyleSheet("font-size: 10px; font-weight: 900; background-color: #FEE2E2; color: #B91C1C; border-radius: 4px; padding: 4px; border: none;")
            elif margen_promo < 10.0:
                self.lbl_semaforo.setText("⚠️ MARGEN CRÍTICO: RENTABILIDAD BAJA")
                self.lbl_semaforo.setStyleSheet("font-size: 10px; font-weight: 900; background-color: #FEF3C7; color: #92400E; border-radius: 4px; padding: 4px; border: none;")
            else:
                self.lbl_semaforo.setText("✅ PROMOCIÓN RENTABLE: RENTABILIDAD POSITIVA")
                self.lbl_semaforo.setStyleSheet("font-size: 10px; font-weight: 900; background-color: #DCFCE7; color: #166534; border-radius: 4px; padding: 4px; border: none;")
        else:
            self.lbl_margen_promo.setText("Margen Promo: —")
            self.lbl_ahorro_total.setText("Ahorro de Cliente: —")
            self.lbl_semaforo.setText("✅ Margen Regular Comercial")
            self.lbl_semaforo.setStyleSheet("font-size: 10px; font-weight: 900; background-color: #F1F5F9; color: #475569; border-radius: 4px; padding: 4px; border: none;")


    def _emit_activar_promo(self):
        if not self.producto_id: return
        
        precio_reg = self.txt_quick_precio.value()
        p_of = self.sp_quick_precio_oferta.value()
        p_rel = self.sp_quick_oferta_relampago.value()
        p_prom = self.sp_quick_oferta_promedio.value()
        
        if (p_of > 0 and p_of >= precio_reg) or \
           (p_rel > 0 and p_rel >= precio_reg) or \
           (p_prom > 0 and p_prom >= precio_reg):
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Error", "El precio de oferta no puede ser mayor o igual al precio de venta regular.")
            return
            
        data = {
            'id': self.producto_id,
            'cant_oferta': self.sp_quick_cant_oferta.value(),
            'precio_oferta': p_of,
            'precio_oferta_relampago': p_rel,
            'precio_oferta_promedio': p_prom,
            'limite_oferta_relampago': self.sp_limite_relampago.value(),
            'precio_regular': precio_reg
        }
        self.activar_promo.emit(data)

    def _emit_quitar_promo(self):
        if not self.producto_id: return
        self.quitar_promo.emit(self.producto_id)
        
    def _emit_imprimir_cartel(self):
        if not self.producto_id: return
        self.imprimir_cartel.emit(
            self.producto_id,
            self.sp_quick_cant_oferta.value(),
            self.sp_quick_precio_oferta.value()
        )
