from src.utils.theme_manager import theme_manager
import os
import json
import subprocess
import time
from datetime import datetime
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, 
    QTableWidget, QTableWidgetItem, QHeaderView, QFrame, QMessageBox, QDialog,
    QGraphicsDropShadowEffect, QDateEdit, QCheckBox, QFileDialog
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QColor, QFont
from src.config import config
from src.base_de_datos.database import db_manager

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

class MPPollingThread(QThread):
    new_payment = pyqtSignal(dict)
    error_signal = pyqtSignal(str)
    
    def __init__(self, token):
        super().__init__()
        self.token = token
        self.running = True
        self.processed_ids = set()
        self.initialized = False
        
    def run(self):
        if not REQUESTS_AVAILABLE:
            self.error_signal.emit("Instalando dependencias de red automáticamente... Por favor, espera.")
            import subprocess, sys
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", "requests"])
                self.error_signal.emit("✅ Listo. Por favor, CIERRA el programa y vuélvelo a abrir para activar Mercado Pago.")
            except Exception:
                self.error_signal.emit("Error. Ejecuta en terminal: .venv/Scripts/python.exe -m pip install requests")
            self.running = False
            return
            
        while self.running:
            if not self.token:
                self.msleep(5000)
                continue
                
            mi_id = getattr(self, "mi_id", None)
            headers = {"Authorization": f"Bearer {self.token}"}
            
            if not mi_id:
                try:
                    me_resp = requests.get("https://api.mercadopago.com/users/me", headers=headers, timeout=5, verify=False)
                    if me_resp.status_code == 200:
                        self.mi_id = me_resp.json().get("id")
                        mi_id = self.mi_id
                except: pass
                
            # Buscamos los últimos 10 pagos para tener un margen seguro ante ráfagas
            url = "https://api.mercadopago.com/v1/payments/search?sort=date_created&criteria=desc&limit=10"
            try:
                response = requests.get(url, headers=headers, timeout=10, verify=False)
                if response.status_code == 200:
                    results = response.json().get("results", [])
                    if results:
                        # Si es la primera vez que corre, llenamos los procesados con lo que ya está aprobado
                        # para no notificar cobros antiguos del pasado al abrir la app.
                        if not self.initialized:
                            for p in results:
                                p_id = str(p.get("id"))
                                if p.get("status") == "approved":
                                    self.processed_ids.add(p_id)
                            self.initialized = True
                        else:
                            # Procesar en orden cronológico (los más antiguos primero)
                            for p in reversed(results):
                                p_id = str(p.get("id"))
                                status = p.get("status")
                                
                                if status == "approved":
                                    # Evitar procesar dos veces el mismo ID
                                    if p_id in self.processed_ids:
                                        continue
                                        
                                    # Verificar que seamos el cobrador (dueño del token)
                                    if mi_id and str(p.get("collector_id")) != str(mi_id):
                                        continue
                                        
                                    # Verificar si el pago es reciente (máximo 180 segundos) para no alertar de pagos antiguos
                                    is_recent = True
                                    date_approved_str = p.get("date_approved")
                                    if date_approved_str:
                                        try:
                                            from datetime import datetime, timezone
                                            import dateutil.parser
                                            dt_approved = dateutil.parser.isoparse(date_approved_str)
                                            ts_approved = dt_approved.timestamp()
                                            if abs(time.time() - ts_approved) > 180:
                                                is_recent = False
                                        except:
                                            try:
                                                clean_date = date_approved_str.split(".")[0].replace("T", " ")
                                                dt_approved = datetime.strptime(clean_date, "%Y-%m-%d %H:%M:%S")
                                                ts_approved = dt_approved.timestamp()
                                                if abs(time.time() - ts_approved) > 180:
                                                    is_recent = False
                                            except:
                                                pass
                                                
                                    # ¡Nuevo pago aprobado detectado!
                                    self.processed_ids.add(p_id)
                                    if is_recent:
                                        self.new_payment.emit(p)
                                    
                elif response.status_code == 401:
                    self.error_signal.emit("Token Inválido. Deteniendo escáner.")
                    self.running = False
            except Exception:
                pass # Evita spam de errores de red
                
            for _ in range(10): # Duerme en ciclos de 1 seg para poder detenerlo rápido
                if not self.running: break
                self.msleep(1000)
                
    def stop(self):
        self.running = False

