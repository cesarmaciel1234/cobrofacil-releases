from src.utils.theme_manager import theme_manager
import sys, random, math
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QTableWidget, QTableWidgetItem, QHeaderView, QFrame,
    QPushButton, QAbstractItemView, QApplication, QGridLayout, QTextEdit, QMessageBox
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QPropertyAnimation, QRect
from PyQt5.QtGui import QColor, QFont, QPainter, QBrush, QPen
from datetime import datetime
import threading

try:
    import winsound
    AUDIO_ENABLED = True
except ImportError:
    AUDIO_ENABLED = False

try:
    import psutil
    PSUTIL_ENABLED = True
except ImportError:
    PSUTIL_ENABLED = False

try:
    from src.base_de_datos.database import db_manager
except ImportError:
    from database import db_manager

# ==============================================================================
# HOJA DE ESTILOS "NEXUS WARM-COLD 2026"
# ==============================================================================
EXTREME_STYLE = """
#NexusExtremeControl {
    background: #0F172A;
    font-family: 'Segoe UI', 'Consolas', monospace;
}

/* Paneles laterales */
#NexusExtremeControl QFrame.CyberPanel {
    background-color: rgba(15, 23, 42, 0.9);
    border: 1px solid #1E293B;
    border-radius: 8px;
    border-left: 3px solid #D97706;
}

/* Botones generales — frío (azul) */
#NexusExtremeControl QPushButton {
    background-color: rgba(2, 132, 199, 0.10);
    color: #7DD3FC;
    border: 1px solid rgba(2, 132, 199, 0.45);
    border-radius: 6px;
    padding: 10px 16px;
    font-weight: 900;
    font-size: 12px;
    letter-spacing: 1.5px;
    font-family: 'Segoe UI', sans-serif;
}
#NexusExtremeControl QPushButton:hover {
    background-color: rgba(2, 132, 199, 0.22);
    color: #E0F2FE;
    border: 1.5px solid #0284C7;
}

/* Botón crítico — cálido (rojo-ámbar) */
#NexusExtremeControl QPushButton#BtnCritical {
    background-color: rgba(239, 68, 68, 0.10);
    color: #FCA5A5;
    border: 1.5px solid rgba(239, 68, 68, 0.55);
    border-radius: 8px;
    padding: 10px 22px;
    font-size: 12px;
    font-weight: 900;
    letter-spacing: 2px;
}
#NexusExtremeControl QPushButton#BtnCritical:hover {
    background-color: rgba(239, 68, 68, 0.22);
    color: #FECACA;
    border-color: #EF4444;
}

/* Campo de texto — borde ámbar cálido */
#NexusExtremeControl QLineEdit {
    background: rgba(15, 23, 42, 0.7);
    color: #FDE68A;
    border: 1.5px solid rgba(217, 119, 6, 0.50);
    border-bottom: 3px solid #D97706;
    font-size: 26px;
    font-weight: 900;
    padding: 6px;
    border-radius: 6px;
    font-family: 'Segoe UI', sans-serif;
}
#NexusExtremeControl QLineEdit:focus {
    border-color: #F59E0B;
    background: rgba(217, 119, 6, 0.08);
}

#NexusExtremeControl QTextEdit {
    background-color: transparent;
    color: #CBD5E1;
    border: none;
    font-size: 12px;
    font-family: 'Consolas', monospace;
}

/* Tabla — oscuro con grid templado */
#NexusExtremeControl QTableWidget {
    background-color: rgba(3, 7, 18, 0.7);
    color: #E2E8F0;
    border: none;
    font-size: 11px;
    font-weight: 600;
    gridline-color: #1E293B;
    font-family: 'Segoe UI', sans-serif;
}
#NexusExtremeControl QTableWidget::item:selected {
    background: rgba(99, 102, 241, 0.20);
    color: #E0E7FF;
    font-weight: bold;
}
QHeaderView::section {
    background: rgba(30, 41, 59, 0.95);
    color: #94A3B8;
    font-weight: 900;
    font-size: 10px;
    letter-spacing: 1.5px;
    border: none;
    border-bottom: 2px solid #D97706;
    padding: 6px 8px;
    font-family: 'Segoe UI', sans-serif;
}
"""

