# src/jefe/componentes_visuales/panel_alertas_ia.py
from PyQt6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
from PyQt6.QtCore import Qt, QTimer
try:
    from src.base_de_datos.database import db_manager
except ImportError:
    db_manager = None

class PanelAlertasIA(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("PanelIA")
        self.setStyleSheet("""
            QFrame#PanelIA {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #1E293B, stop:1 #0F172A);
                border-radius: 20px;
                border: 1px solid #334155;
            }
        """)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(25, 25, 25, 25)
        lay.setSpacing(15)

        # Header IA
        h_head = QHBoxLayout()
        lbl_ico = QLabel("🧠")
        lbl_ico.setStyleSheet("font-size: 24px; background: transparent; border: none;")
        h_head.addWidget(lbl_ico)

        lbl_tit = QLabel("ASESOR DE I.A. PREDICTIVO")
        lbl_tit.setStyleSheet("color: #E2E8F0; font-size: 14px; font-weight: 900; letter-spacing: 2px; background: transparent; border: none;")
        h_head.addWidget(lbl_tit)
        h_head.addStretch()

        self.btn_recalcular = QPushButton("🔄 ANALIZAR AHORA")
        self.btn_recalcular.setCursor(Qt.PointingHandCursor)
        self.btn_recalcular.setStyleSheet("""
            QPushButton {
                background: transparent; color: #818CF8; border: 1px solid #818CF8; border-radius: 8px; padding: 6px 12px; font-weight: 900; font-size: 10px;
            }
            QPushButton:hover { background: #818CF8; color: white; }
        """)
        self.btn_recalcular.clicked.connect(self.analizar)
        h_head.addWidget(self.btn_recalcular)
        lay.addLayout(h_head)

        # Contenedor de Alertas
        self.alertas_lay = QVBoxLayout()
        self.alertas_lay.setSpacing(10)
        lay.addLayout(self.alertas_lay)

        # Analizar al inicio
        QTimer.singleShot(500, self.analizar)

    def analizar(self):
        # Limpiar alertas anteriores
        while self.alertas_lay.count():
            item = self.alertas_lay.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
                
        if not db_manager:
            return

        # 1. Traer todos los productos y su stock actual
        try:
            prods = db_manager.execute_query("SELECT nombre, cantidad, departamento FROM productos WHERE tipo_venta != 'Servicio'") or []
        except Exception:
            prods = []

        stock_actual = {}
        for p in prods:
            stock_actual[p['nombre']] = p['cantidad']

        # 2. Calcular Velocidad de Venta (Últimos 7 días)
        try:
            query = """
                SELECT d.nombre_producto, SUM(d.cantidad) as total_vendido
                FROM detalles_ventas d
                JOIN ventas v ON d.id_venta = v.id
                WHERE v.fecha >= date('now', '-7 days') AND v.estado = 'COMPLETADA'
                GROUP BY d.nombre_producto
            """
            ventas_7d = db_manager.execute_query(query) or []
        except Exception:
            ventas_7d = []

        velocidad = {}
        for v in ventas_7d:
            velocidad[v['nombre_producto']] = v['total_vendido'] / 7.0

        alertas_generadas = []

        # 3. Detectar Quiebres y Estancamientos
        for nombre, vel_diaria in velocidad.items():
            if vel_diaria > 0:
                stock = float(stock_actual.get(nombre, 0.0))
                dias_restantes = stock / vel_diaria
                
                # Quiebre inminente (< 2 días)
                if dias_restantes < 2.0 and stock > 0:
                    alertas_generadas.append({
                        "tipo": "roja",
                        "titulo": f"Quiebre Inminente: {nombre}",
                        "desc": f"Se agotará en {dias_restantes:.1f} días al ritmo actual de venta ({vel_diaria:.1f}/día). Stock: {stock:.1f}."
                    })
                # Estancamiento (> 30 días)
                elif dias_restantes > 30.0 and stock > 0:
                    alertas_generadas.append({
                        "tipo": "azul",
                        "titulo": f"Estancamiento: {nombre}",
                        "desc": f"El stock actual durará {dias_restantes:.0f} días ({vel_diaria:.1f}/día). Sugerimos lanzar una OFERTA RELÁMPAGO."
                    })

        # Mostrar top 3 alertas o mensaje vacío
        if not alertas_generadas:
            lbl = QLabel("✅ Sin anomalías detectadas en los flujos de inventario.")
            lbl.setStyleSheet("color: #34D399; font-weight: bold; font-size: 13px; background: transparent; border: none; padding: 10px;")
            self.alertas_lay.addWidget(lbl)
        else:
            # Ordenar rojas primero
            alertas_generadas.sort(key=lambda x: 0 if x["tipo"] == "roja" else 1)
            for a in alertas_generadas[:3]:
                self.alertas_lay.addWidget(self._crear_tarjeta_alerta(a))

    def _crear_tarjeta_alerta(self, alerta):
        card = QFrame()
        bg_col = "rgba(239, 68, 68, 0.15)" if alerta["tipo"] == "roja" else "rgba(59, 130, 246, 0.15)"
        br_col = "#EF4444" if alerta["tipo"] == "roja" else "#3B82F6"
        icon_txt = "🔴" if alerta["tipo"] == "roja" else "🔵"

        card.setStyleSheet(f"""
            QFrame {{
                background: {bg_col}; border-left: 4px solid {br_col}; border-radius: 8px; padding: 12px;
            }}
        """)
        lay = QVBoxLayout(card)
        lay.setContentsMargins(15, 10, 15, 10)
        lay.setSpacing(5)

        lbl_t = QLabel(f"{icon_txt} {alerta['titulo']}")
        lbl_t.setStyleSheet("color: white; font-weight: 900; font-size: 13px; background: transparent; border: none;")
        lay.addWidget(lbl_t)

        lbl_d = QLabel(alerta['desc'])
        lbl_d.setWordWrap(True)
        lbl_d.setStyleSheet("color: rgba(255,255,255,0.7); font-size: 11px; background: transparent; border: none;")
        lay.addWidget(lbl_d)

        return card