class Admin10MP(QWidget):
    request_dashboard = pyqtSignal()
    ultimo_pago_detectado = None
    
    def __init__(self):
        super().__init__()
        self.poller = None
        self.pagos_hoy = []
        self.todos_los_pagos = []
        self.setup_ui()
        self.cargar_datos_locales()
        self.verificar_token_guardado()
        
    def setup_ui(self):
        self.setStyleSheet(" font-family: 'Segoe UI';")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # --- HEADER ---
        header = QFrame()
        header.setStyleSheet(" background-color: #1e293b; color: white;")
        header.setFixedHeight(70)
        hl = QHBoxLayout(header)
        hl.setContentsMargins(20, 0, 20, 0)
        
        btn_volver = QPushButton("🔙 Volver")
        btn_volver.setStyleSheet("background: white;  font-weight: bold; border-radius: 5px; padding: 8px 15px;")
        btn_volver.clicked.connect(self.request_dashboard.emit)
        hl.addWidget(btn_volver)
        
        hl.addSpacing(20)
        lbl_title = QLabel("Monitor de Mercado Pago (Tiempo Real)")
        lbl_title.setStyleSheet("font-size: 22px; font-weight: bold;")
        hl.addWidget(lbl_title)
        hl.addStretch()
        
        # Estado
        self.lbl_estado = QLabel("🔴 DETENIDO")
        self.lbl_estado.setStyleSheet("font-weight: bold; font-size: 16px;   padding: 5px 15px; border-radius: 10px;")
        hl.addWidget(self.lbl_estado)
        layout.addWidget(header)
        
        # --- BODY ---
        body = QVBoxLayout()
        body.setContentsMargins(20, 20, 20, 20)
        
        # Configuracion Token
        frame_token = QFrame()
        frame_token.setStyleSheet("background: white; border: 1px solid #CBD5E1; border-radius: 8px;")
        ftl = QHBoxLayout(frame_token)
        
        lbl_tok = QLabel("Access Token de Producción:")
        lbl_tok.setStyleSheet("font-weight: bold; ")
        self.txt_token = QLineEdit()
        self.txt_token.setPlaceholderText("APP_USR-...")
        self.txt_token.setStyleSheet("padding: 5px; border: 1px solid #94A3B8; border-radius: 4px; ")
        self.txt_token.setEchoMode(QLineEdit.PasswordEchoOnEdit)
        
        btn_guardar = QPushButton("Guardar e Iniciar")
        btn_guardar.setStyleSheet(" background-color: #3b82f6; color: white; font-weight: bold; padding: 8px 15px; border-radius: 4px;")
        btn_guardar.clicked.connect(self.iniciar_monitor)
        
        btn_sync = QPushButton("🔄 Sincronizar Histórico")
        btn_sync.setStyleSheet(" background-color: #3b82f6; color: white; font-weight: bold; padding: 8px 15px; border-radius: 4px;")
        btn_sync.clicked.connect(self.sincronizar_historico)
        
        btn_import_csv = QPushButton("📥 Importar CSV Oficial MP")
        btn_import_csv.setStyleSheet(" background-color: #3b82f6; color: white; font-weight: bold; padding: 8px 15px; border-radius: 4px;")
        btn_import_csv.clicked.connect(self.importar_csv_mercado_pago)
        
        btn_probar = QPushButton("Simular")
        btn_probar.setStyleSheet(" background-color: #3b82f6; color: white; font-weight: bold; padding: 8px 15px; border-radius: 4px;")
        btn_probar.clicked.connect(self.simular_pago)
        
        ftl.addWidget(lbl_tok)
        ftl.addWidget(self.txt_token, stretch=1)
        ftl.addWidget(btn_guardar)
        ftl.addWidget(btn_sync)
        ftl.addWidget(btn_import_csv)
        ftl.addWidget(btn_probar)
        body.addWidget(frame_token)
        body.addSpacing(15)
        
        # KPI Dashboard Cards
        kpi_lay = QHBoxLayout()
        kpi_lay.setSpacing(15)
        
        def create_kpi_card(title, value, color_hex):
            card = QFrame()
            card.setStyleSheet(f"""
                QFrame {{
                    background: white;
                    border: 1px solid #e2e8f0;
                    border-radius: 12px;
                    padding: 15px;
                }}
            """)
            
            # Drop shadow
            shadow = QGraphicsDropShadowEffect(card)
            shadow.setBlurRadius(15)
            shadow.setColor(QColor(148, 163, 184, 80))
            shadow.setOffset(0, 4)
            card.setGraphicsEffect(shadow)
            
            cl = QVBoxLayout(card)
            cl.setSpacing(5)
            
            lbl_title = QLabel(title)
            lbl_title.setStyleSheet("font-size: 11px; font-weight: 900;  letter-spacing: 1px;")
            
            lbl_value = QLabel(value)
            lbl_value.setStyleSheet(f"font-size: 24px; font-weight: 900; color: {color_hex}; font-family: 'Segoe UI Black';")
            
            cl.addWidget(lbl_title)
            cl.addWidget(lbl_value)
            return card, lbl_value

        self.card_total_mes, self.lbl_kpi_total_mes = create_kpi_card("📅 ACUMULADO BRUTO MES", "$0.00", "#ea580c")
        self.card_neto_mes, self.lbl_kpi_neto_mes = create_kpi_card("💵 ACUMULADO NETO MES", "$0.00", "#10b981")
        self.card_total, self.lbl_kpi_total = create_kpi_card("💰 RECAUDADO HOY", "$0.00", "#3b82f6")
        self.card_count, self.lbl_kpi_count = create_kpi_card("✅ TRANSACCIONES HOY", "0", "#0284c7")
        self.card_avg, self.lbl_kpi_avg = create_kpi_card("📈 TICKET PROMEDIO", "$0.00", "#f59e0b")
        
        kpi_lay.addWidget(self.card_total_mes)
        kpi_lay.addWidget(self.card_neto_mes)
        kpi_lay.addWidget(self.card_total)
        kpi_lay.addWidget(self.card_count)
        kpi_lay.addWidget(self.card_avg)
        
        body.addLayout(kpi_lay)
        body.addSpacing(15)
        
        # --- FILTROS DE BUSQUEDA ---
        filter_lay = QHBoxLayout()
        filter_lay.setSpacing(10)
        
        self.txt_buscar = QLineEdit()
        self.txt_buscar.setPlaceholderText("🔍 Buscar por Cliente, ID de Pago o Fecha...")
        self.txt_buscar.setStyleSheet("""
            QLineEdit {
                padding: 8px 12px;
                border: 1px solid #CBD5E1;
                border-radius: 6px;
                background: white;
                font-size: 14px;
            }
            QLineEdit:focus {
                border: 1px solid #00B1EA;
            }
        """)
        self.txt_buscar.textChanged.connect(self.aplicar_filtros)
        
        from PyQt5.QtWidgets import QComboBox
        self.cmb_fecha = QComboBox()
        self.cmb_fecha.addItems(["Todos los registros", "Solo Hoy", "Este Mes", "Día Específico..."])
        self.cmb_fecha.setStyleSheet("""
            QComboBox {
                padding: 8px 12px;
                border: 1px solid #CBD5E1;
                border-radius: 6px;
                background: white;
                font-size: 14px;
                min-width: 150px;
            }
        """)
        self.cmb_fecha.currentIndexChanged.connect(self.on_combo_fecha_changed)
        
        from PyQt5.QtCore import QDate
        self.date_picker = QDateEdit()
        self.date_picker.setCalendarPopup(True)
        self.date_picker.setDate(QDate.currentDate())
        self.date_picker.setStyleSheet("""
            QDateEdit {
                padding: 8px 12px;
                border: 1px solid #CBD5E1;
                border-radius: 6px;
                background: white;
                font-size: 14px;
                min-width: 120px;
            }
        """)
        self.date_picker.dateChanged.connect(self.aplicar_filtros)
        self.date_picker.hide()
        
        self.chk_cargas = QCheckBox("Cargas Propias")
        self.chk_cargas.setChecked(False)
        self.chk_cargas.setStyleSheet("""
            QCheckBox {
                font-size: 13px;
                
                font-weight: bold;
            }
        """)
        self.chk_cargas.stateChanged.connect(self.aplicar_filtros)
        
        self.chk_omitidos = QCheckBox("Omitidos")
        self.chk_omitidos.setChecked(False)
        self.chk_omitidos.setStyleSheet("""
            QCheckBox {
                font-size: 13px;
                
                font-weight: bold;
            }
        """)
        self.chk_omitidos.stateChanged.connect(self.aplicar_filtros)
        
        filter_lay.addWidget(self.txt_buscar, stretch=1)
        filter_lay.addWidget(self.cmb_fecha)
        filter_lay.addWidget(self.date_picker)
        filter_lay.addWidget(self.chk_cargas)
        filter_lay.addWidget(self.chk_omitidos)
        body.addLayout(filter_lay)
        body.addSpacing(10)
        
        # Tabla de Pagos
        self.tabla = QTableWidget(0, 5)
        self.tabla.setHorizontalHeaderLabels(["Fecha", "ID de Pago", "Cliente", "Monto", "Estado"])
        self.tabla.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tabla.setStyleSheet("background: white; alternate- font-size: 14px;")
        self.tabla.setAlternatingRowColors(True)
        self.tabla.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tabla.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tabla.customContextMenuRequested.connect(self.mostrar_menu_contextual)
        body.addWidget(self.tabla)
        
        layout.addLayout(body)
        
    def verificar_token_guardado(self):
        token = config.get("mp_access_token", "")
        if token:
            self.txt_token.setText(token)
            self.iniciar_monitor()
            
    def iniciar_monitor(self):
        token = self.txt_token.text().strip()
        if not token:
            QMessageBox.warning(self, "Error", "Debes ingresar un Access Token válido.")
            return
            
        config.set("mp_access_token", token)
        
        if self.poller is not None:
            self.poller.stop()
            self.poller.wait()
            
        self.poller = MPPollingThread(token)
        self.poller.new_payment.connect(self.procesar_pago)
        self.poller.error_signal.connect(self.mostrar_error)
        self.poller.start()
        
        self.lbl_estado.setText("🟢 ESCUCHANDO")
        self.lbl_estado.setStyleSheet("font-weight: bold; font-size: 16px;   padding: 5px 15px; border-radius: 10px;")
        
        # Sincronizar historial cada vez que se inicia
        self.sincronizar_historico()

    def sincronizar_historico(self):
        token = self.txt_token.text().strip()
        if not token: return
        
        try:
            import requests
            headers = {"Authorization": f"Bearer {token}"}
            
            mi_id = None
            try:
                me_resp = requests.get("https://api.mercadopago.com/users/me", headers=headers, timeout=5, verify=False)
                if me_resp.status_code == 200:
                    mi_id = me_resp.json().get("id")
            except: pass
            
            now = datetime.now()
            mes_str = now.strftime("%Y-%m")
            hoy_str = now.strftime("%Y-%m-%d")
            
            # 1. Cargar IDs ya archivados localmente para optimizar la descarga
            ids_existentes = set()
            csv_dir = "reportes"
            csv_file = os.path.join(csv_dir, "mercado_pago_sync.csv")
            if os.path.exists(csv_file):
                try:
                    import csv
                    with open(csv_file, mode="r", encoding="utf-8-sig") as f:
                        reader = csv.reader(f)
                        next(reader, None) # Saltar cabecera
                        for r in reader:
                            if r and len(r) > 1:
                                ids_existentes.add(str(r[1]).strip())
                except: pass
            
            # 2. Paginación mensual inteligente para poblar base de datos local (CSV) con el historial real del mes
            begin_date = f"{mes_str}-01T00:00:00.000-03:00"
            limit = 100
            offset = 0
            results_acumulados = []
            
            # Buscaremos hasta 100 páginas (10.000 transacciones) para cubrir el mes actual de forma completa
            for page in range(100):
                url = f"https://api.mercadopago.com/v1/payments/search?sort=date_created&criteria=desc&limit={limit}&offset={offset}&status=approved&range=date_created&begin_date={begin_date}"
                response = requests.get(url, headers=headers, timeout=12, verify=False)
                if response.status_code == 200:
                    data = response.json().get("results", [])
                    if not data:
                        break
                    results_acumulados.extend(data)
                    
                    # Optimización: si todos los IDs de esta página ya están archivados, cortamos la descarga
                    todos_duplicados = True
                    for p in data:
                        p_id = str(p.get("id", "")).strip()
                        if p_id not in ids_existentes:
                            todos_duplicados = False
                            break
                            
                    if todos_duplicados and ids_existentes:
                        break
                        
                    if len(data) < limit:
                        break
                    offset += limit
                else:
                    break
            
            # Filtrar por collector_id para asegurar que son ventas propias
            cobros_mes = []
            for p in results_acumulados:
                if p.get("transaction_amount", 0) <= 0: continue
                if mi_id and str(p.get("collector_id")) != str(mi_id): continue
                cobros_mes.append(p)
                
            # Guardar/actualizar en el CSV local (de-duplica automáticamente)
            if cobros_mes:
                self.resguardar_pagos_csv(cobros_mes)
            
        except Exception as e:
            print("Error en sincronización MP:", e)
        finally:
            # 3. Recargar la grilla y las métricas desde el CSV local (funciona con y sin internet)
            self.cargar_datos_locales()
            
    def resguardar_pagos_csv(self, pagos_list):
        """
        Guarda una lista de pagos en el archivo CSV de reportes (reportes/mercado_pago_sync.csv),
        evitando duplicaciones mediante verificación de IDs.
        """
        import csv
        from src.logger import logger
        csv_dir = "reportes"
        csv_file = os.path.join(csv_dir, "mercado_pago_sync.csv")
        
        os.makedirs(csv_dir, exist_ok=True)
        
        ids_existentes = set()
        
        # Leer IDs existentes si el archivo ya existe
        if os.path.exists(csv_file):
            try:
                with open(csv_file, mode="r", encoding="utf-8-sig") as f:
                    reader = csv.reader(f)
                    header = next(reader, None) # Omitir cabecera
                    for row in reader:
                        if row and len(row) > 1:
                            ids_existentes.add(str(row[1]).strip())
            except Exception as e:
                print("Error leyendo CSV existente:", e)
                
        nuevas_filas = []
        for p in pagos_list:
            id_pago = str(p.get("id", "")).strip()
            if not id_pago or id_pago in ids_existentes:
                continue
            if "SIMULADO" in id_pago:
                continue
                
            fecha_aprobado = p.get("date_approved", "")
            # Formatear fecha para Excel
            if fecha_aprobado:
                fecha_aprobado = fecha_aprobado.replace("T", " ").replace(".000Z", "").split("+")[0]
            else:
                fecha_aprobado = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
            try:
                monto = float(p.get("transaction_amount", 0))
            except:
                monto = 0.0
            
            payer = p.get("payer", {})
            nombre = f"{payer.get('first_name', '')} {payer.get('last_name', '')}".strip() or "Cliente"
            email = payer.get("email", "") or "sin_email@mercadopago.com"
            estado = p.get("status", "approved")
            fecha_local = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            op_type = p.get("operation_type", "regular_payment")
            
            # Obtener neto recibido y tarifa
            detalles = p.get("transaction_details", {})
            neto_val = detalles.get("net_received_amount")
            if neto_val is None:
                neto_val = monto
            else:
                try:
                    neto_val = float(neto_val)
                except:
                    neto_val = monto
            
            tarifa_val = monto - neto_val
            
            nuevas_filas.append([
                fecha_aprobado,
                id_pago,
                f"{monto:.2f}",
                nombre,
                email,
                estado.upper(),
                fecha_local,
                op_type,
                f"{neto_val:.2f}",
                f"{tarifa_val:.2f}"
            ])
            ids_existentes.add(id_pago)
            
        if nuevas_filas:
            es_nuevo = not os.path.exists(csv_file)
            try:
                with open(csv_file, mode="a", newline="", encoding="utf-8-sig") as f:
                    writer = csv.writer(f)
                    if es_nuevo:
                        writer.writerow([
                            "Fecha Aprobacion",
                            "ID de Pago",
                            "Monto",
                            "Cliente",
                            "Email Cliente",
                            "Estado",
                            "Fecha Registro Local",
                            "Tipo Operacion",
                            "Monto Neto",
                            "Tarifa"
                        ])
                    writer.writerows(nuevas_filas)
                logger.info(f"Se sincronizaron y respaldaron {len(nuevas_filas)} pagos nuevos en CSV.")
            except Exception as e:
                logger.error(f"Fallo al escribir en CSV de Mercado Pago: {e}")
                
    def cargar_datos_locales(self):
        """
        Lee el archivo CSV local completando el historial y actualiza las métricas y la tabla,
        permitiendo operar al 100% en modo offline.
        """
        self.todos_los_pagos = []
        csv_file = os.path.join("reportes", "mercado_pago_sync.csv")
        
        now = datetime.now()
        mes_str = now.strftime("%Y-%m")
        hoy_str = now.strftime("%Y-%m-%d")
        
        total_mes = 0.0
        total_neto_mes = 0.0
        total_hoy = 0.0
        cant_hoy = 0
        
        if os.path.exists(csv_file):
            try:
                import csv
                filas_limpias = []
                hubo_simulado = False
                header = None
                
                with open(csv_file, mode="r", encoding="utf-8-sig") as f:
                    reader = csv.reader(f)
                    header = next(reader, None) # Saltar cabecera
                    for row in reader:
                        if row and len(row) > 5:
                            id_pago = row[1].strip()
                            if "SIMULADO" in id_pago:
                                hubo_simulado = True
                                continue
                            filas_limpias.append(row)
                            
                            fecha_aprob = row[0].strip()
                            try:
                                monto = float(row[2])
                            except:
                                monto = 0.0
                            nombre = row[3].strip()
                            email = row[4].strip()
                            estado = row[5].strip()
                            
                            # Cargar neto si existe
                            try:
                                neto = float(row[8]) if len(row) > 8 else monto
                            except:
                                neto = monto
                            
                            # Detección inteligente de cargas propias/autotransferencias
                            if len(row) > 7:
                                op_type = row[7].strip()
                            else:
                                if email == "cesar-th123@live.com":
                                    op_type = "account_fund"
                                else:
                                    op_type = "regular_payment"
                            
                            pago_dict = {
                                "fecha": fecha_aprob,
                                "id": id_pago,
                                "monto": monto,
                                "nombre": nombre,
                                "email": email,
                                "estado": estado,
                                "op_type": op_type,
                                "neto": neto
                            }
                            self.todos_los_pagos.append(pago_dict)
                            
                            # Acumuladores (excluir autotransferencias y omitidos)
                            if estado.upper() == "APPROVED" and op_type != "account_fund":
                                if fecha_aprob.startswith(mes_str):
                                    total_mes += monto
                                    total_neto_mes += neto
                                if fecha_aprob.startswith(hoy_str):
                                    total_hoy += monto
                                    cant_hoy += 1
                                    
                # Si había registros simulados guardados, reescribimos el CSV limpio
                if hubo_simulado:
                    with open(csv_file, mode="w", newline="", encoding="utf-8-sig") as f:
                        writer = csv.writer(f)
                        if header:
                            writer.writerow(header)
                        writer.writerows(filas_limpias)
                        
            except Exception as e:
                print("Error cargando CSV local:", e)
                
        # Ordenar cronológicamente (más recientes arriba)
        self.todos_los_pagos.sort(key=lambda x: x["fecha"], reverse=True)
        
        # Actualizar KPIs
        self.lbl_kpi_total_mes.setText(f"${total_mes:,.2f}")
        self.lbl_kpi_neto_mes.setText(f"${total_neto_mes:,.2f}")
        self.lbl_kpi_total.setText(f"${total_hoy:,.2f}")
        self.lbl_kpi_count.setText(str(cant_hoy))
        prom = (total_hoy / cant_hoy) if cant_hoy > 0 else 0
        self.lbl_kpi_avg.setText(f"${prom:,.2f}")
        
        # Aplicar filtros a la grilla
        self.aplicar_filtros()

    def aplicar_filtros(self):
        """
        Aplica los filtros de texto, fecha, cargas propias y omitidos a la lista de pagos.
        """
        filtro_texto = self.txt_buscar.text().lower().strip()
        filtro_fecha = self.cmb_fecha.currentText()
        
        now = datetime.now()
        mes_str = now.strftime("%Y-%m")
        hoy_str = now.strftime("%Y-%m-%d")
        
        show_cargas = self.chk_cargas.isChecked()
        show_omitidos = self.chk_omitidos.isChecked()
        
        pagos_filtrados = []
        for p in getattr(self, "todos_los_pagos", []):
            # Filtro por Cargas Propias
            if p["op_type"] == "account_fund" and not show_cargas:
                continue
                
            # Filtro por Omitidos
            if p["estado"] == "OMITIDO" and not show_omitidos:
                continue
                
            # Filtro por Fecha
            if filtro_fecha == "Solo Hoy" and not p["fecha"].startswith(hoy_str):
                continue
            if filtro_fecha == "Este Mes" and not p["fecha"].startswith(mes_str):
                continue
            if filtro_fecha == "Día Específico...":
                fecha_sel = self.date_picker.date().toString("yyyy-MM-dd")
                if not p["fecha"].startswith(fecha_sel):
                    continue
                
            # Filtro por Texto
            if filtro_texto:
                match = (
                    filtro_texto in p["fecha"].lower() or
                    filtro_texto in p["id"].lower() or
                    filtro_texto in p["nombre"].lower() or
                    filtro_texto in p["email"].lower() or
                    filtro_texto in f"${p['monto']:.2f}"
                )
                if not match:
                    continue
                    
            pagos_filtrados.append(p)
            
        # Rellenar la tabla
        self.tabla.setRowCount(0)
        for p in pagos_filtrados:
            row = self.tabla.rowCount()
            self.tabla.insertRow(row)
            self.tabla.setItem(row, 0, QTableWidgetItem(p["fecha"]))
            self.tabla.setItem(row, 1, QTableWidgetItem(p["id"]))
            
            # Nombre de Cliente o Carga
            nombre_display = p["nombre"]
            if p["op_type"] == "account_fund":
                nombre_display = "Carga de Fondos (Autotransferencia)"
            self.tabla.setItem(row, 2, QTableWidgetItem(nombre_display))
            
            item_monto = QTableWidgetItem(f"${p['monto']:.2f}")
            item_monto.setForeground(QColor("#059669"))
            item_monto.setFont(QFont("Segoe UI", 12, QFont.Bold))
            self.tabla.setItem(row, 3, item_monto)
            
            if p["op_type"] == "account_fund":
                item_estado = QTableWidgetItem("CARGA DE FONDOS")
                item_estado.setForeground(QColor("#8B5CF6")) # Violeta
            else:
                item_estado = QTableWidgetItem(p["estado"].upper())
                if p["estado"].upper() == "APPROVED":
                    item_estado.setForeground(QColor("#059669"))
                elif p["estado"].upper() == "OMITIDO":
                    item_estado.setForeground(QColor("#94A3B8"))
            self.tabla.setItem(row, 4, item_estado)
            
    def on_combo_fecha_changed(self, index):
        if self.cmb_fecha.currentText() == "Día Específico...":
            self.date_picker.show()
        else:
            self.date_picker.hide()
        self.aplicar_filtros()

    def mostrar_menu_contextual(self, pos):
        item = self.tabla.itemAt(pos)
        if not item: return
        
        row = self.tabla.row(item)
        id_item = self.tabla.item(row, 1)
        if not id_item: return
        id_pago = id_item.text()
        
        from PyQt5.QtWidgets import QMenu, QAction
        menu = QMenu(self)
        
        pago_actual = None
        for p in self.todos_los_pagos:
            if p["id"] == id_pago:
                pago_actual = p
                break
                
        if pago_actual:
            es_omitido = (pago_actual.get("estado") == "OMITIDO")
            
            action_omitir = QAction("🚫 Omitir de Reportes / Ocultar" if not es_omitido else "🔄 Restaurar en Reportes", self)
            action_omitir.triggered.connect(lambda: self.toggle_omitir_pago(id_pago))
            menu.addAction(action_omitir)
            
            menu.exec_(self.tabla.mapToGlobal(pos))

    def toggle_omitir_pago(self, id_pago):
        csv_file = os.path.join("reportes", "mercado_pago_sync.csv")
        if not os.path.exists(csv_file): return
        
        filas_actualizadas = []
        try:
            import csv
            with open(csv_file, mode="r", encoding="utf-8-sig") as f:
                reader = csv.reader(f)
                header = next(reader, None)
                for row in reader:
                    if row and len(row) > 1:
                        if row[1].strip() == id_pago:
                            if row[5].strip() == "OMITIDO":
                                row[5] = "APPROVED"
                            else:
                                row[5] = "OMITIDO"
                        filas_actualizadas.append(row)
            
            with open(csv_file, mode="w", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f)
                if header:
                    writer.writerow(header)
                writer.writerows(filas_actualizadas)
                
            self.cargar_datos_locales()
        except Exception as e:
            print("Error al toggle omitir pago:", e)
        
    def mostrar_error(self, msg):
        self.lbl_estado.setText("🔴 ERROR DE TOKEN")
        self.lbl_estado.setStyleSheet("font-weight: bold; font-size: 16px;   padding: 5px 15px; border-radius: 10px;")
        QMessageBox.critical(self, "Mercado Pago", msg)
        
    def simular_pago(self):
        pago_simulado = {
            "id": "SIMULADO_123",
            "date_approved": datetime.now().strftime("%Y-%m-%dT%H:%M:%S.000Z"),
            "transaction_amount": 1500.50,
            "payer": {"first_name": "Juan", "last_name": "Perez"},
            "status": "approved"
        }
        self.procesar_pago(pago_simulado)
        
    def procesar_pago(self, pago):
        id_pago = str(pago.get("id", ""))
        fecha = pago.get("date_approved", "")[:10]
        monto = pago.get("transaction_amount", 0)
        
        # Extraer nombre
        payer = pago.get("payer", {})
        nombre = f"{payer.get('first_name', '')} {payer.get('last_name', '')}".strip()
        if not nombre:
            nombre = "Cliente"
            
        estado = pago.get("status", "")
        
        # Guardar en variable de clase para que la pantalla de cobro (Paso 6) pueda auto-detectar el pago
        Admin10MP.ultimo_pago_detectado = {
            "id": id_pago,
            "monto": float(monto),
            "nombre": nombre,
            "timestamp": time.time()
        }
        
        # Resguardar en CSV local (solo si no es simulado)
        if "SIMULADO" not in id_pago:
            self.resguardar_pagos_csv([pago])
            self.cargar_datos_locales()
        else:
            # Para pagos simulados, lo agregamos en memoria temporalmente
            pago_dict = {
                "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "id": id_pago,
                "monto": float(monto),
                "nombre": nombre,
                "email": payer.get("email", "") or "sin_email@mercadopago.com",
                "estado": estado,
                "op_type": "regular_payment"
            }
            self.todos_los_pagos.insert(0, pago_dict)
            self.aplicar_filtros()
            
            # Programar remoción automática tras 8 segundos
            QTimer.singleShot(8000, self.remover_pago_simulado)
            
        # Audio TTS (Liviano via PowerShell)
        mensaje = f"Llegó {monto:.0f} pesos, gracias por su compra."
        self.reproducir_audio(mensaje)
        
        # Popup Notificación
        self.mostrar_popup_verde(nombre, monto)
        
    def remover_pago_simulado(self):
        self.todos_los_pagos = [p for p in getattr(self, "todos_los_pagos", []) if "SIMULADO" not in p["id"]]
        self.aplicar_filtros()
        
    def reproducir_audio(self, texto):
        try:
            escaped_text = texto.replace('"', '""').replace("\n", " ")
            subprocess.Popen([
                "powershell", "-NoProfile", "-WindowStyle", "Hidden", "-Command",
                f'Add-Type -AssemblyName System.Speech; $s=New-Object System.Speech.Synthesis.SpeechSynthesizer; $s.Speak("{escaped_text}");'
            ])
        except Exception:
            pass
            
    def mostrar_popup_verde(self, nombre, monto):
        import sys, os
        from src.utils.paths import get_resource_path
        monto_str = f"${monto:.0f}" if monto == int(monto) else f"${monto:.2f}"
        script_path = get_resource_path(os.path.join("src", "admin", "mp_explosion.py"))
        
        try:
            if hasattr(sys, '_MEIPASS'):
                # En modo ejecutable, intentamos usar el python que suele estar en el path o ignorar si falla
                subprocess.Popen(["python", script_path, nombre, monto_str], 
                               creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
            else:
                subprocess.Popen([sys.executable, script_path, nombre, monto_str])
        except Exception:
            pass # Si no hay python instalado en el sistema destino, simplemente no muestra la animación explosiva

    def importar_csv_mercado_pago(self):
        """
        Importa CSV oficial descargado desde el panel de Mercado Pago.
        Guarda el original en reportes/ventas_digitales/originales/mercadopago/
        y recarga los datos locales.
        """
        import shutil
        from src.admin.admin14_ventas_digitales import (
            DIR_ORIGINALES_MP, parsear_csv_mercado_pago, crear_estructura
        )
        paths, _ = QFileDialog.getOpenFileNames(
            self, "Importar CSV Oficial de Mercado Pago", "",
            "Archivos CSV (*.csv);;Todos los archivos (*)"
        )
        if not paths:
            return

        crear_estructura()
        total_nuevos = 0
        errores = []

        for src in paths:
            fname = os.path.basename(src)
            dst = os.path.join(DIR_ORIGINALES_MP,
                               f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{fname}")
            shutil.copy2(src, dst)

            # Parsear e integrar en nuestro CSV del sistema (de-duplicado)
            try:
                filas = parsear_csv_mercado_pago(dst)
                pagos_api_fmt = []
                for f_row in filas:
                    pagos_api_fmt.append({
                        "id": f_row["id"],
                        "date_approved": f_row["fecha"],
                        "transaction_amount": f_row["bruto"],
                        "payer": {"first_name": "", "last_name": "", "email": ""},
                        "status": "approved",
                        "operation_type": "regular_payment",
                        "transaction_details": {
                            "net_received_amount": f_row["neto"]
                        }
                    })
                self.resguardar_pagos_csv(pagos_api_fmt)
                total_nuevos += len(pagos_api_fmt)
            except Exception as e:
                errores.append(f"{fname}: {e}")

        self.cargar_datos_locales()

        msg = f"✅ Se importaron {len(paths)} archivo(s) de Mercado Pago.\n"
        msg += f"Se integraron {total_nuevos} transacciones a tu base de datos local.\n\n"
        msg += f"📂 Original guardado en:\n{DIR_ORIGINALES_MP}"
        if errores:
            msg += f"\n\n⚠️ Errores:\n" + "\n".join(errores)
        QMessageBox.information(self, "Importación Completa", msg)
