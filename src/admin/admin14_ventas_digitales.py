"""
admin14_ventas_digitales.py
Centro de Ventas Digitales — Panel Fiscal Unificado
----------------------------------------------------
Gestiona e integra cobros de:
  • Mercado Pago (CSV oficial + capturado por el sistema)
  • Banco Provincia / Cuenta DNI (CSV exportado)
  • Cualquier otro medio digital (CSV genérico)

Estructura de carpetas creada automáticamente:
  reportes/ventas_digitales/
  ├── originales/           ← CSVs descargados sin modificar de cada plataforma
  │   ├── mercadopago/
  │   └── banco_provincia/
  ├── sistema/              ← CSV generado por el programa en tiempo real
  │   └── mercado_pago_sync.csv  (copiado simbólicamente)
  └── consolidado/          ← Archivo maestro unificado para el fisco
      └── ventas_digitales_YYYY-MM.csv
"""
import os
import csv
import json
import shutil
from datetime import datetime
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QFrame,
    QFileDialog, QMessageBox, QTabWidget, QGraphicsDropShadowEffect,
    QComboBox, QLineEdit, QDateEdit, QCheckBox
)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QColor, QFont, QBrush

# ── Rutas base ──────────────────────────────────────────────────────────────
RAIZ_VENTAS = os.path.join("reportes", "ventas_digitales")
DIR_ORIGINALES_MP   = os.path.join(RAIZ_VENTAS, "originales", "mercadopago")
DIR_ORIGINALES_BP   = os.path.join(RAIZ_VENTAS, "originales", "banco_provincia")
DIR_SISTEMA         = os.path.join(RAIZ_VENTAS, "sistema")
DIR_CONSOLIDADO     = os.path.join(RAIZ_VENTAS, "consolidado")
CSV_SISTEMA_SRC     = os.path.join("reportes", "mercado_pago_sync.csv")

def crear_estructura():
    for d in [DIR_ORIGINALES_MP, DIR_ORIGINALES_BP, DIR_SISTEMA, DIR_CONSOLIDADO]:
        os.makedirs(d, exist_ok=True)


# ── Helpers de parseo ────────────────────────────────────────────────────────
def limpiar_monto(s: str) -> float:
    """Convierte '$1.234,56' o '1234.56' o '1.234,56' a float."""
    s = str(s).strip().replace(" ", "")
    s = s.replace("$", "").replace("\xa0", "")
    # formato argentino: 1.234,56
    if "," in s and "." in s:
        s = s.replace(".", "").replace(",", ".")
    elif "," in s:
        s = s.replace(",", ".")
    try:
        return float(s)
    except:
        return 0.0


def normalizar_fecha(s: str) -> str:
    """Devuelve YYYY-MM-DD HH:MM:SS o YYYY-MM-DD lo mejor posible."""
    s = s.strip()
    for fmt in [
        "%Y-%m-%dT%H:%M:%S.%f%z", "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%d %H:%M:%S", "%Y-%m-%d",
        "%d/%m/%Y %H:%M:%S", "%d/%m/%Y",
        "%d-%m-%Y %H:%M:%S", "%d-%m-%Y",
    ]:
        try:
            dt = datetime.strptime(s[:len(fmt)], fmt)
            return dt.strftime("%Y-%m-%d %H:%M:%S")
        except:
            pass
    return s


