from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QFrame, QGridLayout, QScrollArea, QSizePolicy
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
import os
import json
import time

class TarjetaTerminalFila(QFrame):
    """Componente visual para cada terminal en la matriz dinámica"""
    clicked = pyqtSignal(str)
    
    def __init__(self, nombre, ip, parent=None):
        super().__init__(parent)
        self.nombre = nombre
        self.ip = ip
        self.setCursor(Qt.PointingHandCursor)
        self.init_ui()

    def init_ui(self):
        self.setFixedSize(140, 80)
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(2)

        self.lbl_nombre = QLabel(self.nombre.upper())
        self.lbl_nombre.setStyleSheet("font-size: 11px; font-weight: bold; background: transparent; border: none;")
        
        self.lbl_ip = QLabel(self.ip)
        self.lbl_ip.setStyleSheet("color: #888888; font-size: 9px; font-family: monospace; background: transparent; border: none;")

        self.lbl_estado = QLabel("● ACTIVA")
        self.lbl_estado.setStyleSheet("color: #2ECC71; font-size: 10px; font-weight: bold; font-family: monospace; background: transparent; border: none;")

        layout.addWidget(self.lbl_nombre)
        layout.addWidget(self.lbl_ip)
        layout.addStretch()
        layout.addWidget(self.lbl_estado)
        self.setLayout(layout)

    def set_estado(self, estado, tiempo_restante=0, is_selected=False):
        if is_selected:
            self.setStyleSheet("background-color: #0EA5E9; border: 2px solid #38BDF8; border-radius: 8px;")
            self.lbl_nombre.setStyleSheet("color: #FFFFFF; font-size: 11px; font-weight: bold; background: transparent; border: none;")
            self.lbl_estado.setStyleSheet("color: #FFFFFF; font-size: 10px; font-weight: bold; background: transparent; border: none;")
            self.lbl_estado.setText("● SELECCIONADA")
        elif estado == "Activo":
            self.setStyleSheet("background-color: #F8FAFC; border: 1px solid #2ECC71; border-radius: 6px;")
            self.lbl_nombre.setStyleSheet("color: #0F172A; font-size: 11px; font-weight: bold; background: transparent; border: none;")
            self.lbl_estado.setText("● ACTIVA")
            self.lbl_estado.setStyleSheet("color: #2ECC71; font-size: 10px; font-weight: bold; background: transparent; border: none;")
        elif estado == "Warning":
            self.setStyleSheet("background-color: #FFFBEB; border: 1px solid #F1C40F; border-radius: 6px;")
            self.lbl_nombre.setStyleSheet("color: #0F172A; font-size: 11px; font-weight: bold; background: transparent; border: none;")
            self.lbl_estado.setText(f"● ESPERANDO ({tiempo_restante}s)")
            self.lbl_estado.setStyleSheet("color: #F59E0B; font-size: 10px; font-weight: bold; background: transparent; border: none;")
        else:
            self.setStyleSheet("background-color: #FEF2F2; border: 1px solid #FCA5A5; border-radius: 6px;")
            self.lbl_nombre.setStyleSheet("color: #991B1B; font-size: 11px; font-weight: bold; background: transparent; border: none;")
            self.lbl_estado.setText("● CAÍDA")
            self.lbl_estado.setStyleSheet("color: #EF4444; font-size: 10px; font-weight: bold; background: transparent; border: none;")

    def mousePressEvent(self, event):
        self.clicked.emit(self.nombre)
        super().mousePressEvent(event)

