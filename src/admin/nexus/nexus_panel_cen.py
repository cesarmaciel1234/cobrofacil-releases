from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QFrame, QGridLayout, QScrollArea, QSizePolicy
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtCore import Qt, pyqtSignal

class NexusPanelCen(QFrame):
    request_z_close = pyqtSignal(float)
    caja_selected = pyqtSignal(int)
    
    def __init__(self):
        super().__init__()
        self.setStyleSheet("background-color: transparent; border-radius: 8px;")
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(15)

        self.selected_caja_id = 0 # 0 = Todas

        # -- SECCIÓN 1: NODOS (TOPOLOGÍA DE CAJAS) --
        # Area scrolleable para las cajas
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

        grid_nodos = QGridLayout()
        grid_nodos.setSpacing(8)
        self.nodos_ui = []
        
        btn_todas = QPushButton("🌐\nTODAS")
        btn_todas.setCursor(Qt.PointingHandCursor)
        btn_todas.setMinimumHeight(65)
        btn_todas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.nodos_ui.append(btn_todas) # index 0 es TODAS
        grid_nodos.addWidget(btn_todas, 0, 0)
        btn_todas.clicked.connect(lambda _, cid=0: self.seleccionar_caja(cid))
        
        # Generar 20 cajas
        num_cajas = 20
        for i in range(1, num_cajas + 1):
            btn = QPushButton(f"🖥️\nCAJA {i} ❌")
            btn.setCursor(Qt.PointingHandCursor)
            btn.setMinimumHeight(75)
            btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            self.nodos_ui.append(btn)
            btn.clicked.connect(lambda _, cid=i: self.seleccionar_caja(cid))
            
        # Acomodar en grid (4 columnas para hacerlos más cuadrados)
        for idx, btn in enumerate(self.nodos_ui):
            if idx == 0:
                grid_nodos.addWidget(btn, 0, 0, 1, 4) # TODAS ocupa el ancho completo arriba
            else:
                row = ((idx - 1) // 4) + 1
                col = (idx - 1) % 4
                grid_nodos.addWidget(btn, row, col)
            
        self.aplicar_estilos_botones()
        
        lay_nodos_box.addLayout(grid_nodos)
        self.scroll_nodos.setWidget(frame_nodos)
        main_layout.addWidget(self.scroll_nodos, 1) # Ocupará el 50%

        # Sistema de parpadeo de cajas activas
        import time
        self.active_boxes = {}
        self.blink_state = False
        self.timer_blink = QTimer(self)
        self.timer_blink.timeout.connect(self._update_blinking_lights)
        self.timer_blink.start(500)

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

    def seleccionar_caja(self, caja_id):
        self.selected_caja_id = caja_id
        self.aplicar_estilos_botones()
        self.caja_selected.emit(caja_id)

    def aplicar_estilos_botones(self):
        for idx, btn in enumerate(self.nodos_ui):
            if idx == self.selected_caja_id:
                # Estilo Activo / Seleccionado
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: #38BDF8;
                        color: #0F172A; 
                        border: 1px solid #38BDF8; 
                        border-radius: 4px;
                        font-family: Consolas, monospace;
                        font-weight: 900; 
                        font-size: 13px; 
                        padding: 8px;
                        letter-spacing: 2px;
                    }
                """)
            else:
                # Estilo Normal (Inactivo) - Fondo negro para resaltar PC en blanco
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: #020617;
                        color: #FFFFFF; 
                        border: 1px solid #1E293B; 
                        border-radius: 6px;
                        font-family: Consolas, monospace;
                        font-weight: bold; 
                        font-size: 13px; 
                        padding: 8px;
                        letter-spacing: 2px;
                    }
                    QPushButton:hover {
                        background-color: #0F172A;
                        border: 1px solid #38BDF8;
                    }
                """)

    def mark_active(self, caja_id):
        import time
        self.active_boxes[caja_id] = time.time()

    def _update_blinking_lights(self):
        try:
            import time
            now = time.time()
            self.blink_state = not self.blink_state
            for cid, btn in enumerate(self.nodos_ui):
                if cid == 0: continue
                
                # Si tuvo actividad en los últimos 4 segundos, parpadea en verde
                if cid in self.active_boxes and now - self.active_boxes[cid] < 4:
                    new_text = f"🖥️\nCAJA {cid} 🟢" if self.blink_state else f"🖥️\nCAJA {cid} ⚪"
                else:
                    # Si no está activa, mostrar solo cruz roja o blanco opaco (fijo sin parpadeo molestoso)
                    new_text = f"🖥️\nCAJA {cid} ❌"
                    
                    
                if btn.text() != new_text:
                    btn.setText(new_text)
        except Exception as e:
            import traceback
            with open("error_blink.log", "w") as f:
                f.write(traceback.format_exc())

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