# ─────────────────────────────────────────────────────────────────────────────
def load_bank_dataframe(path: str):
    import pandas as pd
    try:
        if path.lower().endswith(('.xls', '.xlsx')):
            try:
                df = pd.read_excel(path, header=None)
            except Exception as e1:
                import logging
                logging.getLogger(__name__).error(f"Fallo read_excel para {path}: {e1}")
                try:
                    df = pd.read_html(path, decimal=',', thousands='.')[0]
                except Exception as e2:
                    logging.getLogger(__name__).error(f"Fallo read_html para {path}: {e2}")
                    df = pd.read_csv(path, header=None, encoding="utf-8-sig", on_bad_lines="skip")
        else:
            df = pd.read_csv(path, header=None, encoding="utf-8-sig", on_bad_lines="skip", sep=None, engine='python')
            
        header_idx = 0
        max_keywords = 0
        keywords = {"fecha", "date", "importe", "monto", "amount", "descripcion", "concepto", "detalle", "estado", "referencia", "operacion"}
        
        for i, row in df.head(30).iterrows():
            row_str = " ".join([str(x).lower() for x in row.values])
            matches = sum(1 for k in keywords if k in row_str)
            if matches > max_keywords and matches >= 2:
                max_keywords = matches
                header_idx = i
                
        if max_keywords >= 2:
            df.columns = [str(c).strip().lower() for c in df.iloc[header_idx].values]
            df = df.iloc[header_idx+1:].reset_index(drop=True)
        else:
            df.columns = [str(c).strip().lower() for c in df.iloc[0].values]
            df = df.iloc[1:].reset_index(drop=True)
            
        return df
    except Exception as e:
        print(f"Error load_bank_dataframe {path}: {e}")
        return pd.DataFrame()

# ─────────────────────────────────────────────────────────────────────────────
# Parser Mercado Pago CSV oficial
# Columnas típicas del CSV de MP:
#   Fecha de cobro, Descripción, ID de pago, Tipo, Monto bruto, Cargo, Monto neto, Estado
# ─────────────────────────────────────────────────────────────────────────────
def parsear_csv_mercado_pago(path: str) -> list:
    import pandas as pd
    filas = []
    df = load_bank_dataframe(path)
    if df.empty:
        return []
    
    def col(names):
        for fn in df.columns:
            for n in names:
                if n in fn:
                    return fn
        return None
        
    col_fecha  = col(["fecha", "date"])
    col_id     = col(["id", "referencia", "operacion"])
    col_bruto  = col(["bruto", "amount", "monto"])
    col_neto   = col(["neto", "net"])
    col_cargo  = col(["cargo", "fee", "comision"])
    col_estado = col(["estado", "status"])
    col_desc   = col(["descripcion", "description", "detalle"])

    for _, row in df.iterrows():
        fecha  = normalizar_fecha(str(row.get(col_fecha, "")) if pd.notna(row.get(col_fecha)) else "")
        id_p   = str(row.get(col_id, "")).strip() if pd.notna(row.get(col_id)) else ""
        bruto  = limpiar_monto(str(row.get(col_bruto, "0")) if pd.notna(row.get(col_bruto)) else "0")
        neto   = limpiar_monto(str(row.get(col_neto, "0")) if pd.notna(row.get(col_neto)) else "0")
        cargo  = limpiar_monto(str(row.get(col_cargo, "0")) if pd.notna(row.get(col_cargo)) else "0")
        estado = str(row.get(col_estado, "approved") if pd.notna(row.get(col_estado)) else "approved").upper()
        desc   = str(row.get(col_desc, "")).strip() if pd.notna(row.get(col_desc)) else ""
        
        if bruto == 0 and neto == 0:
            continue
        if not id_p:
            id_p = f"MP-{fecha}-{bruto}"
        
        filas.append({
            "fecha": fecha, "id": id_p, "bruto": bruto,
            "neto": neto if neto else bruto - cargo,
            "cargo": cargo, "estado": estado,
            "fuente": "Mercado Pago (CSV/Excel oficial)", "desc": desc
        })
    return filas