class NexusPanelCen(QFrame):
    request_z_close = pyqtSignal(float)
    caja_selected = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.MAX_PANTALLAS = 20
        self.setStyleSheet("background-color: transparent; border-radius: 8px;")
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(15)

        self.selected_caja_id = "todas" # Ahora usa el origen

        # -- SECCIÓN 1: NODOS (TOPOLOGÍA DE CAJAS) --
        
        cabecera_nodos = QHBoxLayout()
        titulo = QLabel("MATRIZ DE TRÁFICO // ORDENADO POR ACTIVIDAD")
        titulo.setStyleSheet("font-size: 12px; font-weight: bold; color: #3B82F6; letter-spacing: 1px;")
        self.lbl_info_matriz = QLabel("Monitoreando 0/20 terminales")
        self.lbl_info_matriz.setStyleSheet("color: #10B981; font-family: monospace; font-size: 10px; font-weight: bold;")
        cabecera_nodos.addWidget(titulo)
        cabecera_nodos.addStretch()
        cabecera_nodos.addWidget(self.lbl_info_matriz)
        main_layout.addLayout(cabecera_nodos)

        self.scroll_nodos = QScrollArea()
        self.scroll_nodos.setWidgetResizable(True)
        self.scroll_nodos.setStyleSheet("""
            QScrollArea { border: none; background: transparent; }
            QWidget#NodosContainer { background: transparent; }
            QScrollBar:vertical { border: none; background: #0F172A; width: 10px; }
            QScrollBar::handle:vertical { background: #334155; border-radius: 5px; }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }
        """)
        
        frame_nodos = QFrame()
        frame_nodos.setObjectName("NodosContainer")
        lay_nodos_box = QVBoxLayout(frame_nodos)
        lay_nodos_box.setContentsMargins(5, 5, 5, 5)
        lay_nodos_box.setSpacing(8)

        self.grid_nodos = QGridLayout()
        self.grid_nodos.setSpacing(8)
        
        # Diccionario en memoria de Nexus para el control de actividad
        self.active_boxes = {} # formato: {"origen": {"ip": "IP", "ultima_actividad": time.time()}}
        
        btn_todas = QPushButton("🌐 VER TODAS LAS CAJAS")
        btn_todas.setCursor(Qt.PointingHandCursor)
        btn_todas.setStyleSheet("QPushButton { background-color: #FFFFFF; color: #0F172A; font-weight: bold; border-radius: 8px; border: 1px solid #CBD5E1; padding: 10px; } QPushButton:hover { background-color: #F8FAFC; border: 1px solid #94A3B8; }")
        lay_nodos_box.addWidget(btn_todas)
        btn_todas.clicked.connect(lambda: self.seleccionar_caja("todas"))
        
        lay_nodos_box.addLayout(self.grid_nodos)
        lay_nodos_box.addStretch()
        
        self.scroll_nodos.setWidget(frame_nodos)
        main_layout.addWidget(self.scroll_nodos, 1) # Ocupará el 50%

        # Sistema de actualización de matriz dinámica
        self.timer_blink = QTimer(self)
        self.timer_blink.timeout.connect(self._actualizar_matriz_visual)
        self.timer_blink.start(2000)

        # Contenedor para la mitad inferior
        self.frame_abajo = QFrame()
        lay_abajo = QVBoxLayout(self.frame_abajo)
        lay_abajo.setContentsMargins(0, 0, 0, 0)
        lay_abajo.setSpacing(15)



        # -- SECCIÓN 2: TARJETAS SUPERIORES --
        row_top_cards = QFrame()
        col_izq_lay = QHBoxLayout(row_top_cards)
        col_izq_lay.setContentsMargins(0, 0, 0, 0)
        col_izq_lay.setSpacing(10)

        # Helper para crear mini tarjetas
        def style_mini_card(card, val_lbl, title_lbl, p_key):
            _PAL_MINI = {
                "green":  ("#1E293B", "#10B981"),
                "blue":   ("#1E293B", "#3B82F6"),
                "purple": ("#1E293B", "#8B5CF6"),
            }
            bg, accent = _PAL_MINI[p_key]
            card.setStyleSheet(f"""
                QFrame {{ background-color: {bg}; border-radius: 12px; border: 1px solid #334155; }}
            """)
            title_lbl.setStyleSheet(f"font-size: 9px; font-weight: 800; color: {accent}; background: transparent; border: none; letter-spacing: 0.5px;")
            val_lbl.setStyleSheet(f"font-size: 16px; font-weight: 900; color: #F8FAFC; background: transparent; border: none;")

        # Card 1: Ventas Efectivo
        self.lbl_efectivo = QFrame()
        lay_ve = QHBoxLayout(self.lbl_efectivo)
        lay_ve.setContentsMargins(12, 15, 12, 15)
        lbl_ve_ico = QLabel("💰")
        lbl_ve_ico.setStyleSheet("font-size: 20px; border: none; background: transparent;")
        lay_ve.addWidget(lbl_ve_ico)
        info_ve = QVBoxLayout(); info_ve.setSpacing(2)
        lbl_ve_t = QLabel("VENTAS EFECTIVO")
        self.lbl_efectivo.val_label = QLabel("$ 0.00")
        info_ve.addWidget(lbl_ve_t, 0, Qt.AlignCenter)
        info_ve.addWidget(self.lbl_efectivo.val_label, 0, Qt.AlignCenter)
        lay_ve.addLayout(info_ve)
        style_mini_card(self.lbl_efectivo, self.lbl_efectivo.val_label, lbl_ve_t, "green")

        # Card 2: Ventas Digital
        self.lbl_digital = QFrame()
        lay_vd = QHBoxLayout(self.lbl_digital)
        lay_vd.setContentsMargins(12, 15, 12, 15)
        lbl_vd_ico = QLabel("💳")
        lbl_vd_ico.setStyleSheet("font-size: 20px; border: none; background: transparent;")
        lay_vd.addWidget(lbl_vd_ico)
        info_vd = QVBoxLayout(); info_vd.setSpacing(2)
        lbl_vd_t = QLabel("VENTAS DIGITAL")
        self.lbl_digital.val_label = QLabel("$ 0.00")
        info_vd.addWidget(lbl_vd_t, 0, Qt.AlignCenter)
        info_vd.addWidget(self.lbl_digital.val_label, 0, Qt.AlignCenter)
        lay_vd.addLayout(info_vd)
        style_mini_card(self.lbl_digital, self.lbl_digital.val_label, lbl_vd_t, "blue")

        # Card 3: Fondo Apertura
        self.lbl_fondo = QFrame()
        lay_vf = QHBoxLayout(self.lbl_fondo)
        lay_vf.setContentsMargins(12, 15, 12, 15)
        lbl_vf_ico = QLabel("🏁")
        lbl_vf_ico.setStyleSheet("font-size: 20px; border: none; background: transparent;")
        lay_vf.addWidget(lbl_vf_ico)
        info_vf = QVBoxLayout(); info_vf.setSpacing(2)
        lbl_vf_t = QLabel("FONDO APERTURA")
        self.lbl_fondo.val_label = QLabel("$ 0.00")
        info_vf.addWidget(lbl_vf_t, 0, Qt.AlignCenter)
        info_vf.addWidget(self.lbl_fondo.val_label, 0, Qt.AlignCenter)
        lay_vf.addLayout(info_vf)
        style_mini_card(self.lbl_fondo, self.lbl_fondo.val_label, lbl_vf_t, "purple")

        col_izq_lay.addWidget(self.lbl_efectivo)
        col_izq_lay.addWidget(self.lbl_digital)
        col_izq_lay.addWidget(self.lbl_fondo)
        lay_abajo.addWidget(row_top_cards)

        # -- SECCIÓN 3: FILA INFERIOR --
        row_bot_cards = QFrame()
        col_der_lay = QHBoxLayout(row_bot_cards)
        col_der_lay.setContentsMargins(0, 0, 0, 0)
        col_der_lay.setSpacing(10)

        # Efectivo Esperado Card
        self.f_esp = QFrame()
        self.f_esp.setStyleSheet("background-color: #1E293B; border: 1px solid #334155; border-radius: 12px;")
        lay_esp = QVBoxLayout(self.f_esp)
        lay_esp.setContentsMargins(15, 20, 15, 20)
        lbl_esp_t = QLabel("EFECTIVO ESPERADO")
        lbl_esp_t.setAlignment(Qt.AlignCenter)
        lbl_esp_t.setStyleSheet("font-size: 9px; font-weight: 800; color: #38BDF8; border: none; background: transparent; letter-spacing: 0.5px;")
        self.lbl_live_esperado = QLabel("$ 0.00")
        self.lbl_live_esperado.setAlignment(Qt.AlignCenter)
        self.lbl_live_esperado.setStyleSheet("font-size: 20px; font-weight: 900; color: #F8FAFC; border: none; background: transparent;")
        lay_esp.addWidget(lbl_esp_t)
        lay_esp.addWidget(self.lbl_live_esperado)
        self.f_esp.setFixedWidth(160)
        col_der_lay.addWidget(self.f_esp)

        # Input Físico Contado
        self.f_input = QFrame()
        self.f_input.setStyleSheet("background-color: #1E293B; border: 1px solid #334155; border-radius: 12px;")
        lay_input = QVBoxLayout(self.f_input)
        lay_input.setContentsMargins(20, 15, 20, 15)
        lbl_inp_t = QLabel("INGRESA EL FÍSICO CONTADO ($)")
        lbl_inp_t.setAlignment(Qt.AlignCenter)
        lbl_inp_t.setStyleSheet("font-size: 10px; font-weight: 800; color: #F59E0B; border: none; background: transparent; letter-spacing: 0.5px;")
        
        self.txt_fisico = QLineEdit()
        self.txt_fisico.setAlignment(Qt.AlignCenter)
        self.txt_fisico.setStyleSheet("""
            QLineEdit {
                background: #0F172A; border: 2px solid #F59E0B; border-radius: 8px;
                color: #F8FAFC; font-size: 20px; font-weight: 900; padding: 5px;
            }
            QLineEdit:focus { border-color: #FCD34D; }
        """)
        self.txt_fisico.setText("0.00")
        
        lay_input.addWidget(lbl_inp_t)
        lay_input.addWidget(self.txt_fisico)
        col_der_lay.addWidget(self.f_input)

        main_layout.addWidget(row_bot_cards)
        
        # Boton Forzar Z
        btn_forzar = QPushButton("F12 // FORZAR CIERRE Z")
        btn_forzar.setCursor(Qt.PointingHandCursor)
        btn_forzar.setStyleSheet("""
            QPushButton {
                background: #EF4444; color: white; border: none; border-radius: 10px;
                font-weight: 800; font-size: 12px; padding: 12px;
            }
            QPushButton:hover { background: #DC2626; }
        """)
        btn_forzar.clicked.connect(self._force_z_close)
        lay_abajo.addWidget(btn_forzar)
        
        main_layout.addWidget(self.frame_abajo, 1) # Ocupará el otro 50%

    def _force_z_close(self):
        try:
            monto_fisico = float(self.txt_fisico.text().replace(',', '.'))
            self.request_z_close.emit(monto_fisico)
        except ValueError:
            self.request_z_close.emit(-1.0) # Error code

    def registrar_nodo_dinamico(self, origen, guardar=True):
        if origen == "todas": return
        if origen not in self.active_boxes:
            self.active_boxes[origen] = {"ip": "Local/Detectada", "ultima_actividad": time.time()}
            self._actualizar_matriz_visual()

    def seleccionar_caja(self, origen):
        self.selected_caja_id = origen
        self._actualizar_matriz_visual()
        self.caja_selected.emit(str(origen))

    def aplicar_estilos_botones(self):
        pass # Reemplazado por Matriz Dinamica

    def mark_active(self, origen):
        if origen == "todas": return
        if origen not in self.active_boxes:
            self.active_boxes[origen] = {"ip": "Local/Detectada", "ultima_actividad": time.time()}
        else:
            self.active_boxes[origen]["ultima_actividad"] = time.time()
            
    def _update_blinking_lights(self):
        pass

    def _actualizar_matriz_visual(self):
        # 1. Limpiar el Grid visual
        while self.grid_nodos.count():
            item = self.grid_nodos.takeAt(0)
            w = item.widget()
            if w: w.deleteLater()

        ahora = time.time()

        # 2. ORDENAR ESTRICTAMENTE: jefe, admin, cajero, carteleria
        orden_estricto = ["jefe", "admin", "cajero", "cartel"]
        def obtener_indice(nombre):
            nombre_lower = str(nombre).lower()
            for idx, role in enumerate(orden_estricto):
                if role in nombre_lower:
                    return idx
            return 999
            
        terminales_ordenadas = sorted(
            self.active_boxes.items(),
            key=lambda x: obtener_indice(x[0])
        )

        # 3. CORTE RESTRICTIVO (Regla de Máx 20)
        if len(terminales_ordenadas) > self.MAX_PANTALLAS:
            eliminadas = terminales_ordenadas[self.MAX_PANTALLAS:]
            terminales_ordenadas = terminales_ordenadas[:self.MAX_PANTALLAS]
            for nombre_eliminar, _ in eliminadas:
                if nombre_eliminar in self.active_boxes:
                    del self.active_boxes[nombre_eliminar]

        self.lbl_info_matriz.setText(f"Monitoreando {len(terminales_ordenadas)}/20 terminales vivas")

        # 4. PINTAR EN GRID (Matriz de 5 columnas)
        COLUMNAS = 5
        for posicion, (nombre, datos) in enumerate(terminales_ordenadas):
            fila = posicion // COLUMNAS
            columna = posicion % COLUMNAS
            
            tarjeta = TarjetaTerminalFila(nombre, datos["ip"])
            tarjeta.clicked.connect(self.seleccionar_caja)
            
            segundos = int(ahora - datos["ultima_actividad"])
            is_selected = (nombre == self.selected_caja_id)
            
            if segundos < 32:
                tarjeta.set_estado("Activo", is_selected=is_selected)
            elif segundos < 45:
                tarjeta.set_estado("Warning", tiempo_restante=45 - segundos, is_selected=is_selected)
            else:
                tarjeta.set_estado("Inactivo", is_selected=is_selected)

            self.grid_nodos.addWidget(tarjeta, fila, columna)

    def aplicar_tema(self, is_dark):
        if is_dark:
            # Tema oscuro
            self._tema_oscuro()
        else:
            # Tema claro
            self._tema_claro()

    def _tema_oscuro(self):
        self.setStyleSheet("background-color: transparent; border-radius: 8px;")
        self.scroll_nodos.setStyleSheet("QScrollArea { border: none; background: transparent; } QWidget#NodosContainer { background: transparent; } QScrollBar:vertical { border: none; background: #0F172A; width: 10px; } QScrollBar::handle:vertical { background: #334155; border-radius: 5px; }")
        
        # Tarjetas Top
        self.lbl_efectivo.setStyleSheet("QFrame { background-color: #1E293B; border-radius: 12px; border: 1px solid #334155; }")
        self.lbl_digital.setStyleSheet("QFrame { background-color: #1E293B; border-radius: 12px; border: 1px solid #334155; }")
        self.lbl_fondo.setStyleSheet("QFrame { background-color: #1E293B; border-radius: 12px; border: 1px solid #334155; }")
        
        self.lbl_efectivo.val_label.setStyleSheet("font-size: 16px; font-weight: 900; color: #F8FAFC; background: transparent; border: none;")
        self.lbl_digital.val_label.setStyleSheet("font-size: 16px; font-weight: 900; color: #F8FAFC; background: transparent; border: none;")
        self.lbl_fondo.val_label.setStyleSheet("font-size: 16px; font-weight: 900; color: #F8FAFC; background: transparent; border: none;")
        # Bottom Cards
        self.f_esp.setStyleSheet("background-color: #1E293B; border: 1px solid #334155; border-radius: 12px;")
        self.lbl_live_esperado.setStyleSheet("font-size: 20px; font-weight: 900; color: #F8FAFC; border: none; background: transparent;")
        
        self.f_input.setStyleSheet("background-color: #1E293B; border: 1px solid #334155; border-radius: 12px;")
        self.txt_fisico.setStyleSheet("QLineEdit { background: #0F172A; border: 2px solid #F59E0B; border-radius: 8px; color: #F8FAFC; font-size: 20px; font-weight: 900; padding: 5px; } QLineEdit:focus { border-color: #FCD34D; }")
        
        # Botones nodos
        self.aplicar_estilos_botones()

    def _tema_claro(self):
        self.setStyleSheet("background-color: transparent; border-radius: 8px;")
        self.scroll_nodos.setStyleSheet("QScrollArea { border: none; background: transparent; } QWidget#NodosContainer { background: transparent; } QScrollBar:vertical { border: none; background: #F1F5F9; width: 10px; } QScrollBar::handle:vertical { background: #CBD5E1; border-radius: 5px; }")
        
        # Tarjetas Top
        self.lbl_efectivo.setStyleSheet("QFrame { background-color: #ECFDF5; border-radius: 12px; border: none; }")
        self.lbl_digital.setStyleSheet("QFrame { background-color: #EFF6FF; border-radius: 12px; border: none; }")
        self.lbl_fondo.setStyleSheet("QFrame { background-color: #F5F3FF; border-radius: 12px; border: none; }")
        
        self.lbl_efectivo.val_label.setStyleSheet("font-size: 16px; font-weight: 900; color: #0F172A; background: transparent; border: none;")
        self.lbl_digital.val_label.setStyleSheet("font-size: 16px; font-weight: 900; color: #0F172A; background: transparent; border: none;")
        self.lbl_fondo.val_label.setStyleSheet("font-size: 16px; font-weight: 900; color: #0F172A; background: transparent; border: none;")
        # Bottom Cards
        self.f_esp.setStyleSheet("background-color: #EFF6FF; border: none; border-radius: 12px;")
        self.lbl_live_esperado.setStyleSheet("font-size: 20px; font-weight: 900; color: #1E3A8A; border: none; background: transparent;")
        
        self.f_input.setStyleSheet("background-color: #FFFBEB; border: none; border-radius: 12px;")
        self.txt_fisico.setStyleSheet("QLineEdit { background: white; border: 2px solid #F59E0B; border-radius: 8px; color: #B45309; font-size: 20px; font-weight: 900; padding: 5px; } QLineEdit:focus { border-color: #D97706; }")
        
        self.aplicar_estilos_botones()
