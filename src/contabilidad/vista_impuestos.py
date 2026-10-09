from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from src.contabilidad.shared_globals import *

class VistaImpuestosMixin:
    def _build_tab_impuestos(self):
        lay, _ = self._page()
        
        lay.addWidget(section_title("💵  Gestión de Impuestos - Aprendizaje Contable"))
        
        # Info educativa
        info_box = QFrame()
        info_box.setStyleSheet(f"""
            QFrame {{
                background: {PAL['surface']};
                border: 1px solid {PAL['border']};
                border-radius: 8px;
                padding: 12px;
            }}
        """)
        info_lay = QVBoxLayout(info_box)
        
        info_text = QLabel(
            "📚 Conceptos Contables:\n"
            "• Débito Fiscal: IVA que cobras en tus ventas (a favor tuyo)\n"
            "• Crédito Fiscal: IVA que pagas en tus compras (descuento)\n"
            "• Saldo a Pagar: Débito > Crédito (debes pagar AFIP)\n"
            "• Saldo a Creditar: Crédito > Débito (AFIP te devuelve)\n\n"
            "💡 Los productos en Almacén con IVA 21% generan automáticamente el asiento contable con desglose."
        )
        info_text.setStyleSheet(f"font-size: 12px; color: {PAL['text']}; background: transparent;")
        info_lay.addWidget(info_text)
        lay.addWidget(info_box)
        
        lay.addSpacing(15)
        
        # Selector de período
        periodo_lay = QHBoxLayout()
        lbl_periodo = QLabel("Período:")
        lbl_periodo.setStyleSheet(f"font-size: 13px; font-weight: bold; color: {PAL['text']}; background: transparent;")
        
        self.date_desde = QDateEdit()
        self.date_desde.setDate(QDate.currentDate().addMonths(-1))
        self.date_desde.setCalendarPopup(True)
        self.date_desde.setDisplayFormat("MM/yyyy")
        
        self.date_hasta = QDateEdit()
        self.date_hasta.setDate(QDate.currentDate())
        self.date_hasta.setCalendarPopup(True)
        self.date_hasta.setDisplayFormat("MM/yyyy")
        
        btn_liquidar = btn_primary("📊 Liquidar IVA del Período")
        btn_liquidar.clicked.connect(self._liquidar_iva)
        
        periodo_lay.addWidget(lbl_periodo)
        periodo_lay.addWidget(self.date_desde)
        periodo_lay.addWidget(QLabel("a"))
        periodo_lay.addWidget(self.date_hasta)
        periodo_lay.addWidget(btn_liquidar)
        periodo_lay.addStretch()
        lay.addLayout(periodo_lay)
        
        lay.addSpacing(15)
        
        # Tarjetas de resumen
        tarjetas_lay = QHBoxLayout()
        
        self.card_debito = self._crear_tarjeta_resumen("Débito Fiscal", "IVA cobrado en ventas", PAL['danger'])
        self.card_credito = self._crear_tarjeta_resumen("Crédito Fiscal", "IVA pagado en compras", PAL['success'])
        self.card_saldo = self._crear_tarjeta_resumen("Saldo IVA", "Resultado del período", PAL['primary'])
        
        tarjetas_lay.addWidget(self.card_debito)
        tarjetas_lay.addWidget(self.card_credito)
        tarjetas_lay.addWidget(self.card_saldo)
        lay.addLayout(tarjetas_lay)
        
        lay.addSpacing(15)
        
        # Tabla de comprobantes con desglose
        self._tbl_comprobantes = build_table(["Fecha", "Tipo", "Número", "Monto Gravado", "IVA", "Monto Total", "Estado"])
        lay.addWidget(self._tbl_comprobantes)
        lay.addStretch()
    
    def _crear_tarjeta_resumen(self, titulo, subtitulo, color):
        """Crea una tarjeta de resumen para IVA"""
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background: {PAL['surface']};
                border: 1px solid {PAL['border']};
                border-top: 4px solid {color};
                border-radius: 12px;
            }}
        """)
        lay = QVBoxLayout(card)
        lay.setContentsMargins(16, 12, 16, 12)
        lay.setSpacing(4)
        
        lbl_t = QLabel(titulo)
        lbl_t.setStyleSheet(f"font-size: 11px; font-weight: 800; color: {PAL['text3']}; letter-spacing: 0.5px; background: transparent;")
        lay.addWidget(lbl_t)
        
        self.lbl_valor = QLabel("$ 0.00")
        self.lbl_valor.setStyleSheet(f"font-size: 24px; font-weight: 900; color: {color}; background: transparent;")
        lay.addWidget(self.lbl_valor)
        
        lbl_s = QLabel(subtitulo)
        lbl_s.setStyleSheet(f"font-size: 11px; color: {PAL['text2']}; background: transparent;")
        lay.addWidget(lbl_s)
        
        return card
    
    def _load_impuestos(self):
        if not self._db:
            return
        
        try:
            # Cargar comprobantes recientes
            from datetime import date, timedelta
            desde = date.today() - timedelta(days=30)
            
            if self._db.is_enterprise_mode():
                # Usar motor de impuestos si está disponible
                try:
                    from src.contabilidad.motor_impuestos import MotorImpuestos
                    motor = MotorImpuestos(self._db.db_name)
                    comprobantes = motor.obtener_comprobantes('venta', desde, date.today())
                    
                    self._tbl_comprobantes.setRowCount(0)
                    for comp in comprobantes:
                        r = self._tbl_comprobantes.rowCount()
                        self._tbl_comprobantes.insertRow(r)
                        
                        vals = [
                            comp.get('fecha', ''),
                            comp.get('tipo', ''),
                            comp.get('numero', ''),
                            f"${comp.get('monto_gravado', 0):,.2f}",
                            f"${comp.get('monto_iva', 0):,.2f}",
                            f"${comp.get('monto_total', 0):,.2f}",
                            comp.get('tipo_operacion', '')
                        ]
                        
                        for c, v in enumerate(vals):
                            item = QTableWidgetItem(str(v))
                            self._tbl_comprobantes.setItem(r, c, item)
                    
                    # Calcular resumen del período actual
                    self._calcular_resumen_periodo()
                except Exception as e:
                    logging.warning(f"Error cargando comprobantes enterprise: {e}")
            else:
                QMessageBox.warning(self, "Modo Enterprise", 
                    "El modo enterprise no está activado. Las funciones de impuestos avanzadas requieren los motores enterprise.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error cargando impuestos: {e}")
    
    def _calcular_resumen_periodo(self):
        """Calcula el resumen de IVA del período seleccionado"""
        try:
            from datetime import date
            desde_date = self.date_desde.date().toPyDate()
            hasta_date = self.date_hasta.date().toPyDate()
            
            from src.contabilidad.motor_impuestos import MotorImpuestos
            motor = MotorImpuestos(self._db.db_name)
            liquidacion = motor.liquidar_iva(desde_date, hasta_date)
            
            # Actualizar tarjetas
            self.card_debito.findChild(QLabel, "lbl_valor").setText(f"${liquidacion.get('debito_fiscal', 0):,.2f}")
            self.card_credito.findChild(QLabel, "lbl_valor").setText(f"${liquidacion.get('credito_fiscal', 0):,.2f}")
            
            saldo = liquidacion.get('saldo', 0)
            color = PAL['success'] if saldo >= 0 else PAL['danger']
            self.card_saldo.findChild(QLabel, "lbl_valor").setText(f"${saldo:,.2f}")
            self.card_saldo.findChild(QLabel, "lbl_valor").setStyleSheet(f"font-size: 24px; font-weight: 900; color: {color}; background: transparent;")
            
        except Exception as e:
            logging.warning(f"Error calculando resumen: {e}")
    
    def _liquidar_iva(self):
        if not self._db or not self._db.is_enterprise_mode():
            QMessageBox.warning(self, "Modo Enterprise", "El modo enterprise no está activado.")
            return
        
        try:
            from datetime import date
            desde_date = self.date_desde.date().toPyDate()
            hasta_date = self.date_hasta.date().toPyDate()
            
            from src.contabilidad.motor_impuestos import MotorImpuestos
            motor = MotorImpuestos(self._db.db_name)
            liquidacion = motor.liquidar_iva(desde_date, hasta_date)
            
            resumen = motor.obtener_resumen_iva(desde_date, hasta_date)
            
            # Dialogo educativo con detalle
            dialog = QDialog(self)
            dialog.setWindowTitle(f"Liquidación de IVA - {desde_date.strftime('%m/%Y')} a {hasta_date.strftime('%m/%Y')}")
            dialog.setFixedSize(500, 400)
            
            lay = QVBoxLayout(dialog)
            lay.setSpacing(15)
            
            # Resumen
            resumen_box = QFrame()
            resumen_box.setStyleSheet("background: #F8FAFC; border-radius: 8px; padding: 15px;")
            resumen_lay = QVBoxLayout(resumen_box)
            
            lbl_titulo = QLabel("📊 Liquidación de IVA")
            lbl_titulo.setStyleSheet("font-size: 16px; font-weight: bold;")
            resumen_lay.addWidget(lbl_titulo)
            
            lbl_debito = QLabel(f"Débito Fiscal (IVA cobrado): ${liquidacion.get('debito_fiscal', 0):,.2f}")
            lbl_debito.setStyleSheet("font-size: 14px; color: #DC2626;")
            resumen_lay.addWidget(lbl_debito)
            
            lbl_credito = QLabel(f"Crédito Fiscal (IVA pagado): ${liquidacion.get('credito_fiscal', 0):,.2f}")
            lbl_credito.setStyleSheet("font-size: 14px; color: #059669;")
            resumen_lay.addWidget(lbl_credito)
            
            line = QFrame()
            line.setFrameShape(QFrame.Shape.HLine)
            line.setStyleSheet("background: #CBD5E1;")
            resumen_lay.addWidget(line)
            
            saldo = liquidacion.get('saldo', 0)
            lbl_saldo = QLabel(f"Saldo: ${saldo:,.2f}")
            lbl_saldo.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {'#DC2626' if saldo < 0 else '#059669'};")
            resumen_lay.addWidget(lbl_saldo)
            
            lay.addWidget(resumen_box)
            
            # Explicación
            if saldo > 0:
                explicacion = f"💡 A Pagar a AFIP: ${liquidacion.get('a_pagar', 0):,.2f}\n(Ventas > Compras con IVA)"
            else:
                explicacion = f"💡 A Creditar de AFIP: ${abs(liquidacion.get('a_creditar', 0)):,.2f}\n(Compras > Ventas con IVA)"
            
            lbl_exp = QLabel(explicacion)
            lbl_exp.setStyleSheet("font-size: 13px; color: #475569; padding: 10px; background: #FEF3C7; border-radius: 6px;")
            lay.addWidget(lbl_exp)
            
            # Desglose por alicuota
            if resumen and resumen.get('ventas_por_alicuota'):
                lbl_desglose = QLabel("📋 Desglose por Alicuota:")
                lbl_desglose.setStyleSheet("font-size: 13px; font-weight: bold;")
                lay.addWidget(lbl_desglose)
                
                for item in resumen['ventas_por_alicuota']:
                    txt = f"  • IVA {item['alicuota']}%: ${item['total_iva']:,.2f} ({item['cantidad']} operaciones)"
                    lbl_item = QLabel(txt)
                    lbl_item.setStyleSheet("font-size: 12px; color: #475569;")
                    lay.addWidget(lbl_item)
            
            btn_cerrar = QPushButton("Cerrar")
            btn_cerrar.clicked.connect(dialog.accept)
            btn_cerrar.setStyleSheet("padding: 10px 20px; font-weight: bold;")
            lay.addStretch()
            lay.addWidget(btn_cerrar)
            
            dialog.exec()
            
            # Actualizar tarjetas
            self._calcular_resumen_periodo()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error liquidando IVA: {e}")
    
    def _ver_comprobantes(self):
        self._load_impuestos()