# ─────────────────────────────────────────────────────────────────────────────
# Parser Banco Provincia / Cuenta DNI CSV
# Columnas típicas del extracto:
#   Fecha, Número de operación, Descripción, Importe, Saldo
# ─────────────────────────────────────────────────────────────────────────────
def parsear_csv_banco_provincia(path: str) -> list:
    import pandas as pd
    filas = []
    df = load_bank_dataframe(path)
    if df.empty:
        return []
        
    def col(names):
        for fn in df.columns:
            for n in names:
                if n in fn:
                    return fn
        return None
        
    col_fecha  = col(["fecha", "date"])
    col_id     = col(["numero", "id", "referencia", "operacion", "n°", "nro"])
    col_importe= col(["importe", "credito", "monto", "amount", "cobro", "haber"])
    col_desc   = col(["descripcion", "concepto", "detalle", "movimiento"])
    
    for _, row in df.iterrows():
        fecha   = normalizar_fecha(str(row.get(col_fecha, "")) if pd.notna(row.get(col_fecha)) else "")
        id_p    = str(row.get(col_id, "")).strip() if pd.notna(row.get(col_id)) else ""
        importe = limpiar_monto(str(row.get(col_importe, "0")) if pd.notna(row.get(col_importe)) else "0")
        desc    = str(row.get(col_desc, "")).strip() if pd.notna(row.get(col_desc)) else ""
        
        if importe <= 0:
            continue
        if not id_p:
            id_p = f"BP-{fecha}-{importe}"
        
        filas.append({
            "fecha": fecha, "id": id_p, "bruto": importe,
            "neto": importe,
            "cargo": 0.0, "estado": "APPROVED",
            "fuente": "Banco Provincia / Cuenta DNI", "desc": desc
        })
    return filas


# ─────────────────────────────────────────────────────────────────────────────
# Parser CSV generado por el sistema (admin10_mp.py)
# ─────────────────────────────────────────────────────────────────────────────
def parsear_csv_sistema(path: str) -> list:
    filas = []
    if not os.path.exists(path):
        return filas
    with open(path, encoding="utf-8-sig", errors="replace") as f:
        reader = csv.reader(f)
        header = next(reader, None)
        for row in reader:
            if not row or len(row) < 6:
                continue
            if "SIMULADO" in row[1]:
                continue
            op_type = row[7].strip() if len(row) > 7 else "regular_payment"
            if op_type == "account_fund":
                continue
            estado = row[5].strip().upper()
            if estado not in ("APPROVED", "approved"):
                continue
            fecha = row[0].strip()
            id_p  = row[1].strip()
            bruto = limpiar_monto(row[2])
            neto  = limpiar_monto(row[8]) if len(row) > 8 else bruto
            cargo = bruto - neto
            filas.append({
                "fecha": fecha, "id": id_p, "bruto": bruto,
                "neto": neto, "cargo": cargo, "estado": "APPROVED",
                "fuente": "Sistema (captura en tiempo real)", "desc": row[3].strip()
            })
    return filas


# ─────────────────────────────────────────────────────────────────────────────
# Generar CSV consolidado del mes
# ─────────────────────────────────────────────────────────────────────────────
def generar_csv_consolidado(mes_str: str, filas: list) -> str:
    crear_estructura()
    path = os.path.join(DIR_CONSOLIDADO, f"ventas_digitales_{mes_str}.csv")
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["Fecha", "ID Operacion", "Descripcion", "Fuente",
                    "Monto Bruto", "Monto Neto", "Cargo/Comision", "Estado"])
        for p in filas:
            w.writerow([
                p["fecha"], p["id"], p.get("desc", ""), p["fuente"],
                f"{p['bruto']:.2f}", f"{p['neto']:.2f}", f"{p['cargo']:.2f}", p["estado"]
            ])
    return path


