import os
import datetime
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QGridLayout, QScrollArea, QGraphicsDropShadowEffect,
    QSizePolicy, QSpacerItem
)
from PyQt6.QtCore import Qt, pyqtSignal, QThread, QTimer, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QFont, QColor, QPainter, QLinearGradient, QBrush, QPalette

try:
    from src.base_de_datos.database import db_manager
except ImportError:
    db_manager = None

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
                voices = engine.getProperty('voices')
                for voice in voices:
                    if 'spanish' in voice.name.lower() or 'es' in voice.languages:
                        engine.setProperty('voice', voice.id)
                        break
                engine.setProperty('rate', 150)
                engine.say(self.texto)
                engine.runAndWait()
            except Exception as e:
                print(f"Error reproduciendo voz: {e}")


class CardIA(QFrame):
    """Tarjeta de análisis con diseño premium y badge de estado."""

    def __init__(self, titulo, icono, color_acento, parent=None):
        super().__init__(parent)
        self._color = color_acento
        self.setMinimumHeight(180)
        self.setStyleSheet(f"""
            QFrame#CardIA {{
                background-color: #FFFFFF;
                border-radius: 18px;
                border: 1px solid #E8EDF5;
            }}
        """)
        self.setObjectName("CardIA")

        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(28)
        shadow.setColor(QColor(0, 0, 0, 18))
        shadow.setOffset(0, 6)
        self.setGraphicsEffect(shadow)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Barra de color superior
        barra = QFrame()
        barra.setFixedHeight(5)
        barra.setStyleSheet(f"background: {color_acento}; border-radius: 18px 18px 0 0; border: none;")
        root.addWidget(barra)

        # Contenido
        inner = QVBoxLayout()
        inner.setContentsMargins(22, 18, 22, 20)
        inner.setSpacing(10)

        # Header
        head = QHBoxLayout()
        head.setSpacing(10)

        ico_wrap = QFrame()
        ico_wrap.setFixedSize(44, 44)
        ico_wrap.setStyleSheet(f"""
            QFrame {{
                background: {color_acento}18;
                border-radius: 12px;
                border: none;
            }}
        """)
        ico_lay = QHBoxLayout(ico_wrap)
        ico_lay.setContentsMargins(0, 0, 0, 0)
        lbl_ico = QLabel(icono)
        lbl_ico.setAlignment(Qt.AlignCenter)
        lbl_ico.setStyleSheet("font-size: 20px; background: transparent; border: none;")
        ico_lay.addWidget(lbl_ico)

        lbl_titulo = QLabel(titulo)
        lbl_titulo.setStyleSheet(
            "font-size: 15px; font-weight: 800; color: #0F172A; "
            "background: transparent; border: none; letter-spacing: 0.2px;"
        )

        # Badge de estado
        self.lbl_badge = QLabel("Analizando...")
        self.lbl_badge.setStyleSheet(f"""
            QLabel {{
                background: {color_acento}22;
                color: {color_acento};
                font-size: 11px;
                font-weight: 700;
                padding: 3px 10px;
                border-radius: 10px;
                border: none;
            }}
        """)
        self.lbl_badge.setAlignment(Qt.AlignCenter)

        head.addWidget(ico_wrap)
        head.addWidget(lbl_titulo)
        head.addStretch()
        head.addWidget(self.lbl_badge)
        inner.addLayout(head)

        # Separador
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setFixedHeight(1)
        sep.setStyleSheet("background: #F1F5F9; border: none;")
        inner.addWidget(sep)

        # Contenido scroll
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet("background: transparent; border: none;")

        contenido_widget = QWidget()
        contenido_widget.setStyleSheet("background: transparent;")
        contenido_lay = QVBoxLayout(contenido_widget)
        contenido_lay.setContentsMargins(0, 4, 0, 0)

        self.lbl_contenido = QLabel("Analizando datos...")
        self.lbl_contenido.setWordWrap(True)
        self.lbl_contenido.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.lbl_contenido.setStyleSheet(
            "font-size: 13px; color: #475569; background: transparent; "
            "border: none; line-height: 1.6;"
        )
        contenido_lay.addWidget(self.lbl_contenido)
        contenido_lay.addStretch()

        scroll.setWidget(contenido_widget)
        inner.addWidget(scroll)

        root.addLayout(inner)

    def set_texto(self, texto, badge_texto="OK", badge_ok=True):
        self.lbl_contenido.setText(texto)
        self.lbl_badge.setText(badge_texto)
        color = "#10B981" if badge_ok else "#EF4444"
        self.lbl_badge.setStyleSheet(f"""
            QLabel {{
                background: {color}22;
                color: {color};
                font-size: 11px;
                font-weight: 700;
                padding: 3px 10px;
                border-radius: 10px;
                border: none;
            }}
        """)

    def set_cargando(self):
        self.lbl_contenido.setText("⏳ Analizando datos en tiempo real...")
        self.lbl_badge.setText("Procesando")
        self.lbl_badge.setStyleSheet(f"""
            QLabel {{
                background: {self._color}22;
                color: {self._color};
                font-size: 11px;
                font-weight: 700;
                padding: 3px 10px;
                border-radius: 10px;
                border: none;
            }}
        """)


