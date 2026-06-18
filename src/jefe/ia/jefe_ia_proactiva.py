import os
import datetime
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QGridLayout, QScrollArea, QGraphicsDropShadowEffect,
    QTextEdit, QProgressBar
)
from PyQt5.QtCore import Qt, pyqtSignal, QThread, QTimer
from PyQt5.QtGui import QFont, QColor

try:
    from src.base_de_datos.database import db_manager
except ImportError:
    db_manager = None

# Dependencia opcional para Text-to-Speech
try:
    import pyttsx3
    HAS_TTS = True
except ImportError:
    HAS_TTS = False

class VozWorker(QThread):
    def __init__(self, texto):
        super().__init__()
        self.texto = texto

    def run(self):
        if HAS_TTS:
            try:
                engine = pyttsx3.init()
                # Configurar voz en español si es posible
                voices = engine.getProperty('voices')
                for voice in voices:
                    if 'spanish' in voice.name.lower() or 'es' in voice.languages:
                        engine.setProperty('voice', voice.id)
                        break
                engine.setProperty('rate', 150) # Velocidad moderada
                engine.say(self.texto)
                engine.runAndWait()
            except Exception as e:
                print(f"Error reproduciendo voz: {e}")

class CardIA(QFrame):
    def __init__(self, titulo, icono, color_borde, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: #FFFFFF;
                border-radius: 16px;
                border-top: 5px solid {color_borde};
                border-left: 1px solid #E2E8F0;
                border-right: 1px solid #E2E8F0;
                border-bottom: 1px solid #E2E8F0;
            }}
        """)
        # Sombra
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 15))
        shadow.setOffset(0, 4)
        self.setGraphicsEffect(shadow)

        self.lay = QVBoxLayout(self)
        self.lay.setContentsMargins(20, 20, 20, 20)
        
        # Header
        head_lay = QHBoxLayout()
        lbl_ico = QLabel(icono)
        lbl_ico.setStyleSheet("font-size: 24px; background: transparent; border: none;")
        
        lbl_titulo = QLabel(titulo)
        lbl_titulo.setStyleSheet("font-size: 16px; font-weight: 900; color: #1E293B; background: transparent; border: none;")
        
        head_lay.addWidget(lbl_ico)
        head_lay.addWidget(lbl_titulo)
        head_lay.addStretch()
        self.lay.addLayout(head_lay)
        
        # Linea separadora
        linea = QFrame()
        linea.setFrameShape(QFrame.HLine)
        linea.setStyleSheet("background: #F1F5F9; border: none;")
        linea.setFixedHeight(2)
        self.lay.addWidget(linea)
        
        # Contenido
        self.lbl_contenido = QLabel("Cargando análisis...")
        self.lbl_contenido.setWordWrap(True)
        self.lbl_contenido.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.lbl_contenido.setStyleSheet("font-size: 14px; color: #475569; background: transparent; border: none; margin-top: 10px;")
        
        self.lay.addWidget(self.lbl_contenido)
        self.lay.addStretch()

    def set_texto(self, texto):
        self.lbl_contenido.setText(texto)

class JefeIAProactiva(QWidget):
    request_dashboard = pyqtSignal()

    def __init__(self, parent_main=None):
        super().__init__()
        self.parent_main = parent_main
        self.voz_thread = None
        self._setup_ui()
        self.analizar_todo()

    def _setup_ui(self):
        self.setStyleSheet("background-color: #F8FAFC;")
        main_lay = QVBoxLayout(self)
        main_lay.setContentsMargins(30, 30, 30, 30)
        main_lay.setSpacing(20)

        # --- HEADER ---
        head_lay = QHBoxLayout()
        
        lbl_title = QLabel("🧠 Centro de Inteligencia Proactiva")
        lbl_title.setStyleSheet("font-size: 28px; font-weight: 900; color: #0F172A; letter-spacing: -0.5px;")
        
        btn_refresh = QPushButton("🔄 Re-Analizar Ahora")
        btn_refresh.setCursor(Qt.PointingHandCursor)
        btn_refresh.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #8B5CF6, stop:1 #6D28D9);
                color: white; font-weight: bold; font-size: 14px; padding: 10px 20px; border-radius: 8px; border: none;
            }
            QPushButton:hover { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #7C3AED, stop:1 #5B21B6); }
        """)
        btn_refresh.clicked.connect(self.analizar_todo)
        
        self.btn_voz = QPushButton("🔊 Escuchar Resumen")
        self.btn_voz.setCursor(Qt.PointingHandCursor)
        self.btn_voz.setStyleSheet("""
            QPushButton {
                background: #FFFFFF; color: #6D28D9; border: 2px solid #8B5CF6; font-weight: bold; font-size: 14px; padding: 10px 20px; border-radius: 8px;
            }
            QPushButton:hover { background: #F5F3FF; }
        """)
        self.btn_voz.clicked.connect(self._reproducir_voz)
        if not HAS_TTS:
            self.btn_voz.hide() # Ocultar si no hay pyttsx3 instalado
            
        head_lay.addWidget(lbl_title)
        head_lay.addStretch()
        head_lay.addWidget(self.btn_voz)
        head_lay.addWidget(btn_refresh)
        
        main_lay.addLayout(head_lay)

        # --- GRID DE TARJETAS ---
        grid = QGridLayout()
        grid.setSpacing(20)
        
        self.card_picos = CardIA("Predicción de Horarios", "📈", "#3B82F6") # Azul
        self.card_fugas = CardIA("Detección de Fugas", "⚠️", "#EF4444") # Rojo
        self.card_stock = CardIA("Sugerencias de Stock", "📦", "#F59E0B") # Naranja
        self.card_resumen = CardIA("Resumen Ejecutivo", "🤖", "#8B5CF6") # Violeta
        
        grid.addWidget(self.card_picos, 0, 0)
        grid.addWidget(self.card_fugas, 0, 1)
        grid.addWidget(self.card_stock, 1, 0)
        grid.addWidget(self.card_resumen, 1, 1)
        
        # Ajustar para que las tarjetas ocupen el espacio equitativamente
        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)
        grid.setRowStretch(0, 1)
        grid.setRowStretch(1, 1)
        
        main_lay.addLayout(grid)

    def showEvent(self, event):
        super().showEvent(event)
        # Reanalizar cada vez que el jefe abre esta pestaña
        self.analizar_todo()

    def analizar_todo(self):
        if not db_manager:
            self.card_resumen.set_texto("Error: Base de datos no conectada.")
            return

        self._analizar_picos()
        self._analizar_fugas()
        self._analizar_stock()
        self._generar_resumen()

    def _analizar_picos(self):
        try:
            # Buscar la hora con más ventas en los últimos 7 días
            query = """
                SELECT strftime('%H', fecha) as hora, COUNT(*) as cant 
                FROM ventas 
                WHERE fecha >= date('now', '-7 days') AND estado != 'CANCELADA'
                GROUP BY hora 
                ORDER BY cant DESC LIMIT 1
            """
            res = db_manager.execute_query(query)
            if res:
                hora = res[0].get('hora', '00') if isinstance(res[0], dict) else res[0][0]
                self.card_picos.set_texto(
                    f"He analizado el histórico de la semana pasada.\n\n"
                    f"🔥 **Pico de Ventas:** Se espera un fuerte flujo de clientes alrededor de las **{hora}:00 hs**.\n\n"
                    f"💡 *Sugerencia:* Asegúrate de tener al menos 2 cajeros operativos y stock repuesto en mostrador antes de esta hora."
                )
            else:
                self.card_picos.set_texto("Aún no hay suficientes datos de ventas en la semana para predecir horarios pico.")
        except Exception as e:
            self.card_picos.set_texto(f"Error analizando picos: {e}")

    def _analizar_fugas(self):
        try:
            # Buscar ventas canceladas de HOY
            query = """
                SELECT COUNT(*) as canceladas, SUM(total) as dinero_perdido
                FROM ventas 
                WHERE date(fecha) = date('now') AND estado = 'CANCELADA'
            """
            res = db_manager.execute_query(query)
            if res:
                r = res[0]
                cant = r.get('canceladas', 0) if isinstance(r, dict) else r[0]
                dinero = float(r.get('dinero_perdido') or 0.0) if isinstance(r, dict) else float(r[1] or 0.0)
                
                if cant > 0:
                    self.card_fugas.set_texto(
                        f"🚨 **¡Atención!** Se han detectado **{cant} ventas canceladas** en el día de hoy.\n\n"
                        f"💸 Esto representa una posible fuga de ingresos por valor de **${dinero:,.2f}**.\n\n"
                        f"💡 *Sugerencia:* Revisa el módulo de Reportes para auditar qué cajero realizó estas cancelaciones y consultar el motivo."
                    )
                else:
                    self.card_fugas.set_texto(
                        "✅ **Todo en orden.**\n\nNo se han detectado cancelaciones inusuales ni fugas de dinero en la jornada de hoy. El flujo de caja parece íntegro."
                    )
            else:
                self.card_fugas.set_texto("No se encontraron registros de ventas para analizar fugas hoy.")
        except Exception as e:
            self.card_fugas.set_texto(f"Error analizando fugas: {e}")

    def _analizar_stock(self):
        try:
            # Productos por debajo del stock mínimo (solo si stock_minimo > 0)
            query = """
                SELECT nombre, stock, stock_minimo 
                FROM productos 
                WHERE stock <= stock_minimo AND stock_minimo > 0 AND precio > 0
                ORDER BY stock ASC LIMIT 5
            """
            res = db_manager.execute_query(query)
            if res:
                texto = "⚠️ **Stock Crítico Detectado:**\nLos siguientes productos necesitan reposición urgente:\n\n"
                for r in res:
                    n = r.get('nombre', '') if isinstance(r, dict) else r[0]
                    s = r.get('stock', 0) if isinstance(r, dict) else r[1]
                    sm = r.get('stock_minimo', 0) if isinstance(r, dict) else r[2]
                    texto += f"• **{n}**: Quedan {s} (Mínimo: {sm})\n"
                
                texto += "\n💡 *Sugerencia:* Ve al módulo de Proveedores para emitir órdenes de compra hoy mismo antes de quebrar stock."
                self.card_stock.set_texto(texto)
            else:
                self.card_stock.set_texto(
                    "📦 **Inventario Saludable.**\n\nNingún producto clave ha cruzado la línea de stock mínimo establecido. Tienes mercadería suficiente para operar con normalidad."
                )
        except Exception as e:
            self.card_stock.set_texto(f"Error analizando stock: {e}")

    def _generar_resumen(self):
        try:
            query = "SELECT SUM(total) as total, COUNT(*) as cantidad FROM ventas WHERE date(fecha) = date('now') AND estado != 'CANCELADA'"
            res = db_manager.execute_query(query)
            
            total_hoy = 0
            cant_hoy = 0
            if res:
                total_hoy = float(res[0].get('total') or 0.0) if isinstance(res[0], dict) else float(res[0][0] or 0.0)
                cant_hoy = res[0].get('cantidad', 0) if isinstance(res[0], dict) else res[0][1]

            # Buscar producto estrella de hoy
            query_top = """
                SELECT nombre_producto, SUM(cantidad) as cant 
                FROM detalles_ventas dv 
                JOIN ventas v ON dv.id_venta = v.id 
                WHERE date(v.fecha) = date('now') AND v.estado != 'CANCELADA'
                GROUP BY nombre_producto 
                ORDER BY cant DESC LIMIT 1
            """
            res_top = db_manager.execute_query(query_top)
            producto_estrella = "nada por ahora"
            if res_top:
                producto_estrella = res_top[0].get('nombre_producto', '') if isinstance(res_top[0], dict) else res_top[0][0]

            self.resumen_texto = (
                f"🐺 El Lobo analiza tu negocio, Jefe:\n\n"
                f"Hoy hemos cerrado {cant_hoy} ventas, embolsando ${total_hoy:,.2f} crocantes en la caja.\n"
                f"La gente se está volviendo loca por '{producto_estrella}'.\n\n"
                f"¡La calle está dura pero los números no mienten, a seguir facturando!"
            )
            self.card_resumen.set_texto(self.resumen_texto)
        except Exception as e:
            self.resumen_texto = "Jefe, se me cruzaron los cables leyendo la base de datos."
            self.card_resumen.set_texto(f"Error generando resumen: {e}")

    def _reproducir_voz(self):
        if not HAS_TTS:
            return
            
        if hasattr(self, 'resumen_texto'):
            self.voz_thread = VozWorker(self.resumen_texto)
            self.voz_thread.start()