# ═════════════════════════════════════════════════════════════════════════════
class Admin14VentasDigitales(QWidget):
    """
    Módulo fiscal de ventas digitales.
    Unifica Mercado Pago + Banco Provincia en una vista consolidada.
    """
    from PyQt5.QtCore import pyqtSignal
    request_dashboard = pyqtSignal()

    def __init__(self):
        super().__init__()
        crear_estructura()
        self.todos_los_movs = []   # lista de dicts unificada
        self.setup_ui()
        self.recargar_datos()

    # ── UI ───────────────────────────────────────────────────────────────────
    def setup_ui(self):
        self.setStyleSheet("background:#F1F5F9; font-family:'Segoe UI';")
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Header
        hdr = QFrame()
        hdr.setStyleSheet("background:#1e3a5f; color:white;")
        hdr.setFixedHeight(68)
        hhl = QHBoxLayout(hdr)
        hhl.setContentsMargins(18, 0, 18, 0)

        btn_volver = QPushButton("🔙 Volver")
        btn_volver.setStyleSheet(
            "background:rgba(255,255,255,0.18); color:white; font-weight:bold;"
            "border:1px solid rgba(255,255,255,0.35); border-radius:6px; padding:7px 14px;")
        btn_volver.clicked.connect(self.request_dashboard.emit)
        hhl.addWidget(btn_volver)
        hhl.addSpacing(18)

        ico = QLabel("🏦")
        ico.setStyleSheet("font-size:28px;")
        hhl.addWidget(ico)

        ttl = QLabel("Centro de Ventas Digitales — Panel Fiscal")
        ttl.setStyleSheet("font-size:20px; font-weight:800; letter-spacing:0.5px;")
        hhl.addWidget(ttl)
        hhl.addStretch()

        lbl_info = QLabel("Mercado Pago · Banco Provincia · Consolidado Fiscal")
        lbl_info.setStyleSheet("font-size:13px; color:rgba(255,255,255,0.7);")
        hhl.addWidget(lbl_info)

        root.addWidget(hdr)

        # Toolbar de importación
        tb = QFrame()
        tb.setStyleSheet("background:#1e3a5f; border-bottom:3px solid #00B1EA;")
        tbl = QHBoxLayout(tb)
        tbl.setContentsMargins(18, 8, 18, 8)
        tbl.setSpacing(10)

        def tbtn(txt, color, slot):
            b = QPushButton(txt)
            b.setStyleSheet(
                f"background:{color}; color:white; font-weight:bold;"
                f"padding:9px 18px; border-radius:6px; font-size:13px;")
            b.clicked.connect(slot)
            return b

        tbl.addWidget(tbtn("📥 Importar Excel/CSV Mercado Pago", "#0d9488", self.importar_mp))
        tbl.addWidget(tbtn("🏛 Importar Excel/CSV Banco Provincia", "#0369a1", self.importar_bp))
        tbl.addWidget(tbtn("🔄 Recargar Datos", "#64748b", self.recargar_datos))
        tbl.addWidget(tbtn("💾 Exportar Consolidado CSV", "#7c3aed", self.exportar_consolidado))
        tbl.addWidget(tbtn("📂 Abrir Carpeta Reportes", "#b45309", self.abrir_carpeta))
        tbl.addStretch()

        root.addWidget(tb)

        # KPI cards
        body = QVBoxLayout()
        body.setContentsMargins(18, 15, 18, 15)
        body.setSpacing(12)

        kpi_lay = QHBoxLayout()
        kpi_lay.setSpacing(14)
        def mkcard(title, val, color):
            c = QFrame()
            c.setStyleSheet(
                "QFrame{background:white;border:1px solid #e2e8f0;"
                "border-radius:12px;padding:12px;}")
            sh = QGraphicsDropShadowEffect(c)
            sh.setBlurRadius(12); sh.setOffset(0, 3)
            sh.setColor(QColor(0, 0, 0, 25)); c.setGraphicsEffect(sh)
            cl = QVBoxLayout(c); cl.setSpacing(4)
            lt = QLabel(title)
            lt.setStyleSheet("font-size:10px; font-weight:900; color:#64748B; letter-spacing:1px;")
            lv = QLabel(val)
            lv.setStyleSheet(f"font-size:22px; font-weight:900; color:{color};")
            cl.addWidget(lt); cl.addWidget(lv)
            return c, lv

        self.card_bruto, self.lbl_bruto = mkcard("📊 TOTAL BRUTO MES", "$0", "#ea580c")
        self.card_neto,  self.lbl_neto  = mkcard("💵 TOTAL NETO MES",  "$0", "#10b981")
        self.card_cargo, self.lbl_cargo = mkcard("🏦 COMISIONES MES",  "$0", "#ef4444")
        self.card_mp,    self.lbl_mp    = mkcard("💳 MP (CSV OFICIAL)", "$0", "#00B1EA")
        self.card_bp,    self.lbl_bp    = mkcard("🏛 BANCO PROVINCIA", "$0", "#0369a1")
        self.card_sis,   self.lbl_sis   = mkcard("🤖 SISTEMA (RT)",    "$0", "#8b5cf6")

        for c in [self.card_bruto, self.card_neto, self.card_cargo,
                  self.card_mp, self.card_bp, self.card_sis]:
            kpi_lay.addWidget(c)
        body.addLayout(kpi_lay)

        # Filtros
        fl = QHBoxLayout(); fl.setSpacing(10)
        self.txt_buscar = QLineEdit()
        self.txt_buscar.setPlaceholderText("🔍 Buscar por ID, descripción o fuente...")
        self.txt_buscar.setStyleSheet(
            "padding:8px 12px; border:1px solid #CBD5E1; border-radius:6px;"
            "background:white; font-size:13px;")
        self.txt_buscar.textChanged.connect(self.aplicar_filtros)

        self.dt_desde = QDateEdit()
        self.dt_desde.setCalendarPopup(True)
        self.dt_desde.setDate(QDate.currentDate().addDays(-30))
        self.dt_desde.setStyleSheet("padding:8px 12px; border:1px solid #CBD5E1; border-radius:6px; background:white; font-size:13px;")
        self.dt_desde.dateChanged.connect(self.aplicar_filtros)

        self.dt_hasta = QDateEdit()
        self.dt_hasta.setCalendarPopup(True)
        self.dt_hasta.setDate(QDate.currentDate())
        self.dt_hasta.setStyleSheet("padding:8px 12px; border:1px solid #CBD5E1; border-radius:6px; background:white; font-size:13px;")
        self.dt_hasta.dateChanged.connect(self.aplicar_filtros)

        self.cmb_fuente = QComboBox()
        self.cmb_fuente.addItems(["Todas las fuentes", "Mercado Pago (CSV oficial)",
                                  "Banco Provincia / Cuenta DNI", "Sistema (captura en tiempo real)"])
        self.cmb_fuente.setStyleSheet(
            "padding:8px 12px; border:1px solid #CBD5E1; border-radius:6px;"
            "background:white; font-size:13px; min-width:200px;")
        self.cmb_fuente.currentIndexChanged.connect(self.aplicar_filtros)

        fl.addWidget(self.txt_buscar, stretch=1)
        fl.addWidget(QLabel("Desde:")); fl.addWidget(self.dt_desde)
        fl.addWidget(QLabel("Hasta:")); fl.addWidget(self.dt_hasta)
        fl.addWidget(QLabel("Fuente:")); fl.addWidget(self.cmb_fuente)
        body.addLayout(fl)

        # Tabla
        self.tabla = QTableWidget(0, 7)
        self.tabla.setHorizontalHeaderLabels(
            ["Fecha", "ID Operación", "Fuente", "Descripción", "Monto Bruto", "Monto Neto", "Comisión"])
        self.tabla.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.tabla.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        self.tabla.setStyleSheet(
            "QTableWidget{background:white; alternate-background-color:#F8FAFC; font-size:13px;"
            "border:1px solid #e2e8f0; border-radius:8px;}"
            "QHeaderView::section{background:#1e3a5f; color:white; font-weight:bold;"
            "padding:8px 5px; border:none;}")
        self.tabla.setAlternatingRowColors(True)
        self.tabla.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tabla.setSelectionBehavior(QTableWidget.SelectRows)
        self.tabla.verticalHeader().setVisible(False)
        body.addWidget(self.tabla)

        # Barra de estado
        self.lbl_status = QLabel("ℹ️ Importá tus CSVs para comenzar el análisis fiscal.")
        self.lbl_status.setStyleSheet(
            "background:#dbeafe; color:#1e40af; padding:8px 16px;"
            "border-radius:6px; font-size:12px;")
        body.addWidget(self.lbl_status)

        root.addLayout(body)

    # ── Importación MP ────────────────────────────────────────────────────────
    def importar_mp(self):
        paths, _ = QFileDialog.getOpenFileNames(
            self, "Seleccionar Archivos de Mercado Pago", "",
            "Archivos soportados (*.csv *.xlsx *.xls);;Todos los archivos (*)")
        if not paths:
            return
        total = 0
        for src in paths:
            fname = os.path.basename(src)
            dst = os.path.join(DIR_ORIGINALES_MP,
                               f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{fname}")
            shutil.copy2(src, dst)
            total += 1
        QMessageBox.information(self, "✅ Importado",
            f"Se guardaron {total} archivo(s) de Mercado Pago.\n\n"
            f"Ubicación: {DIR_ORIGINALES_MP}\n\nRecargando datos...")
        self.recargar_datos()

    # ── Importación Banco Provincia ───────────────────────────────────────────
    def importar_bp(self):
        paths, _ = QFileDialog.getOpenFileNames(
            self, "Seleccionar Archivos de Banco Provincia / Cuenta DNI", "",
            "Archivos soportados (*.csv *.xlsx *.xls);;Todos los archivos (*)")
        if not paths:
            return
        total = 0
        for src in paths:
            fname = os.path.basename(src)
            dst = os.path.join(DIR_ORIGINALES_BP,
                               f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{fname}")
            shutil.copy2(src, dst)
            total += 1
        QMessageBox.information(self, "✅ Importado",
            f"Se guardaron {total} archivo(s) del Banco Provincia.\n\n"
            f"Ubicación: {DIR_ORIGINALES_BP}\n\nRecargando datos...")
        self.recargar_datos()

    # ── Carga y combinación de todos los datos ────────────────────────────────
    def recargar_datos(self):
        self.todos_los_movs = []
        errores = []

        # 1. CSV generado por el sistema
        try:
            sis = parsear_csv_sistema(CSV_SISTEMA_SRC)
            # Copiar al dir sistema para referencia
            if os.path.exists(CSV_SISTEMA_SRC):
                shutil.copy2(CSV_SISTEMA_SRC,
                             os.path.join(DIR_SISTEMA, "mercado_pago_sync.csv"))
            self.todos_los_movs.extend(sis)
        except Exception as e:
            errores.append(f"Sistema: {e}")

        # 2. CSVs oficiales MP
        for fn in sorted(os.listdir(DIR_ORIGINALES_MP)):
            if not fn.lower().endswith((".csv", ".xls", ".xlsx")):
                continue
            try:
                rows = parsear_csv_mercado_pago(os.path.join(DIR_ORIGINALES_MP, fn))
                self.todos_los_movs.extend(rows)
            except Exception as e:
                errores.append(f"MP {fn}: {e}")

        # 3. CSVs Banco Provincia
        for fn in sorted(os.listdir(DIR_ORIGINALES_BP)):
            if not fn.lower().endswith((".csv", ".xls", ".xlsx")):
                continue
            try:
                rows = parsear_csv_banco_provincia(os.path.join(DIR_ORIGINALES_BP, fn))
                self.todos_los_movs.extend(rows)
            except Exception as e:
                errores.append(f"BP {fn}: {e}")

        # De-duplicar por ID+fuente
        vistos = set()
        unicos = []
        for m in self.todos_los_movs:
            key = (m["id"], m["fuente"])
            if key not in vistos:
                vistos.add(key)
                unicos.append(m)
        self.todos_los_movs = sorted(unicos, key=lambda x: x["fecha"], reverse=True)

        # Actualizar filtros y UI
        self.aplicar_filtros()

        n = len(self.todos_los_movs)
        msg = f"✅ {n} movimientos cargados desde {2+len(os.listdir(DIR_ORIGINALES_MP))+len(os.listdir(DIR_ORIGINALES_BP))} fuentes."
        if errores:
            msg += f" ⚠️ {len(errores)} errores menores al parsear."
        self.lbl_status.setText(msg)

    # ── Filtros ───────────────────────────────────────────────────────────────
    def aplicar_filtros(self):
        texto   = self.txt_buscar.text().lower().strip()
        fuente_sel = self.cmb_fuente.currentText()
        
        fd = self.dt_desde.date().toString("yyyy-MM-dd")
        fh = self.dt_hasta.date().toString("yyyy-MM-dd") + " 23:59:59"

        filtrados = []
        for m in self.todos_los_movs:
            # check date
            if not (fd <= m["fecha"] <= fh):
                continue
            if fuente_sel != "Todas las fuentes" and m["fuente"] != fuente_sel:
                continue
            if texto and not any(
                texto in str(m.get(k, "")).lower()
                for k in ["fecha", "id", "fuente", "desc"]
            ):
                continue
            filtrados.append(m)

        # KPIs
        tot_bruto = sum(m["bruto"] for m in filtrados)
        tot_neto  = sum(m["neto"]  for m in filtrados)
        tot_cargo = sum(m["cargo"] for m in filtrados)
        mp_total  = sum(m["bruto"] for m in filtrados if "oficial" in m["fuente"].lower())
        bp_total  = sum(m["bruto"] for m in filtrados if "banco" in m["fuente"].lower())
        sis_total = sum(m["bruto"] for m in filtrados if "sistema" in m["fuente"].lower())

        self.lbl_bruto.setText(f"${tot_bruto:,.2f}")
        self.lbl_neto.setText(f"${tot_neto:,.2f}")
        self.lbl_cargo.setText(f"${tot_cargo:,.2f}")
        self.lbl_mp.setText(f"${mp_total:,.2f}")
        self.lbl_bp.setText(f"${bp_total:,.2f}")
        self.lbl_sis.setText(f"${sis_total:,.2f}")

        # Tabla
        COLOR_MP  = QColor("#e0f2fe")
        COLOR_BP  = QColor("#ecfdf5")
        COLOR_SIS = QColor("#faf5ff")

        self.tabla.setRowCount(0)
        for m in filtrados:
            r = self.tabla.rowCount()
            self.tabla.insertRow(r)

            # Color de fila según fuente
            if "oficial" in m["fuente"].lower():
                bg = COLOR_MP
            elif "banco" in m["fuente"].lower():
                bg = COLOR_BP
            else:
                bg = COLOR_SIS

            items = [
                m["fecha"][:16],
                m["id"],
                m["fuente"],
                m.get("desc", ""),
                f"${m['bruto']:,.2f}",
                f"${m['neto']:,.2f}",
                f"${m['cargo']:,.2f}",
            ]
            for col, val in enumerate(items):
                it = QTableWidgetItem(val)
                it.setBackground(QBrush(bg))
                if col == 4:
                    it.setForeground(QColor("#b45309"))
                    it.setFont(QFont("Segoe UI", 11, QFont.Bold))
                if col == 5:
                    it.setForeground(QColor("#059669"))
                    it.setFont(QFont("Segoe UI", 11, QFont.Bold))
                self.tabla.setItem(r, col, it)

    # ── Exportar consolidado ──────────────────────────────────────────────────
    def exportar_consolidado(self):
        fd = self.dt_desde.date().toString("yyyy-MM-dd")
        fh = self.dt_hasta.date().toString("yyyy-MM-dd")
        
        filtrados = [m for m in self.todos_los_movs if fd <= m["fecha"] <= fh + " 23:59:59"]
        if not filtrados:
            QMessageBox.warning(self, "Sin datos",
                "No hay movimientos para el período seleccionado.")
            return

        path = generar_csv_consolidado(f"{fd}_al_{fh}", filtrados)
        QMessageBox.information(self, "✅ Exportado",
            f"Archivo consolidado generado con {len(filtrados)} movimientos:\n\n{path}")

    # ── Abrir carpeta ─────────────────────────────────────────────────────────
    def abrir_carpeta(self):
        import subprocess
        abs_path = os.path.abspath(RAIZ_VENTAS)
        os.makedirs(abs_path, exist_ok=True)
        subprocess.Popen(["explorer", abs_path])
