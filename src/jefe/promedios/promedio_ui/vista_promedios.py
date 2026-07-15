from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
import datetime
from src.jefe.contabilidad.shared_globals import *
import json
import os

class VistaPromediosMixin:
    def _build_tab_promedios(self):
        lay, _ = self._page()
        
        # ESTADOS AUTO-GUARDADOS
        self._promedios_json_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "estado_promedios_borrador.json")
        default_estado = {
            "Carne": {"kilos": "", "merma": "", "precio": "", "filas": []},
            "Cerdo": {"kilos": "", "merma": "", "precio": "", "filas": []},
            "Pollo": {"kilos": "", "merma": "", "precio": "", "filas": []}
        }
        
        try:
            if os.path.exists(self._promedios_json_path):
                with open(self._promedios_json_path, "r", encoding="utf-8") as f:
                    self._estado_promedios = json.load(f)
            else:
                self._estado_promedios = default_estado
        except:
            self._estado_promedios = default_estado
            
        self._tipo_promedio = "Carne"
        
        botones_lay = QHBoxLayout()
        botones_lay.setSpacing(10)
        
        self._btn_tipo_carne = QPushButton("🥩 CARNE")
        self._btn_tipo_cerdo = QPushButton("🐖 CERDO")
        self._btn_tipo_pollo = QPushButton("🍗 POLLO")
        
        self._btn_tipo_carne.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_tipo_cerdo.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_tipo_pollo.setCursor(Qt.CursorShape.PointingHandCursor)
        
        self._btn_tipo_carne.clicked.connect(lambda: self._cambiar_tipo_promedio("Carne"))
        self._btn_tipo_cerdo.clicked.connect(lambda: self._cambiar_tipo_promedio("Cerdo"))
        self._btn_tipo_pollo.clicked.connect(lambda: self._cambiar_tipo_promedio("Pollo"))
        
        botones_lay.addWidget(self._btn_tipo_carne)
        botones_lay.addWidget(self._btn_tipo_cerdo)
        botones_lay.addWidget(self._btn_tipo_pollo)
        botones_lay.addStretch()
        lay.addLayout(botones_lay)

        self._costo_real_kg = 0.0

        cab = QHBoxLayout()
        self._prom_prov = input_field("Proveedor")
        self._prom_fecha = date_field()
        cab.addWidget(QLabel("Proveedor:"))
        cab.addWidget(self._prom_prov)
        cab.addStretch()
        cab.addWidget(QLabel("Fecha:"))
        cab.addWidget(self._prom_fecha)

        btn_guardar_hist = QPushButton("💾 Guardar Historial")
        btn_guardar_hist.setStyleSheet(f"QPushButton {{ background: {PAL['primary']}; color: white; border-radius: 6px; padding: 8px 12px; font-weight: bold; }}")
        btn_guardar_hist.clicked.connect(self._prom_guardar_historial)
        
        btn_cargar_hist = QPushButton("📂 Cargar Historial")
        btn_cargar_hist.setStyleSheet(f"QPushButton {{ background: {PAL['info']}; color: white; border-radius: 6px; padding: 8px 12px; font-weight: bold; }}")
        btn_cargar_hist.clicked.connect(self._prom_cargar_historial)

        cab.addSpacing(20)
        cab.addWidget(btn_guardar_hist)
        cab.addWidget(btn_cargar_hist)
        
        lay.addLayout(cab)

        media_frame = QFrame()
        media_frame.setStyleSheet(f"background: {PAL['surface']}; border: 1px solid {PAL['border']}; border-radius: 8px;")
        m_lay = QHBoxLayout(media_frame)
        m_lay.setContentsMargins(15, 15, 15, 15)
        
        self._prom_kilos = input_field("Kilos totales")
        self._prom_merma = input_field("Merma Auto (kg)")
        self._prom_merma.setReadOnly(True)
        self._prom_merma.setStyleSheet(f"QLineEdit {{ background: #E2E8F0; border: 1px solid #94A3B8; color: #DC2626; font-weight: bold; border-radius: 6px; padding: 8px; }}")
        
        self._prom_precio = input_field("Precio/kg compra")
        
        for qle in [self._prom_kilos, self._prom_precio, self._prom_prov]:
            qle.setStyleSheet(f"QLineEdit {{ background: #FFFFFF; border: 1px solid #94A3B8; color: #0F172A; border-radius: 6px; padding: 8px; font-weight: bold; }}")
        
        btn_calc = btn_primary("⚙️ Calcular Costo Base")
        btn_calc.clicked.connect(self._calc_media_res)
        
        self._prom_kilos.textChanged.connect(lambda: self._calc_media_res(quiet=True))
        self._prom_precio.textChanged.connect(lambda: self._calc_media_res(quiet=True))
        
        lbl_kilos = QLabel("Kilos:")
        lbl_merma = QLabel("Merma:")
        lbl_precio = QLabel("Precio/kg:")
        for lbl in [lbl_kilos, lbl_merma, lbl_precio]:
            lbl.setStyleSheet("QLabel { color: #0F172A; font-weight: bold; }")
            
        m_lay.addWidget(lbl_kilos)
        m_lay.addWidget(self._prom_kilos)
        m_lay.addWidget(lbl_merma)
        m_lay.addWidget(self._prom_merma)
        m_lay.addWidget(lbl_precio)
        m_lay.addWidget(self._prom_precio)
        m_lay.addStretch()
        m_lay.addWidget(btn_calc)
        lay.addWidget(media_frame)

        self._lbl_prom_costos = QLabel("Kilos útiles: 0.00 | Costo real kg: $0.00")
        self._lbl_prom_costos.setStyleSheet(f"QLabel {{ font-size: 16px; font-weight: 900; color: {PAL['danger']}; }}")
        lay.addWidget(self._lbl_prom_costos)

        # NUEVAS COLUMNAS (Sin Costo Total, con Oferta)
        self._prom_tabla = build_table(["Corte", "Kilos", "Costo $/kg", "% Ganancia", "Precio/kg Venta", "Oferta", "Cant. Oferta", "Venta Total", "Ganancia Neta"])
        self._prom_tabla.itemChanged.connect(self._on_prom_tabla_changed)
        lay.addWidget(self._prom_tabla)

        tot_lay = QHBoxLayout()
        self._lbl_prom_totales_normal = QLabel("Normal => Venta: $0.00 | Ganancia: $0.00")
        self._lbl_prom_totales_oferta = QLabel("Ofertas => Venta: $0.00 | Ganancia: $0.00")
        self._lbl_prom_totales_normal.setStyleSheet(f"QLabel {{ font-size: 15px; font-weight: 900; color: {PAL['success']}; }}")
        self._lbl_prom_totales_oferta.setStyleSheet(f"QLabel {{ font-size: 15px; font-weight: 900; color: {PAL['info']}; }}")
        
        lbl_vbox = QVBoxLayout()
        lbl_vbox.addWidget(self._lbl_prom_totales_normal)
        lbl_vbox.addWidget(self._lbl_prom_totales_oferta)
        
        btn_redondeo = QPushButton("Redondear Precios (500)")
        btn_redondeo.setStyleSheet(f"QPushButton {{ background: {PAL['warning']}; color: #0F172A; font-weight: bold; padding: 10px; border-radius: 6px; }}")
        btn_redondeo.clicked.connect(self._prom_redondear)
        
        btn_export = QPushButton("💾 Exportar a Inventario")
        btn_export.setStyleSheet("QPushButton { background: #0EA5E9; color: #ffffff; font-weight: bold; padding: 10px; border-radius: 6px; }")
        btn_export.clicked.connect(self._prom_exportar_inventario)
        
        btn_sync = QPushButton("🔄 Sincronizar")
        btn_sync.setStyleSheet("QPushButton { background: #10B981; color: #ffffff; font-weight: bold; padding: 10px; border-radius: 6px; }")
        btn_sync.clicked.connect(self._prom_sincronizar_inventario)

        btn_pdf_int = btn_primary("📄 PDF Interno")
        btn_pdf_int.clicked.connect(self._prom_pdf_interno)

        btn_pdf_cli = btn_primary("📄 PDF Público (Lista Precios)")
        btn_pdf_cli.clicked.connect(self._prom_pdf_clientes)

        tot_lay.addLayout(lbl_vbox)
        tot_lay.addStretch()
        tot_lay.addWidget(btn_sync)
        tot_lay.addWidget(btn_export)
        tot_lay.addWidget(btn_redondeo)
        tot_lay.addWidget(btn_pdf_int)
        tot_lay.addWidget(btn_pdf_cli)
        lay.addLayout(tot_lay)

        self._load_cortes_base()

    def _guardar_estado_actual(self):
        if not hasattr(self, '_prom_tabla'): return
        filas = []
        for r in range(self._prom_tabla.rowCount()):
            row_data = [self._prom_tabla.item(r, c).text() if self._prom_tabla.item(r, c) else "" for c in range(9)]
            filas.append(row_data)
        
        self._estado_promedios[self._tipo_promedio] = {
            "kilos": self._prom_kilos.text(),
            "merma": self._prom_merma.text(),
            "precio": self._prom_precio.text(),
            "filas": filas
        }

    def _cambiar_tipo_promedio(self, tipo):
        if hasattr(self, '_prom_tabla'):
            self._guardar_estado_actual()
            
        self._tipo_promedio = tipo
        active_style = f"QPushButton {{ background: {PAL['primary']}; color: white; border-radius: 8px; padding: 12px 24px; font-weight: bold; font-size: 14px; }}"
        inactive_style = "QPushButton { background: #E2E8F0; color: #0F172A; border: 1px solid #94A3B8; border-radius: 8px; padding: 12px 24px; font-weight: bold; font-size: 14px; }"
        
        self._btn_tipo_carne.setStyleSheet(active_style if tipo == "Carne" else inactive_style)
        self._btn_tipo_cerdo.setStyleSheet(active_style if tipo == "Cerdo" else inactive_style)
        self._btn_tipo_pollo.setStyleSheet(active_style if tipo == "Pollo" else inactive_style)
        
        self._load_cortes_base()

    def _load_cortes_base(self):
        self._prom_tabla.blockSignals(True)
        self._prom_tabla.setRowCount(0)
        
        estado = self._estado_promedios.get(self._tipo_promedio, {})
        filas = estado.get("filas", [])
        
        self._prom_kilos.setText(estado.get("kilos", ""))
        self._prom_merma.setText(estado.get("merma", ""))
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
import datetime
from src.jefe.contabilidad.shared_globals import *