# La clase CyberRadar ha sido movida a nexus_panel_izq.py

class NexusExtremeControl(QWidget):
    request_dashboard = pyqtSignal()
    request_z_close = pyqtSignal(float, int) # (monto_fisico, caja_id)

    def __init__(self):
        super().__init__()
        self.setObjectName("NexusExtremeControl")
        self.setFocusPolicy(Qt.StrongFocus)
        self.setStyleSheet(EXTREME_STYLE)
        
        self.last_sale_id = None
        self.total_esperado_cache = 0.0
        
        self._setup_ui()
        self._start_timers()

    def hideEvent(self, event):
        if hasattr(self, 't_matrix'): self.t_matrix.stop()
        if hasattr(self, 'panel_izq') and hasattr(self.panel_izq.spectrum, 'timer'): self.panel_izq.spectrum.timer.stop()
        super().hideEvent(event)

    def showEvent(self, event):
        if hasattr(self, 't_matrix'): self.t_matrix.start(3000) 
        if hasattr(self, 'panel_izq') and hasattr(self.panel_izq.spectrum, 'timer'): self.panel_izq.spectrum.timer.start(100)
        super().showEvent(event)

    def _play_sound(self, sound_type):
        pass # Desactivado temporalmente para prevenir RPC_E_CANTCALLOUT_ININPUTSYNCCALL en Windows

    def _start_timers(self):
        self.t_reloj = QTimer(self)
        self.t_reloj.timeout.connect(lambda: self.lbl_reloj.setText(datetime.now().strftime("%H:%M:%S // %d-%m-%Y")))
        self.t_reloj.start(1000)

        self.t_matrix = QTimer(self)
        self.t_matrix.timeout.connect(self._sync_live_data)
        self.t_matrix.start(2000)

    def keyPressEvent(self, event):
        key = event.key()
        if key in (Qt.Key_Right, Qt.Key_Down):
            self.focusNextChild()
        elif key in (Qt.Key_Left, Qt.Key_Up):
            self.focusPreviousChild()
        elif key in (Qt.Key_Enter, Qt.Key_Return):
            fw = QApplication.focusWidget()
            if isinstance(fw, QPushButton):
                fw.click()
                self._append_terminal(f"> COMANDO EJECUTADO: {fw.text()}")
        elif key == Qt.Key_F12:
            self._force_z_close()
        elif key == Qt.Key_Escape:
            self.request_dashboard.emit()
        else:
            super().keyPressEvent(event)

    def _setup_ui(self):
        self.is_dark_mode = True
        self.setStyleSheet("")
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(10)

        # --- HEADER HUD ---
        hdr = QFrame()
        hdr.setFixedHeight(45) 
        lay_h = QHBoxLayout(hdr)
        lay_h.setContentsMargins(0, 0, 0, 0)
        
        self.btn_abort = QPushButton("← SALIR DE NEXUS")
        self.btn_abort.setObjectName("BtnCritical")
        self.btn_abort.clicked.connect(self.request_dashboard.emit)

        lbl_titulo = QLabel("N E X U S  //  CONTROL CENTER")
        lbl_titulo.setStyleSheet("""
            font-size: 16px; font-weight: 900; letter-spacing: 5px;
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 #D97706, stop:0.5 #6366F1, stop:1 #0284C7);
            -webkit-background-clip: text;
            color: #E0F2FE;
            font-family: 'Segoe UI', sans-serif;
        """)

        self.lbl_reloj = QLabel("00:00:00  //  00-00-0000")
        self.lbl_reloj.setStyleSheet("""
            font-size: 12px; font-weight: 700; color: #94A3B8;
            font-family: 'Consolas', monospace;
            background: transparent; border: none;
        """)

        self.btn_theme = QPushButton("☀ MODO DÍA")
        self.btn_theme.setCursor(Qt.PointingHandCursor)
        self.btn_theme.setStyleSheet("""
            QPushButton {
                background: rgba(217,119,6,0.12);
                color: #FDE68A; border: 1px solid rgba(217,119,6,0.45);
                border-radius: 6px; padding: 5px 14px; font-weight: 800;
                font-size: 11px; font-family: 'Segoe UI', sans-serif;
            }
            QPushButton:hover {
                background: rgba(217,119,6,0.25); color: #FEF3C7;
            }
        """)
        self.btn_theme.clicked.connect(self._toggle_theme)

        lay_h.addWidget(self.btn_abort)
        lay_h.addSpacing(8)
        lay_h.addWidget(self.btn_theme)
        lay_h.addStretch()
        lay_h.addWidget(lbl_titulo)
        lay_h.addStretch()
        lay_h.addWidget(self.lbl_reloj)
        main_layout.addWidget(hdr)

        # --- GRID TÁCTICO 3 COLUMNAS ---
        grid = QGridLayout()
        grid.setSpacing(10)

        # Importar paneles modulares
        from src.admin.nexus.nexus_panel_izq import NexusPanelIzq
        from src.admin.nexus.nexus_panel_cen import NexusPanelCen
        from src.admin.nexus.nexus_panel_der import NexusPanelDer

        # 1. COLUMNA IZQ
        self.panel_izq = NexusPanelIzq()
        grid.addWidget(self.panel_izq, 0, 0, 2, 1)

        # 2. COLUMNA CENTRO
        self.panel_cen = NexusPanelCen()
        self.panel_cen.request_z_close.connect(self._force_z_close_from_panel)
        grid.addWidget(self.panel_cen, 0, 1, 2, 1)

        # 3. COLUMNA DER
        self.panel_der = NexusPanelDer()
        grid.addWidget(self.panel_der, 0, 2, 2, 1)

        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)
        grid.setColumnStretch(2, 2)
        grid.setRowStretch(0, 1)
        grid.setRowStretch(1, 1)

        main_layout.addLayout(grid)
        
        self.current_caja_filter = 0
        self.panel_cen.caja_selected.connect(self._on_caja_selected)

    def _toggle_theme(self):
        self.is_dark_mode = not self.is_dark_mode
        if self.is_dark_mode:
            self.setStyleSheet(EXTREME_STYLE)
            self.btn_theme.setText("☀️ MODO DÍA")
            self.btn_theme.setStyleSheet("QPushButton {  background-color: #3b82f6; color: white; border: none; border-radius: 4px; padding: 5px 10px; font-weight: bold; } QPushButton:hover {  }")
        else:
            self.setStyleSheet("")
            self.btn_theme.setText("🌙 MODO NOCHE")
            self.btn_theme.setStyleSheet("QPushButton {   border: none; border-radius: 4px; padding: 5px 10px; font-weight: bold; } QPushButton:hover {  }")
            
        if hasattr(self.panel_cen, "aplicar_tema"): self.panel_cen.aplicar_tema(self.is_dark_mode)
        if hasattr(self.panel_der, "aplicar_tema"): self.panel_der.aplicar_tema(self.is_dark_mode)
        # Panel izquierdo se queda oscuro siempre por estética, o podemos forzarlo
        if hasattr(self.panel_izq, "aplicar_tema"): self.panel_izq.aplicar_tema(self.is_dark_mode)

    def _on_caja_selected(self, caja_id):
        self.current_caja_filter = caja_id
        if caja_id > 0:
            self._append_terminal(f"> [SYSTEM] FILTRO ACTIVADO: CAJA {caja_id}", "#6366F1")
        else:
            self._append_terminal("> [SYSTEM] FILTRO GLOBAL (TODAS LAS CAJAS)", "#10B981")
            
        # Refrescar los totales en el panel izquierdo (con cache bypassing para refresco inmediato)
        self._sync_live_data()
        
        # Filtrar también la tabla de auditoría del panel derecho
        self.panel_der.set_caja_filter(caja_id)

    def _append_terminal(self, texto, color_override=None):
        if color_override:
            color = color_override
        else:
            if "[FATAL]" in texto or "[CRITICAL]" in texto:
                color = "#E11D48" # Rose oscuro
            elif "[WARN]" in texto:
                color = "#D97706" # Amber oscuro
            elif "[OK]" in texto:
                color = "#059669" # Emerald oscuro
            elif "[TX]" in texto:
                color = "#38BDF8" # Azul neon
            else:
                color = "#94A3B8" # Slate claro
        
        self.panel_izq.append_terminal(texto, color)

    def _trigger_glitch(self):
        self._play_sound("critical")
        self.glitch_count = 0
        self.original_style = self.styleSheet()
        self.t_glitch = QTimer(self)
        self.t_glitch.timeout.connect(self._do_glitch_flash)
        self.t_glitch.start(100)

    def _do_glitch_flash(self):
        if self.glitch_count > 15:
            self.t_glitch.stop()
            self.setStyleSheet(self.original_style)
            return
            
        if self.glitch_count % 2 == 0:
            self.setStyleSheet(self.original_style + "\nQWidget {   font-weight: bold; }")
        else:
            self.setStyleSheet(self.original_style)
            
        self.glitch_count += 1

    def _force_z_close(self):
        try:
            monto_fisico = float(self.panel_cen.txt_fisico.text().replace(',', '.'))
        except ValueError:
            self._play_sound("alert")
            QMessageBox.critical(self, "ERROR CRÍTICO", "INPUT FÍSICO CORRUPTO.")
            return
            monto_fisico = 0.0

        self._ejecutar_cierre_z_db(monto_fisico)

    def _force_z_close_from_panel(self, monto_fisico):
        if monto_fisico < 0:
            self._play_sound("alert")
            QMessageBox.critical(self, "ERROR CRÍTICO", "INPUT FÍSICO CORRUPTO.")
            return
        self._ejecutar_cierre_z_db(monto_fisico)

    def _ejecutar_cierre_z_db(self, monto_fisico):
        # ── Guard: el Cierre Z solo puede ejecutarlo el MAESTRO ────────────────────
        if not getattr(db_manager, 'is_master', True):
            self._append_terminal(
                "> [BLOCKED] CIERRE Z DENEGADO: esta terminal corre en modo ESCLAVO."
                " Solo el servidor maestro puede ejecutar cierres fiscales.", "#F43F5E")
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.warning(
                self, "Operación No Permitida",
                "El Cierre Z solo puede ejecutarse desde la PC MAESTRA.\n"
                "Esta terminal está conectada como ESCLAVA a la red."
            )
            return

        if self.current_caja_filter <= 0:
            self._append_terminal("> [ERROR] NO SE PUEDE FORZAR CIERRE GLOBAL. SELECCIONA UNA CAJA ESPECÍFICA PRIMERO.", "#E11D48")
            self._play_sound("error")
            return

        # Calcular si hay descuadre en la caja seleccionada
        try:
            from src.base_de_datos.database import db_manager
            from datetime import datetime
            hoy = datetime.now().strftime("%Y-%m-%d")
            total_efectivo = db_manager.execute_scalar(
                "SELECT SUM(total) FROM ventas WHERE fecha LIKE ? AND metodo_pago = 'Efectivo' AND caja_id = ?",
                (f"{hoy}%", self.current_caja_filter)
            ) or 0.0
            
            # Ajustar por el fondo inicial
            fondo_inicial = float(db_manager.execute_scalar(
                "SELECT monto FROM movimientos_caja WHERE tipo='APERTURA' AND caja_id = ? ORDER BY id DESC LIMIT 1",
                (self.current_caja_filter,)
            ) or 0.0)
            
            esperado = total_efectivo + fondo_inicial
            diferencia = monto_fisico - esperado
            
            if diferencia < 0:
                self._append_terminal(f"> [FATAL] DESCUADRE CRÍTICO EN CAJA {self.current_caja_filter} DE ${diferencia:.2f}. INICIANDO PROTOCOLOS DE AUDITORÍA.")
            elif diferencia > 1000.0:
                self._play_sound("alert")
                self._append_terminal(f"> [WARN] EXCESO NO JUSTIFICADO EN CAJA {self.current_caja_filter} DE ${diferencia:.2f}.")
        except Exception as e:
            print(f"Error calculando cuadre en F12: {e}")

        try:
            hoy = datetime.now().strftime("%Y-%m-%d")
            total_efectivo = db_manager.execute_scalar(
                "SELECT SUM(total) FROM ventas WHERE fecha LIKE ? AND metodo_pago = 'Efectivo' AND caja_id = ?",
                (f"{hoy}%", self.current_caja_filter)
            ) or 0.0

            fondo_inicial = float(db_manager.execute_scalar(
                "SELECT monto FROM movimientos_caja WHERE tipo='APERTURA' AND caja_id = ? ORDER BY id DESC LIMIT 1",
                (self.current_caja_filter,)
            ) or 0.0)

            esperado  = total_efectivo + fondo_inicial
            diferencia = monto_fisico - esperado

            if diferencia < 0:
                self._append_terminal(
                    f"> [FATAL] DESCUADRE CRÍTICO EN CAJA {self.current_caja_filter}"
                    f" DE ${diferencia:.2f}. INICIANDO PROTOCOLOS DE AUDITORÍA.")
            elif diferencia > 1000.0:
                self._play_sound("alert")
                self._append_terminal(
                    f"> [WARN] EXCESO NO JUSTIFICADO EN CAJA {self.current_caja_filter}"
                    f" DE ${diferencia:.2f}.")
        except Exception as e:
            print(f"Error calculando cuadre en F12: {e}")
            esperado   = 0.0
            diferencia = monto_fisico

        self._append_terminal(
            f"> [CRITICAL] SECUENCIA F12 INICIADA. EJECUTANDO CIERRE Z "
            f"CAJA {self.current_caja_filter} (FÍSICO: {monto_fisico})")

        # Confirmar y ejecutar
        try:
            from PyQt5.QtWidgets import QMessageBox
            reply = QMessageBox.question(
                self,
                "Confirmación Crítica — NEXUS OVERRIDE",
                f"¿Estás seguro de emitir el CIERRE Z DEFINITIVO para la CAJA {self.current_caja_filter}?\n"
                f"Monto Físico Declarado: ${monto_fisico:,.2f}",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if reply == QMessageBox.No:
                self._append_terminal("> [ABORT] SECUENCIA DE CIERRE Z ABORTADA POR EL USUARIO.")
                return

            db_manager.execute_non_query(
                "INSERT INTO movimientos_caja (tipo, monto, usuario, observaciones, caja_id)"
                " VALUES (?, ?, ?, ?, ?)",
                ("CIERRE_Z", diferencia, "nexus_admin",
                 f"Modo:global | Fis:${monto_fisico:.2f} | Esp:${esperado:.2f}",
                 self.current_caja_filter)
            )
            db_manager.execute_non_query(
                "UPDATE ventas SET estado='CERRADA' WHERE estado='COMPLETADA' AND caja_id=?",
                (self.current_caja_filter,)
            )

            # Imprimir ticket Z
            try:
                from src.hardware.printer import printer_manager
                printer_manager.imprimir_control_x({
                    "fondo": fondo_inicial, "t_efec": total_efectivo, "t_tarj": 0,
                    "t_total": total_efectivo, "esperado": esperado, "alertas": 0,
                    "dia_tarjeta": 0, "dia_total": total_efectivo,
                    "efectivo_esperado": esperado, "segunda_tiketera": False
                })
            except Exception as e_print:
                self._append_terminal(f"> [WARN] Error de impresión: {e_print}", "#F59E0B")

            QMessageBox.information(
                self, "Cierre Exitoso",
                f"Cierre Z completado para Caja {self.current_caja_filter}.")
            self._append_terminal("> [OK] CIERRE Z EJECUTADO Y SESIÓN FINALIZADA.", "#10B981")

        except Exception as e:
            self._append_terminal(f"> [FATAL] ERROR EN DB DURANTE CIERRE Z: {e}", "#E11D48")

    # ==============================================================================
    # MOTOR DE DATOS REALES (CONEXIÓN A DATABASE)
    # ==============================================================================

    def _sync_live_data(self):
        try:
            hoy = datetime.now().strftime("%Y-%m-%d")

            # 1. Actualizar métricas (Globales o por Caja)
            # DATE(fecha) = ? funciona en SQLite y MariaDB (columna DATETIME)
            params_totales = [hoy]
            filtro_caja_sql = ""
            if self.current_caja_filter > 0:
                filtro_caja_sql = " AND caja_id = ?"
                params_totales.append(self.current_caja_filter)

            total_efectivo = db_manager.execute_scalar(
                f"SELECT SUM(total) FROM ventas"
                f" WHERE DATE(fecha) = ? AND metodo_pago = 'Efectivo'{filtro_caja_sql}",
                tuple(params_totales)
            ) or 0.0
            total_digital = db_manager.execute_scalar(
                f"SELECT SUM(total) FROM ventas"
                f" WHERE DATE(fecha) = ? AND metodo_pago != 'Efectivo'{filtro_caja_sql}",
                tuple(params_totales)
            ) or 0.0

            self.total_esperado_cache = total_efectivo

            str_efectivo = f"$ {int(total_efectivo):,}"
            str_digital  = f"$ {int(total_digital):,}"

            if self.panel_cen.lbl_efectivo.val_label.text() != str_efectivo:
                self.panel_cen.lbl_efectivo.val_label.setText(str_efectivo)
            if self.panel_cen.lbl_digital.val_label.text() != str_digital:
                self.panel_cen.lbl_digital.val_label.setText(str_digital)

            # 2. Buscar ventas nuevas desde la última consulta
            query_nuevas = (
                "SELECT id, caja_id, metodo_pago, total, usuario"
                " FROM ventas WHERE DATE(fecha) = ?"
            )
            params_nuevas = [hoy]
            if self.last_sale_id:
                query_nuevas += " AND id > ?"
                params_nuevas.append(self.last_sale_id)
            query_nuevas += " ORDER BY id ASC LIMIT 5"

            nuevas_ventas = db_manager.execute_query(query_nuevas, tuple(params_nuevas))
            
            if nuevas_ventas:
                for v in nuevas_ventas:
                    self.last_sale_id = v['id']
                    tot_str = f"{int(v['total']):,}"
                    self._registrar_evento_caja(v['caja_id'], "VENTA", f"{v['metodo_pago']} - ${tot_str}")
            else:
                if random.random() > 0.8:
                    self._inyectar_ruido_red()
        except Exception as e:
            import traceback
            with open("error_sync.log", "w") as f:
                f.write(traceback.format_exc())
            print(f"Error _sync_live_data: {e}")

    def _registrar_evento_caja(self, caja_id, cat, msg):
        self._play_sound("sale")
        self.panel_izq.spectrum.add_blip() # Añadir detección al radar
        
        fg_color = "#10B981" if cat == "VENTA" else "#F43F5E"
        bg_color = "#065F46" if cat == "VENTA" else "#991B1B"
        
        # En la UI: indice 0 es TODAS, indice 1 es CAJA 1, etc.
        caja_index = caja_id if caja_id and caja_id < len(self.panel_cen.nodos_ui) else 0
        src = f"CAJA {caja_id}"
        
        # Brillo del botón
        boton = self.panel_cen.nodos_ui[caja_index]
        self.panel_cen.mark_active(caja_index)
        if not hasattr(boton, "estilo_original"):
            boton.estilo_original = boton.styleSheet()
        estilo_brillo = f"background-color: {bg_color}; color: white; border: 2px solid {fg_color};"
        boton.setStyleSheet(estilo_brillo)
        QTimer.singleShot(500, lambda b=boton, c=caja_index: self._restaurar_estilo_boton(b, c))
        # Terminal y Bitácora
        if cat == "VENTA":
            self._append_terminal(f"{src}: {msg}", "#10B981") # Verde esmeralda para ventas
        else:
            self._append_terminal(f"> [TX] {src}: {msg}")
            self._agregar_log_tabla(src, f"[{cat}] {msg}", fg_color)

    def _restaurar_estilo_boton(self, boton, caja_index):
        if hasattr(self.panel_cen, 'selected_caja_id') and self.panel_cen.selected_caja_id == caja_index:
            # Si justo está seleccionado, forzamos aplicar el estilo seleccionado
            self.panel_cen.aplicar_estilos_botones()
        else:
            if hasattr(boton, "estilo_original"):
                boton.setStyleSheet(boton.estilo_original)

    def _inyectar_ruido_red(self):
        eventos = [
            ("SYNC", "Push a DB SQLite Exitoso", "#8B5CF6", "#5B21B6"),
            ("ACCESS", "Apertura Cajón (Shift)", "#94A3B8", "#475569")
        ]
        cat, msg, fg_color, bg_color = random.choice(eventos)
        caja_idx = random.randint(0, 3)
        self._agregar_log_tabla(f"CAJA {caja_idx+1}", f"[{cat}] {msg}", fg_color)

    def _agregar_log_tabla(self, src, payload, fg_color):
        self.panel_der.agregar_log(src, payload, fg_color)
