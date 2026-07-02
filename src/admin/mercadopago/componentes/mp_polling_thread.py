from src.utils.qt_compat import qt_exec
from src.utils.theme_manager import theme_manager
import os
import json
import subprocess
import time
from datetime import datetime
from PyQt6.QtWidgets import (

    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, 
    QTableWidget, QTableWidgetItem, QHeaderView, QFrame, QMessageBox, QDialog,
    QGraphicsDropShadowEffect, QDateEdit, QCheckBox, QFileDialog
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QColor, QFont
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