class VistaPromediosMixin:
    def _build_tab_promedios(self):
        lay, _ = self._page()
        
        # ESTADOS
        self._estado_promedios = {
            "Carne_MediaRes": {"kilos": "", "merma": "", "precio": "", "filas": []},
            "Carne_Mocho": {"kilos": "", "merma": "", "precio": "", "filas": []},
            "Carne_Pecho": {"kilos": "", "merma": "", "precio": "", "filas": []},
            "Cerdo": {"kilos": "", "merma": "", "precio": "", "filas": []},
            "Pollo": {"kilos": "", "merma": "", "precio": "", "filas": []}
        }
        self._tipo_promedio = "Carne_MediaRes"
        
        botones_lay = QHBoxLayout()
        botones_lay.setSpacing(10)
        
        self._btn_tipo_carne = QPushButton("🥩 CARNE")
        self._btn_tipo_cerdo = QPushButton("🐖 CERDO")
        self._btn_tipo_pollo = QPushButton("🍗 POLLO")
        
        self._btn_tipo_carne.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_tipo_cerdo.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_tipo_pollo.setCursor(Qt.CursorShape.PointingHandCursor)
        
        self._btn_tipo_carne.clicked.connect(lambda: self._cambiar_tipo_promedio("Carne_MediaRes", from_main=True))
        self._btn_tipo_cerdo.clicked.connect(lambda: self._cambiar_tipo_promedio("Cerdo", from_main=True))
        self._btn_tipo_pollo.clicked.connect(lambda: self._cambiar_tipo_promedio("Pollo", from_main=True))
        
        botones_lay.addWidget(self._btn_tipo_carne)
        botones_lay.addWidget(self._btn_tipo_cerdo)
        botones_lay.addWidget(self._btn_tipo_pollo)
        botones_lay.addStretch()
        lay.addLayout(botones_lay)
        
        # Sub-menú para Carne
        self._submenu_carne = QWidget()
        self._submenu_carne_lay = QHBoxLayout(self._submenu_carne)
        self._submenu_carne_lay.setContentsMargins(0, 0, 0, 0)
        self._submenu_carne_lay.setSpacing(10)
        
        self._btn_sub_mediares = QPushButton("🐮 Media Res")
        self._btn_sub_mocho = QPushButton("🥩 Mocho")
        self._btn_sub_pecho = QPushButton("🥩 Pecho")
        
        self._btn_sub_mediares.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_sub_mocho.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_sub_pecho.setCursor(Qt.CursorShape.PointingHandCursor)
        
        # Style para diferenciar botones secundarios
        style_sub = f"QPushButton {{ background: {PAL.get('surface2', '#E2E8F0')}; color: {PAL['text']}; border: 1px solid {PAL['border']}; border-radius: 6px; padding: 6px 12px; font-weight: bold; font-size: 13px; }}"
        style_sub_hover = style_sub + f" QPushButton:hover {{ background: {PAL['border2']}; }}"
        self._btn_sub_mediares.setStyleSheet(style_sub_hover)
        self._btn_sub_mocho.setStyleSheet(style_sub_hover)
        self._btn_sub_pecho.setStyleSheet(style_sub_hover)
        
        self._btn_sub_mediares.clicked.connect(lambda: self._cambiar_tipo_promedio("Carne_MediaRes"))
        self._btn_sub_mocho.clicked.connect(lambda: self._cambiar_tipo_promedio("Carne_Mocho"))
        self._btn_sub_pecho.clicked.connect(lambda: self._cambiar_tipo_promedio("Carne_Pecho"))
        
        self._submenu_carne_lay.addWidget(self._btn_sub_mediares)
        self._submenu_carne_lay.addWidget(self._btn_sub_mocho)
        self._submenu_carne_lay.addWidget(self._btn_sub_pecho)
        self._submenu_carne_lay.addStretch()
        
        lay.addWidget(self._submenu_carne)

        self._costo_real_kg = 0.0

        cab = QHBoxLayout()
        self._prom_prov = input_field("Proveedor")
        self._prom_fecha = date_field()
        cab.addWidget(QLabel("Proveedor:"))
        cab.addWidget(self._prom_prov)
        cab.addStretch()
        cab.addWidget(QLabel("Fecha:"))
        cab.addWidget(self._prom_fecha)

        btn_guardar_hist = QPushButton("💾 Guardar Historial")
        btn_guardar_hist.setStyleSheet(f"QPushButton {{ background: {PAL['primary']}; color: white; border-radius: 6px; padding: 8px 12px; font-weight: bold; }}")
        btn_guardar_hist.clicked.connect(self._prom_guardar_historial)
        
        btn_cargar_hist = QPushButton("📂 Cargar Historial")
        btn_cargar_hist.setStyleSheet(f"QPushButton {{ background: {PAL['info']}; color: white; border-radius: 6px; padding: 8px 12px; font-weight: bold; }}")
        btn_cargar_hist.clicked.connect(self._prom_cargar_historial)

        cab.addSpacing(20)
        cab.addWidget(btn_guardar_hist)
        cab.addWidget(btn_cargar_hist)
        
        lay.addLayout(cab)

        media_frame = QFrame()
        media_frame.setStyleSheet(f"background: {PAL['surface']}; border: 1px solid {PAL['border']}; border-radius: 8px;")
        m_lay = QHBoxLayout(media_frame)
        m_lay.setContentsMargins(15, 15, 15, 15)
        
        self._prom_kilos = input_field("Kilos totales")
        self._prom_merma = input_field("Merma Auto (kg)")
        self._prom_merma.setReadOnly(True)
        self._prom_merma.setStyleSheet(f"QLineEdit {{ background: #E2E8F0; border: 1px solid #94A3B8; color: #DC2626; font-weight: bold; border-radius: 6px; padding: 8px; }}")
        
        self._prom_precio = input_field("Precio/kg")
        self._prom_costo_total = input_field("Costo Total $")
        
        for qle in [self._prom_kilos, self._prom_precio, self._prom_costo_total, self._prom_prov]:
            qle.setStyleSheet(f"QLineEdit {{ background: #FFFFFF; border: 1px solid #94A3B8; color: #0F172A; border-radius: 6px; padding: 8px; font-weight: bold; }}")
        
        btn_calc = btn_primary("⚙️ Calcular Costo Base")
        btn_calc.clicked.connect(self._calc_media_res)
        
        self._prom_kilos.textChanged.connect(self._sync_costo_total_from_precio)
        self._prom_precio.textChanged.connect(self._sync_costo_total_from_precio)
        self._prom_costo_total.textChanged.connect(self._sync_precio_from_costo_total)
        
        lbl_kilos = QLabel("Kilos:")
        lbl_merma = QLabel("Merma:")
        lbl_precio = QLabel("Precio/kg:")
        self._lbl_costo_tot = QLabel("Costo Total:")
        for lbl in [lbl_kilos, lbl_merma, lbl_precio, self._lbl_costo_tot]:
            lbl.setStyleSheet("QLabel { color: #0F172A; font-weight: bold; }")
            
        m_lay.addWidget(lbl_kilos)
        m_lay.addWidget(self._prom_kilos)
        m_lay.addWidget(lbl_merma)
        m_lay.addWidget(self._prom_merma)
        m_lay.addWidget(lbl_precio)
        m_lay.addWidget(self._prom_precio)
        m_lay.addWidget(self._lbl_costo_tot)
        m_lay.addWidget(self._prom_costo_total)
        m_lay.addStretch()
        m_lay.addWidget(btn_calc)
        lay.addWidget(media_frame)

        self._lbl_prom_costos = QLabel("Kilos útiles: 0.00 | Costo real kg: $0.00")
        self._lbl_prom_costos.setStyleSheet(f"QLabel {{ font-size: 16px; font-weight: 900; color: {PAL['danger']}; }}")
        lay.addWidget(self._lbl_prom_costos)

        # NUEVAS COLUMNAS (Sin Costo Total, con Oferta)
        self._prom_tabla = build_table(["Corte", "Kilos", "Costo $/kg", "% Ganancia", "Precio/kg Venta", "Oferta", "Cant. Oferta", "Venta Total", "Ganancia Neta"])
        self._prom_tabla.setEditTriggers(QAbstractItemView.EditTrigger.DoubleClicked | QAbstractItemView.EditTrigger.EditKeyPressed | QAbstractItemView.EditTrigger.AnyKeyPressed)
        self._prom_tabla.itemChanged.connect(self._on_prom_tabla_changed)
        lay.addWidget(self._prom_tabla)

        tot_lay = QHBoxLayout()
        self._lbl_prom_totales_normal = QLabel("Normal => Venta: $0.00 | Ganancia: $0.00")
        self._lbl_prom_totales_oferta = QLabel("Ofertas => Venta: $0.00 | Ganancia: $0.00")
        self._lbl_prom_totales_normal.setStyleSheet(f"QLabel {{ font-size: 15px; font-weight: 900; color: {PAL['success']}; }}")
        self._lbl_prom_totales_oferta.setStyleSheet(f"QLabel {{ font-size: 15px; font-weight: 900; color: {PAL['info']}; }}")
        
        lbl_vbox = QVBoxLayout()
        lbl_vbox.addWidget(self._lbl_prom_totales_normal)
        lbl_vbox.addWidget(self._lbl_prom_totales_oferta)
        
        btn_redondeo = QPushButton("Redondear Precios (500)")
        btn_redondeo.setStyleSheet(f"QPushButton {{ background: {PAL['warning']}; color: #0F172A; font-weight: bold; padding: 10px; border-radius: 6px; }}")
        btn_redondeo.clicked.connect(self._prom_redondear)
        
        btn_export = QPushButton("💾 Exportar a Inventario")
        btn_export.setStyleSheet("QPushButton { background: #0EA5E9; color: #ffffff; font-weight: bold; padding: 10px; border-radius: 6px; }")
        btn_export.clicked.connect(self._prom_exportar_inventario)
        
        btn_sync = QPushButton("🔄 Sincronizar")
        btn_sync.setStyleSheet("QPushButton { background: #10B981; color: #ffffff; font-weight: bold; padding: 10px; border-radius: 6px; }")
        btn_sync.clicked.connect(self._prom_sincronizar_inventario)

        btn_pdf_int = btn_primary("📄 PDF Interno")
        btn_pdf_int.clicked.connect(self._prom_pdf_interno)

        btn_pdf_cli = btn_primary("📄 PDF Público (Lista Precios)")
        btn_pdf_cli.clicked.connect(self._prom_pdf_clientes)

        tot_lay.addLayout(lbl_vbox)
        tot_lay.addStretch()
        tot_lay.addWidget(btn_sync)
        tot_lay.addWidget(btn_export)
        tot_lay.addWidget(btn_redondeo)
        tot_lay.addWidget(btn_pdf_int)
        tot_lay.addWidget(btn_pdf_cli)
        lay.addLayout(tot_lay)

        self._load_cortes_base()

    def _guardar_estado_actual(self):
        if not hasattr(self, '_prom_tabla'): return
        filas = []
        for r in range(self._prom_tabla.rowCount()):
            row_data = [self._prom_tabla.item(r, c).text() if self._prom_tabla.item(r, c) else "" for c in range(9)]
            filas.append(row_data)
        
        self._estado_promedios[self._tipo_promedio] = {
            "kilos": self._prom_kilos.text(),
            "merma": self._prom_merma.text(),
            "precio": self._prom_precio.text(),
            "costo_total": self._prom_costo_total.text(),
            "filas": filas
        }
        
        # Auto-guardado en JSON
        try:
            import json
            with open(self._promedios_json_path, "w", encoding="utf-8") as f:
                json.dump(self._estado_promedios, f, indent=4)
        except Exception as e:
            pass

    def _cambiar_tipo_promedio(self, tipo, from_main=False):
        if hasattr(self, '_prom_tabla'):
            self._guardar_estado_actual()
            
        self._tipo_promedio = tipo
        active_style = f"QPushButton {{ background: {PAL['primary']}; color: white; border-radius: 8px; padding: 12px 24px; font-weight: bold; font-size: 14px; }}"
        inactive_style = "QPushButton { background: #E2E8F0; color: #0F172A; border: 1px solid #94A3B8; border-radius: 8px; padding: 12px 24px; font-weight: bold; font-size: 14px; }"
        
        self._btn_tipo_carne.setStyleSheet(active_style if tipo.startswith("Carne") else inactive_style)
        self._btn_tipo_cerdo.setStyleSheet(active_style if tipo == "Cerdo" else inactive_style)
        self._btn_tipo_pollo.setStyleSheet(active_style if tipo == "Pollo" else inactive_style)
        
        if hasattr(self, '_submenu_carne'):
            self._submenu_carne.setVisible(tipo.startswith("Carne"))
            
            if tipo.startswith("Carne"):
                style_sub = f"QPushButton {{ background: {PAL.get('surface2', '#E2E8F0')}; color: {PAL['text']}; border: 1px solid {PAL['border']}; border-radius: 6px; padding: 6px 12px; font-weight: bold; font-size: 13px; }}"
                style_sub_hover = style_sub + f" QPushButton:hover {{ background: {PAL['border2']}; }}"
                style_sub_active = f"QPushButton {{ background: {PAL['primary']}; color: white; border: 1px solid {PAL['primary']}; border-radius: 6px; padding: 6px 12px; font-weight: bold; font-size: 13px; }}"
                
                self._btn_sub_mediares.setStyleSheet(style_sub_active if tipo == "Carne_MediaRes" else style_sub_hover)
                self._btn_sub_mocho.setStyleSheet(style_sub_active if tipo == "Carne_Mocho" else style_sub_hover)
                self._btn_sub_pecho.setStyleSheet(style_sub_active if tipo == "Carne_Pecho" else style_sub_hover)
        
        if tipo == "Pollo":
            self._lbl_costo_tot.setText("Costo Cajón ($):")
        else:
            self._lbl_costo_tot.setText("Costo Total ($):")
            
        self._load_cortes_base()

    def _load_cortes_base(self):
        self._prom_tabla.blockSignals(True)
        self._prom_tabla.setRowCount(0)
        
        estado = self._estado_promedios.get(self._tipo_promedio, {})
        filas = estado.get("filas", [])
        
        self._prom_kilos.setText(estado.get("kilos", ""))
        self._prom_merma.setText(estado.get("merma", ""))
        
        # Block signals so they don't sync recursively during load
        self._prom_precio.blockSignals(True)
        self._prom_costo_total.blockSignals(True)
        self._prom_precio.setText(estado.get("precio", ""))
        self._prom_costo_total.setText(estado.get("costo_total", ""))
        self._prom_precio.blockSignals(False)
        self._prom_costo_total.blockSignals(False)
        
        if filas:
            for i, row_data in enumerate(filas):
                self._prom_tabla.insertRow(i)
                for c in range(9):
                    val = str(row_data[c]) if c < len(row_data) else ""
                    it = QTableWidgetItem(val)
                    if c in [2, 7, 8]:
                        it.setFlags(it.flags() & ~Qt.ItemFlag.ItemIsEditable)
                        if c == 2: it.setForeground(QColor(PAL['text3']))
                    self._prom_tabla.setItem(i, c, it)
        else:
            cortes = []
            from src.jefe.promedios.promedio_motor.res import PromedioRes, PromedioMocho, PromedioPecho
            from src.jefe.promedios.promedio_motor.cerdo import PromedioCerdo
            from src.jefe.promedios.promedio_motor.pollo import PromedioPollo
            from src.jefe.promedios.promedio_motor.motor_promedios import MotorPromedios
            
            if self._tipo_promedio == "Carne_MediaRes":
                cortes = PromedioRes.get_cortes()
            elif self._tipo_promedio == "Carne_Mocho":
                cortes = PromedioMocho.get_cortes()
            elif self._tipo_promedio == "Carne_Pecho":
                cortes = PromedioPecho.get_cortes()
            elif self._tipo_promedio == "Cerdo":
                cortes = PromedioCerdo.get_cortes()
            elif self._tipo_promedio == "Pollo":
                cortes = PromedioPollo.get_cortes()
            
            for i, (corte, kilos, pct) in enumerate(cortes):
                self._prom_tabla.insertRow(i)
                
                it_corte = QTableWidgetItem(corte)
                self._prom_tabla.setItem(i, 0, it_corte)
                
                self._prom_tabla.setItem(i, 1, QTableWidgetItem(str(kilos)))
                
                it_costo = QTableWidgetItem("0.00")
                it_costo.setFlags(it_costo.flags() & ~Qt.ItemFlag.ItemIsEditable)
                it_costo.setForeground(QColor(PAL['text3']))
                self._prom_tabla.setItem(i, 2, it_costo)
                
                self._prom_tabla.setItem(i, 3, QTableWidgetItem(str(pct)))
                self._prom_tabla.setItem(i, 4, QTableWidgetItem("0.00"))
                self._prom_tabla.setItem(i, 5, QTableWidgetItem(""))
                self._prom_tabla.setItem(i, 6, QTableWidgetItem(""))
                
                it_venta = QTableWidgetItem("0.00")
                it_venta.setFlags(it_venta.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self._prom_tabla.setItem(i, 7, it_venta)
                
                it_ganancia = QTableWidgetItem("0.00")
                it_ganancia.setFlags(it_ganancia.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self._prom_tabla.setItem(i, 8, it_ganancia)
                
        self._add_empty_row()
        self._prom_tabla.blockSignals(False)
        self._calc_media_res(quiet=True, from_calc=(not bool(filas)))

    def _add_empty_row(self):
        i = self._prom_tabla.rowCount()
        self._prom_tabla.insertRow(i)
        
        self._prom_tabla.setItem(i, 0, QTableWidgetItem(""))
        self._prom_tabla.setItem(i, 1, QTableWidgetItem(""))
        
        it_costo = QTableWidgetItem("0.00")
        it_costo.setFlags(it_costo.flags() & ~Qt.ItemFlag.ItemIsEditable)
        it_costo.setForeground(QColor(PAL['text3']))
        self._prom_tabla.setItem(i, 2, it_costo)
        
        self._prom_tabla.setItem(i, 3, QTableWidgetItem(""))
        self._prom_tabla.setItem(i, 4, QTableWidgetItem(""))
        self._prom_tabla.setItem(i, 5, QTableWidgetItem(""))
        self._prom_tabla.setItem(i, 6, QTableWidgetItem(""))
        
        it_venta = QTableWidgetItem("0.00")
        it_venta.setFlags(it_venta.flags() & ~Qt.ItemFlag.ItemIsEditable)
        self._prom_tabla.setItem(i, 7, it_venta)
        
        it_ganancia = QTableWidgetItem("0.00")
        it_ganancia.setFlags(it_ganancia.flags() & ~Qt.ItemFlag.ItemIsEditable)
        self._prom_tabla.setItem(i, 8, it_ganancia)

    def _sync_costo_total_from_precio(self):
        if self._prom_costo_total.signalsBlocked(): return
        try:
            kilos = float(self._prom_kilos.text().replace(',', '.') or 0)
            precio_kg = float(self._prom_precio.text().replace(',', '.') or 0)
            if kilos > 0:
                self._prom_costo_total.blockSignals(True)
                self._prom_costo_total.setText(f"{kilos * precio_kg:.2f}")
                self._prom_costo_total.blockSignals(False)
        except: pass
        self._calc_media_res(quiet=True)

    def _sync_precio_from_costo_total(self):
        if self._prom_precio.signalsBlocked(): return
        try:
            kilos = float(self._prom_kilos.text().replace(',', '.') or 0)
            costo_tot = float(self._prom_costo_total.text().replace(',', '.') or 0)
            if kilos > 0:
                self._prom_precio.blockSignals(True)
                self._prom_precio.setText(f"{costo_tot / kilos:.2f}")
                self._prom_precio.blockSignals(False)
        except: pass
        self._calc_media_res(quiet=True)

    def _calc_media_res(self, quiet=False, from_calc=True):
        try:
            from src.jefe.promedios.promedio_motor.motor_promedios import MotorPromedios
            kilos_totales = float(self._prom_kilos.text().replace(',', '.') or "0")
            precio = float(self._prom_precio.text().replace(',', '.') or "0")
            
            suma_kilos = 0.0
            for r in range(self._prom_tabla.rowCount()):
                try: suma_kilos += float(self._prom_tabla.item(r, 1).text())
                except: pass
            
            merma_auto, kilos_utiles, costo_real_kg = MotorPromedios.calcular_media_res(kilos_totales, precio, suma_kilos)
            
            self._prom_merma.setText(f"{merma_auto:.2f}")
            self._kilos_utiles = kilos_utiles
            self._costo_real_kg = costo_real_kg
            
            self._lbl_prom_costos.setText(f"Kilos útiles: {self._kilos_utiles:.2f} kg | Costo real kg: ${self._costo_real_kg:,.2f}")
            self._on_prom_tabla_changed(None, from_calc=from_calc)
        except Exception as e:
            pass # Silent on load

    def _prom_redondear(self):
        import math
        if getattr(self, '_costo_real_kg', 0) == 0: return
        self._prom_tabla.blockSignals(True)
        for r in range(self._prom_tabla.rowCount()):
            try:
                precio_actual = float(self._prom_tabla.item(r, 4).text().replace(',', ''))
                if precio_actual > 0:
                    redondeado = math.ceil(precio_actual / 500) * 500
                    self._prom_tabla.setItem(r, 4, QTableWidgetItem(f"{redondeado:,.2f}"))
            except: pass
        self._prom_tabla.blockSignals(False)
        self._on_prom_tabla_changed(None)

    def _on_prom_tabla_changed(self, item, from_calc=False):
        if not hasattr(self, '_costo_real_kg'): self._costo_real_kg = 0.0
        self._prom_tabla.blockSignals(True)

        if item is not None:
            r = item.row()
            col = item.column()
            
            # --- VALIDACIÓN AUTOMÁTICA NUMÉRICA ---
            if col in [1, 3, 4, 5, 6]:
                txt = item.text().replace(',', '.')
                clean_txt = ''.join(c for c in txt if c.isdigit() or c in '.-')
                if clean_txt != item.text():
                    item.setText(clean_txt)
                    
            if col == 0 and r == self._prom_tabla.rowCount() - 1 and item.text().strip():
                self._prom_tabla.blockSignals(True)
                self._add_empty_row()
                self._prom_tabla.blockSignals(False)

            from src.jefe.promedios.promedio_motor.motor_promedios import MotorPromedios
            try:
                if col in [3, 4]:
                    val = float(item.text() or 0)
                    pct, precio_venta = MotorPromedios.recalcular_fila(col, val, self._costo_real_kg)
                    if col == 3:
                        self._prom_tabla.setItem(r, 4, QTableWidgetItem(f"{precio_venta:,.2f}"))
                    elif col == 4:
                        self._prom_tabla.setItem(r, 3, QTableWidgetItem(f"{pct:.2f}"))
                elif col == 1: # Kilos
                    self._calc_media_res(quiet=True, from_calc=True)
                    self._prom_tabla.blockSignals(False)
                    return # calc already loops
            except: pass

        t_venta_normal = 0.0
        t_ganancia_normal = 0.0
        t_venta_oferta = 0.0
        t_ganancia_oferta = 0.0
        suma_kilos_cortes = 0.0
        
        font_strike = QFont()
        font_strike.setStrikeOut(True)
        font_normal = QFont()
        font_normal.setStrikeOut(False)
        
        for r in range(self._prom_tabla.rowCount()):
            try:
                kilos = float(self._prom_tabla.item(r, 1).text() or 0)
                
                # If global cost changed, recalculate sale price from profit margin
                if self._costo_real_kg > 0:
                    if from_calc or col == 3: # % Ganancia was edited (or global recalculation)
                        pct = float(self._prom_tabla.item(r, 3).text() or 0)
                        precio_venta_base = self._costo_real_kg * (1 + pct / 100)
                        self._prom_tabla.setItem(r, 4, QTableWidgetItem(f"{precio_venta_base:,.2f}"))
                    elif col == 4: # Precio Venta was edited
                        precio_venta_base = float(self._prom_tabla.item(r, 4).text().replace(',','') or 0)
                        if precio_venta_base > 0:
                            pct = ((precio_venta_base / self._costo_real_kg) - 1) * 100
                            self._prom_tabla.setItem(r, 3, QTableWidgetItem(f"{pct:.2f}"))
                        else:
                            self._prom_tabla.setItem(r, 3, QTableWidgetItem("0.00"))
                    else:
                        precio_venta_base = float(self._prom_tabla.item(r, 4).text().replace(',','') or 0)
                else:
                    precio_venta_base = float(self._prom_tabla.item(r, 4).text().replace(',','') or 0)

                oferta_str = self._prom_tabla.item(r, 5).text().replace(',','').strip()
                precio_oferta = 0.0
                tiene_oferta = False
                if oferta_str:
                    try:
                        precio_oferta = float(oferta_str)
                        if precio_oferta > 0: tiene_oferta = True
                    except: pass
                
                it_venta = self._prom_tabla.item(r, 4)
                if tiene_oferta:
                    it_venta.setFont(font_strike)
                    it_venta.setForeground(QColor("#94A3B8"))
                else:
                    it_venta.setFont(font_normal)
                    it_venta.setForeground(QColor(PAL['text']))
                
                costo_tot = kilos * self._costo_real_kg
                
                # Normal Scenario
                venta_n = kilos * precio_venta_base
                gan_n = venta_n - costo_tot
                t_venta_normal += venta_n
                t_ganancia_normal += gan_n
                
                # Offer Scenario
                venta_o = kilos * (precio_oferta if tiene_oferta else precio_venta_base)
                gan_o = venta_o - costo_tot
                t_venta_oferta += venta_o
                t_ganancia_oferta += gan_o
                
                self._prom_tabla.setItem(r, 2, QTableWidgetItem(f"{self._costo_real_kg:,.2f}"))
                
                # Update row UI to show normal
                vi = QTableWidgetItem(f"{venta_n:,.2f}")
                vi.setForeground(QColor(PAL['success'] if gan_n >= 0 else PAL['danger']))
                self._prom_tabla.setItem(r, 7, vi)
                
                gi = QTableWidgetItem(f"{gan_n:,.2f}")
                gi.setForeground(QColor(PAL['success'] if gan_n >= 0 else PAL['danger']))
                self._prom_tabla.setItem(r, 8, gi)
                
                suma_kilos_cortes += kilos
            except Exception as e:
                pass
            
        try:
            kilos_totales = float(self._prom_kilos.text().replace(',', '.') or "0")
            if kilos_totales > 0:
                merma_auto = kilos_totales - suma_kilos_cortes
                self._prom_merma.setText(f"{merma_auto:.2f}")
        except: pass

        if hasattr(self, '_lbl_prom_totales_normal') and hasattr(self, '_lbl_prom_totales_oferta'):
            self._lbl_prom_totales_normal.setText(f"Normal => Venta: ${t_venta_normal:,.2f} | Ganancia: ${t_ganancia_normal:,.2f}")
            self._lbl_prom_totales_oferta.setText(f"Ofertas => Venta: ${t_venta_oferta:,.2f} | Ganancia: ${t_ganancia_oferta:,.2f}")

        self._prom_tabla.blockSignals(False)


    def _prom_exportar_inventario(self):
        pwd, ok = QInputDialog.getText(self, "Exportar Inventario", "Ingrese contraseña de Jefe para autorizar:", QLineEdit.Password)
        if not ok or not pwd: return
        
        from src.base_de_datos.database import DatabaseManager
        import hashlib
        db = DatabaseManager()
        pwd_hash = hashlib.sha256(pwd.encode()).hexdigest()
        res = db.execute_query("SELECT rol FROM usuarios WHERE pin = ? OR password_hash = ?", (pwd, pwd_hash))
        if not res or res[0]['rol'] != 'jefe':
            QMessageBox.critical(self, "Acceso Denegado", "Contraseña incorrecta o el usuario no es Jefe.")
            return
            
        try:
            self._guardar_estado_actual()
            from src.jefe.promedios.promedio_motor.motor_promedios import MotorPromedios
            
            actualizados = MotorPromedios.exportar_a_inventario(db, self._tipo_promedio, self._estado_promedios)
            QMessageBox.information(self, "Éxito", f"Se exportaron los precios de {actualizados} cortes al inventario general.")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Fallo la exportación: {e}")

    def _prom_sincronizar_inventario(self):
        from src.base_de_datos.database import DatabaseManager
        db = DatabaseManager()
        
        try:
            self._guardar_estado_actual()
            from src.jefe.promedios.promedio_motor.motor_promedios import MotorPromedios
            
            actualizados = MotorPromedios.sincronizar_inventario(db, self._tipo_promedio, self._estado_promedios)
            
            self._load_cortes_base()
            QMessageBox.information(self, "Sincronizado", f"Se han importado los precios de {actualizados} cortes desde el inventario.")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Fallo la sincronización: {e}")

    def _prom_pdf_interno(self):
        try:
            from src.creador_pdf_global.motor_pdf_promedios import exportar_pdf_interno
            kilos = float(self._prom_kilos.text().replace(',', '.') or 0)
            merma = float(self._prom_merma.text().replace(',', '.') or 0)
            precio = float(self._prom_precio.text().replace(',', '.') or 0)
            exportar_pdf_interno(self._prom_tabla, self._prom_prov.text(), self._prom_fecha.date().toString("yyyy-MM-dd"), kilos, merma, precio, self)
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Fallo al abrir PDF interno: {e}")

    def _prom_pdf_clientes(self):
        try:
            from src.creador_pdf_global.motor_pdf_promedios import exportar_pdf_clientes
            exportar_pdf_clientes(self._prom_tabla, self._prom_prov.text(), self._prom_fecha.date().toString("yyyy-MM-dd"), self)
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Fallo al abrir PDF público: {e}")

    def _prom_guardar_historial(self):
        prov = self._prom_prov.text().strip()
        if not prov:
            QMessageBox.warning(self, "Datos Incompletos", "Ingrese el nombre del proveedor para guardar el historial.")
            return
            
        self._guardar_estado_actual()
        fecha_str = self._prom_fecha.date().toString("dd/MM/yyyy")
        
        from src.base_de_datos.database import DatabaseManager
        db = DatabaseManager()
        from src.jefe.promedios.promedio_motor.motor_promedios import MotorPromedios
        
        estado = self._estado_promedios.get(self._tipo_promedio)
        if not estado: return
        
        if MotorPromedios.guardar_historial(db, self._tipo_promedio, estado, prov, fecha_str):
            QMessageBox.information(self, "Guardado", "El cálculo ha sido guardado en el historial exitosamente.")
        else:
            QMessageBox.warning(self, "Error", "No se pudo guardar el historial. Asegúrese de que kilos y precio de compra sean mayores a 0.")

    def _prom_cargar_historial(self):
        from src.base_de_datos.database import DatabaseManager
        db = DatabaseManager()
        from src.jefe.promedios.promedio_motor.motor_promedios import MotorPromedios
        
        historial = MotorPromedios.obtener_historial(db, self._tipo_promedio)
        
        if not historial:
            QMessageBox.information(self, "Historial Vacío", f"No hay configuraciones guardadas para {self._tipo_promedio}.")
            return
            
        dlg = QDialog(self)
        dlg.setWindowTitle(f"Historial de {self._tipo_promedio}")
        dlg.setMinimumSize(600, 400)
        lay = QVBoxLayout(dlg)
        
        lista = QListWidget()
        lista.setStyleSheet("QListWidget { font-size: 14px; } QListWidget::item { padding: 10px; border-bottom: 1px solid #ccc; }")
        
        for row in historial:
            texto = f"[{row.get('fecha', '')}] {row.get('proveedor', '')} - Kilos: {row.get('kilos', 0):g} - Costo/kg: ${row.get('precio', 0):,.2f}"
            it = QListWidgetItem(texto)
            it.setData(Qt.ItemDataRole.UserRole, row)
            lista.addItem(it)
            
        lay.addWidget(lista)
        
        btn_cargar = btn_primary("Cargar Seleccionado")
        btn_cargar.clicked.connect(dlg.accept)
        lay.addWidget(btn_cargar)
        
        lista.itemDoubleClicked.connect(dlg.accept)
        
        if dlg.exec() == QDialog.DialogCode.Accepted:
            sel = lista.currentItem()
            if not sel: return
            
            data = sel.data(Qt.ItemDataRole.UserRole)
            try:
                self._estado_promedios[self._tipo_promedio] = {
                    "kilos": str(data.get('kilos', 0)),
                    "merma": "",
                    "precio": str(data.get('precio', 0)),
                    "filas": data.get('filas', [])
                }
                
                self._prom_prov.setText(data.get('proveedor', ''))
                try:
                    from datetime import datetime
                    fecha_str = data.get('fecha', '')
                    if "-" in fecha_str:
                        fecha_obj = datetime.strptime(fecha_str, "%Y-%m-%d").date()
                    else:
                        fecha_obj = datetime.strptime(fecha_str, "%d/%m/%Y").date()
                    self._prom_fecha.setDate(QDate(fecha_obj.year, fecha_obj.month, fecha_obj.day))
                except Exception as ex: print(ex)
                
                self._load_cortes_base()
                QMessageBox.information(self, "Recuperado", "Configuración restaurada con éxito.")
            except Exception as e:
                import traceback
                err_str = traceback.format_exc()
                QMessageBox.warning(self, "Error", f"No se pudo restaurar el historial:\n{e}\n\nDetalles:\n{err_str}")


    # ─────────────────────────────────────────────────────────────────────────