class JefeIAProactiva(QWidget):
    request_dashboard = pyqtSignal()

    def __init__(self, parent_main=None):
        super().__init__()
        self.parent_main = parent_main
        self.voz_thread = None
        self.resumen_texto = ""
        self._setup_ui()
        QTimer.singleShot(300, self.analizar_todo)

    def _make_btn(self, texto, bg, fg="#FFFFFF", border=None):
        btn = QPushButton(texto)
        btn.setCursor(Qt.PointingHandCursor)
        border_css = f"border: 2px solid {border};" if border else "border: none;"
        btn.setStyleSheet(f"""
            QPushButton {{
                background: {bg};
                color: {fg};
                font-weight: 700;
                font-size: 13px;
                padding: 10px 22px;
                border-radius: 10px;
                {border_css}
            }}
            QPushButton:hover {{
                opacity: 0.85;
            }}
            QPushButton:pressed {{
                padding: 11px 21px 9px 23px;
            }}
        """)
        return btn

    def _setup_ui(self):
        self.setStyleSheet("background-color: #F1F5F9;")
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ══════════════════════════════════════════════
        # HEADER PREMIUM con gradiente oscuro
        # ══════════════════════════════════════════════
        header = QFrame()
        header.setFixedHeight(88)
        header.setStyleSheet("""
            QFrame {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #0F172A,
                    stop:0.5 #1E1B4B,
                    stop:1 #0F172A
                );
                border: none;
            }
        """)
        header_lay = QHBoxLayout(header)
        header_lay.setContentsMargins(28, 0, 28, 0)
        header_lay.setSpacing(14)

        # Botón VOLVER
        btn_volver = QPushButton("← Volver")
        btn_volver.setCursor(Qt.PointingHandCursor)
        btn_volver.setFixedHeight(40)
        btn_volver.setStyleSheet("""
            QPushButton {
                background: rgba(255,255,255,0.10);
                color: #C4B5FD;
                font-weight: 700;
                font-size: 13px;
                padding: 0px 18px;
                border-radius: 10px;
                border: 1px solid rgba(196,181,253,0.30);
            }
            QPushButton:hover {
                background: rgba(255,255,255,0.18);
                color: #EDE9FE;
            }
        """)
        btn_volver.clicked.connect(self._volver)

        # Icono + Título
        lbl_ico = QLabel("🧠")
        lbl_ico.setStyleSheet("font-size: 32px; background: transparent; border: none;")

        title_block = QVBoxLayout()
        title_block.setSpacing(2)
        lbl_title = QLabel("Centro de Inteligencia Proactiva")
        lbl_title.setStyleSheet(
            "font-size: 20px; font-weight: 900; color: #FFFFFF; "
            "background: transparent; border: none; letter-spacing: 0.3px;"
        )
        lbl_sub = QLabel("Análisis automático en tiempo real de tu negocio")
        lbl_sub.setStyleSheet(
            "font-size: 12px; color: #94A3B8; background: transparent; border: none;"
        )
        title_block.addWidget(lbl_title)
        title_block.addWidget(lbl_sub)

        # Botones de acción
        self.btn_voz = QPushButton("🔊  Escuchar Resumen")
        self.btn_voz.setCursor(Qt.PointingHandCursor)
        self.btn_voz.setFixedHeight(40)
        self.btn_voz.setStyleSheet("""
            QPushButton {
                background: rgba(255,255,255,0.10);
                color: #E2E8F0;
                font-weight: 700;
                font-size: 13px;
                padding: 0px 18px;
                border-radius: 10px;
                border: 1px solid rgba(255,255,255,0.20);
            }
            QPushButton:hover { background: rgba(255,255,255,0.18); }
        """)
        self.btn_voz.clicked.connect(self._reproducir_voz)
        if not HAS_TTS:
            self.btn_voz.hide()

        btn_refresh = QPushButton("🔄  Re-Analizar")
        btn_refresh.setCursor(Qt.PointingHandCursor)
        btn_refresh.setFixedHeight(40)
        btn_refresh.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #8B5CF6,stop:1 #6D28D9);
                color: white;
                font-weight: 800;
                font-size: 13px;
                padding: 0px 20px;
                border-radius: 10px;
                border: none;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #7C3AED,stop:1 #5B21B6);
            }
        """)
        btn_refresh.clicked.connect(self.analizar_todo)

        header_lay.addWidget(btn_volver)
        header_lay.addSpacing(8)
        header_lay.addWidget(lbl_ico)
        header_lay.addLayout(title_block)
        header_lay.addStretch()
        header_lay.addWidget(self.btn_voz)
        header_lay.addWidget(btn_refresh)

        root.addWidget(header)

        # ══════════════════════════════════════════════
        # Barra de estado / timestamp
        # ══════════════════════════════════════════════
        status_bar = QFrame()
        status_bar.setFixedHeight(36)
        status_bar.setStyleSheet("background: #E2E8F0; border: none;")
        status_lay = QHBoxLayout(status_bar)
        status_lay.setContentsMargins(28, 0, 28, 0)

        self.lbl_timestamp = QLabel("Último análisis: —")
        self.lbl_timestamp.setStyleSheet(
            "font-size: 12px; color: #64748B; background: transparent; border: none;"
        )
        lbl_auto = QLabel("⚡ Actualización automática al abrir")
        lbl_auto.setStyleSheet(
            "font-size: 12px; color: #8B5CF6; font-weight: 600; background: transparent; border: none;"
        )
        status_lay.addWidget(self.lbl_timestamp)
        status_lay.addStretch()
        status_lay.addWidget(lbl_auto)
        root.addWidget(status_bar)

        # ══════════════════════════════════════════════
        # GRID DE TARJETAS
        # ══════════════════════════════════════════════
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.NoFrame)
        scroll_area.setStyleSheet("background: transparent; border: none;")

        content = QWidget()
        content.setStyleSheet("background: transparent;")
        content_lay = QVBoxLayout(content)
        content_lay.setContentsMargins(28, 24, 28, 28)
        content_lay.setSpacing(20)

        grid = QGridLayout()
        grid.setSpacing(20)

        self.card_picos   = CardIA("Predicción de Horarios Pico",  "📈", "#3B82F6")
        self.card_fugas   = CardIA("Detección de Fugas de Caja",   "🚨", "#EF4444")
        self.card_stock   = CardIA("Alertas de Stock Crítico",      "📦", "#F59E0B")
        self.card_resumen = CardIA("Resumen Ejecutivo del Jefe",    "🐺", "#8B5CF6")

        grid.addWidget(self.card_picos,   0, 0)
        grid.addWidget(self.card_fugas,   0, 1)
        grid.addWidget(self.card_stock,   1, 0)
        grid.addWidget(self.card_resumen, 1, 1)

        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)
        grid.setRowStretch(0, 1)
        grid.setRowStretch(1, 1)

        content_lay.addLayout(grid)
        content_lay.addStretch()
        scroll_area.setWidget(content)
        root.addWidget(scroll_area)

    def _volver(self):
        """Vuelve al dashboard del jefe (index 19)."""
        if self.parent_main and hasattr(self.parent_main, 'switch_tab'):
            self.parent_main.switch_tab(19)
        else:
            self.request_dashboard.emit()

    def showEvent(self, event):
        super().showEvent(event)
        QTimer.singleShot(200, self.analizar_todo)

    def analizar_todo(self):
        # Mostrar estado de carga
        for card in (self.card_picos, self.card_fugas, self.card_stock, self.card_resumen):
            card.set_cargando()

        if not db_manager:
            self.card_resumen.set_texto("❌ Error: Base de datos no conectada.", "Sin DB", False)
            return

        self._analizar_picos()
        self._analizar_fugas()
        self._analizar_stock()
        self._generar_resumen()

        ahora = datetime.datetime.now().strftime("%d/%m/%Y a las %H:%M:%S")
        self.lbl_timestamp.setText(f"Último análisis: {ahora}")

    def _analizar_picos(self):
        try:
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
                cant = res[0].get('cant', 0) if isinstance(res[0], dict) else res[0][1]
                self.card_picos.set_texto(
                    f"Analicé el histórico de la última semana.\n\n"
                    f"🔥  Pico de ventas esperado a las {hora}:00 hs ({cant} transacciones).\n\n"
                    f"💡  Asegurate de tener al menos 2 cajeros listos y el mostrador repuesto antes de esa hora.",
                    badge_texto=f"Pico: {hora}:00 hs", badge_ok=True
                )
            else:
                self.card_picos.set_texto(
                    "Todavía no hay suficientes ventas registradas en los últimos 7 días "
                    "para predecir con precisión los horarios pico.\n\n"
                    "💡  Seguí usando el sistema y el análisis mejorará automáticamente.",
                    badge_texto="Sin datos", badge_ok=False
                )
        except Exception as e:
            self.card_picos.set_texto(f"Error al analizar picos: {e}", "Error", False)

    def _analizar_fugas(self):
        try:
            query = """
                SELECT COUNT(*) as canceladas, SUM(total) as dinero_perdido
                FROM ventas
                WHERE date(fecha) = date('now') AND estado = 'CANCELADA'
            """
            res = db_manager.execute_query(query)
            if res:
                r = res[0]
                cant  = r.get('canceladas', 0)     if isinstance(r, dict) else r[0]
                dinero = float(r.get('dinero_perdido') or 0.0) if isinstance(r, dict) else float(r[1] or 0.0)

                if cant and int(cant) > 0:
                    self.card_fugas.set_texto(
                        f"🚨  Se detectaron {cant} ventas canceladas hoy.\n\n"
                        f"💸  Posible fuga de ingresos: ${dinero:,.2f}\n\n"
                        f"💡  Revisá el módulo de Reportes → Auditoría para ver qué cajero realizó estas cancelaciones.",
                        badge_texto=f"{cant} cancel.", badge_ok=False
                    )
                else:
                    self.card_fugas.set_texto(
                        "✅  Sin anomalías detectadas hoy.\n\n"
                        "No se registraron cancelaciones inusuales ni fugas de dinero. "
                        "El flujo de caja parece íntegro.",
                        badge_texto="Todo OK", badge_ok=True
                    )
            else:
                self.card_fugas.set_texto("Sin registros de ventas para analizar hoy.", "Sin datos", False)
        except Exception as e:
            self.card_fugas.set_texto(f"Error: {e}", "Error", False)

    def _analizar_stock(self):
        try:
            query = """
                SELECT nombre, stock, stock_minimo
                FROM productos
                WHERE stock <= stock_minimo AND stock_minimo > 0 AND precio > 0
                ORDER BY stock ASC LIMIT 5
            """
            res = db_manager.execute_query(query)
            if res:
                texto = "⚠️  Productos en stock crítico:\n\n"
                for r in res:
                    n  = r.get('nombre', '')      if isinstance(r, dict) else r[0]
                    s  = r.get('stock', 0)        if isinstance(r, dict) else r[1]
                    sm = r.get('stock_minimo', 0) if isinstance(r, dict) else r[2]
                    texto += f"•  {n}  →  Quedan {s} (mín: {sm})\n"
                texto += "\n💡  Ingresá a Proveedores para emitir órdenes de compra."
                self.card_stock.set_texto(texto, badge_texto=f"{len(res)} alertas", badge_ok=False)
            else:
                self.card_stock.set_texto(
                    "📦  Inventario saludable.\n\n"
                    "Ningún producto cruzó su línea de stock mínimo. "
                    "Tenés mercadería suficiente para operar con normalidad.",
                    badge_texto="Stock OK", badge_ok=True
                )
        except Exception as e:
            self.card_stock.set_texto(f"Error: {e}", "Error", False)

    def _generar_resumen(self):
        try:
            res = db_manager.execute_query(
                "SELECT SUM(total) as total, COUNT(*) as cantidad "
                "FROM ventas WHERE date(fecha) = date('now') AND estado != 'CANCELADA'"
            )
            total_hoy = 0.0
            cant_hoy  = 0
            if res:
                total_hoy = float(res[0].get('total') or 0.0) if isinstance(res[0], dict) else float(res[0][0] or 0.0)
                cant_hoy  = res[0].get('cantidad', 0)         if isinstance(res[0], dict) else res[0][1]

            res_top = db_manager.execute_query("""
                SELECT nombre_producto, SUM(cantidad) as cant
                FROM detalles_ventas dv
                JOIN ventas v ON dv.id_venta = v.id
                WHERE date(v.fecha) = date('now') AND v.estado != 'CANCELADA'
                GROUP BY nombre_producto ORDER BY cant DESC LIMIT 1
            """)
            producto_estrella = "nada aún"
            if res_top:
                producto_estrella = res_top[0].get('nombre_producto', '') if isinstance(res_top[0], dict) else res_top[0][0]

            self.resumen_texto = (
                f"🐺  El Lobo analiza tu negocio, Jefe:\n\n"
                f"Hoy cerraste {cant_hoy} ventas, embolsando ${total_hoy:,.2f} en la caja.\n"
                f"La gente se está volviendo loca por '{producto_estrella}'.\n\n"
                f"¡La calle está dura pero los números no mienten, a seguir facturando!"
            )
            badge = f"${total_hoy:,.0f}" if total_hoy > 0 else "Sin ventas"
            self.card_resumen.set_texto(self.resumen_texto, badge_texto=badge, badge_ok=total_hoy > 0)
        except Exception as e:
            self.resumen_texto = "Jefe, se me cruzaron los cables leyendo la base de datos."
            self.card_resumen.set_texto(f"Error: {e}", "Error", False)

    def _reproducir_voz(self):
        if not HAS_TTS or not self.resumen_texto:
            return
        self.voz_thread = VozWorker(self.resumen_texto)
        self.voz_thread.start()
