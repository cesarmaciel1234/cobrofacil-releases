import os

# --- 1. JEFE CONTABILIDAD ---
jc_path = "src/jefe/jefe_contabilidad.py"
with open(jc_path, "r", encoding="utf-8") as f:
    jc = f.read()

# Add Shadow to KpiCard
if "QGraphicsDropShadowEffect" not in jc.split("def kpi_card")[1][:500]:
    jc = jc.replace("return card\n\ndef build_table(headers):", """
    from PyQt5.QtWidgets import QGraphicsDropShadowEffect
    from PyQt5.QtGui import QColor
    sh = QGraphicsDropShadowEffect()
    sh.setBlurRadius(30)
    sh.setColor(QColor(0, 0, 0, 15))
    sh.setOffset(0, 8)
    card.setGraphicsEffect(sh)
    return card

def build_table(headers):""")

# Enhance KpiCard style
jc = jc.replace("border-radius: 12px;", "border-radius: 16px;")
jc = jc.replace("border-left: 4px solid {color};", "border-top: 4px solid {color};")
jc = jc.replace("font-size: 26px;", "font-size: 32px;")

# Enhance Button Primary
jc = jc.replace("background: {PAL['primary']}; color: #fff;", "background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 {PAL['primary']}, stop:1 {PAL['primary_h']}); color: #fff;")

# Enhance Table
jc = jc.replace("border-radius: 10px;", "border-radius: 16px;")
jc = jc.replace("font-size: 11px;", "font-size: 13px; text-transform: uppercase;")
jc = jc.replace("alternate-background-color: {PAL['surface2']};", "alternate-background-color: #F8FAFC;")

with open(jc_path, "w", encoding="utf-8") as f:
    f.write(jc)


# --- 2. JEFE REPORTES ---
jr_path = "src/jefe/jefe_reportes.py"
with open(jr_path, "r", encoding="utf-8") as f:
    jr = f.read()

# Add Shadow to create_kpi
if "QGraphicsDropShadowEffect" not in jr.split("def create_kpi")[1][:1000]:
    jr = jr.replace("return w\n            \n        self.kpi_layout.addWidget(create_kpi(\"Ventas Totales\", f\"${v_bruta:,.2f}\"), 0, 0)", """
            from PyQt5.QtWidgets import QGraphicsDropShadowEffect
            from PyQt5.QtGui import QColor
            sh = QGraphicsDropShadowEffect()
            sh.setBlurRadius(30)
            sh.setColor(QColor(0, 0, 0, 15))
            sh.setOffset(0, 8)
            w.setGraphicsEffect(sh)
            return w
            
        self.kpi_layout.addWidget(create_kpi("Ventas Totales", f"${v_bruta:,.2f}"), 0, 0)""")

# Round borders KPI
jr = jr.replace("border-radius: 12px;", "border-radius: 18px;")
jr = jr.replace("font-size: 28px;", "font-size: 34px;")

# Improve main table style inside Reportes
jr = jr.replace("border-bottom: 1px solid #F1F5F9;", "border-bottom: 1px solid #F8FAFC;")
jr = jr.replace("QTableWidget::item { padding: 10px;", "QTableWidget::item { padding: 14px;")

# Add Shadow to Card Wrappers inside setup_ui of JefeReportes
if "self.card_vtas_tiempo.setGraphicsEffect" not in jr:
    jr = jr.replace("self.card_vtas_tiempo.setStyleSheet(card_style)", """self.card_vtas_tiempo.setStyleSheet(card_style)
        from PyQt5.QtWidgets import QGraphicsDropShadowEffect
        from PyQt5.QtGui import QColor
        sh2 = QGraphicsDropShadowEffect()
        sh2.setBlurRadius(30)
        sh2.setColor(QColor(0, 0, 0, 12))
        sh2.setOffset(0, 6)
        self.card_vtas_tiempo.setGraphicsEffect(sh2)""")

if "self.card_vtas_depto.setGraphicsEffect" not in jr:
    jr = jr.replace("self.card_vtas_depto.setStyleSheet(card_style)", """self.card_vtas_depto.setStyleSheet(card_style)
        sh3 = QGraphicsDropShadowEffect()
        sh3.setBlurRadius(30)
        sh3.setColor(QColor(0, 0, 0, 12))
        sh3.setOffset(0, 6)
        self.card_vtas_depto.setGraphicsEffect(sh3)""")

# Add shadow to cajeros card and estrellas card if they use card_style
if "self.card_cajeros.setGraphicsEffect" not in jr:
    jr = jr.replace("self.card_cajeros, self.tabla_cajeros, _ = self._crear_tabla_estilizada(\"🏆 Ranking de Cajeros\", 3)", """self.card_cajeros, self.tabla_cajeros, _ = self._crear_tabla_estilizada("🏆 Ranking de Cajeros", 3)
        sh4 = QGraphicsDropShadowEffect()
        sh4.setBlurRadius(30)
        sh4.setColor(QColor(0, 0, 0, 12))
        sh4.setOffset(0, 6)
        self.card_cajeros.setGraphicsEffect(sh4)""")

if "self.card_estrellas.setGraphicsEffect" not in jr:
    jr = jr.replace("self.card_estrellas, self.tabla_estrellas, _ = self._crear_tabla_estilizada(\"⭐ Top 5 Productos Estrella\", 3)", """self.card_estrellas, self.tabla_estrellas, _ = self._crear_tabla_estilizada("⭐ Top 5 Productos Estrella", 3)
        sh5 = QGraphicsDropShadowEffect()
        sh5.setBlurRadius(30)
        sh5.setColor(QColor(0, 0, 0, 12))
        sh5.setOffset(0, 6)
        self.card_estrellas.setGraphicsEffect(sh5)""")

with open(jr_path, "w", encoding="utf-8") as f:
    f.write(jr)

print("UI Remodel script finished!")
