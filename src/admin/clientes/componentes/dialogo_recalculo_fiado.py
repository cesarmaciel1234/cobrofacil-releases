from src.utils.qt_compat import qt_exec
from datetime import datetime
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
                             QPushButton, QTableWidget, QTableWidgetItem, 
                             QHeaderView, QLineEdit, QMessageBox, QDialog, 
                             QFormLayout, QDoubleSpinBox, QGraphicsDropShadowEffect, QComboBox)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QColor, QCursor
from src.base_de_datos.database import db_manager
from src.repositories.cliente_repository import ClienteRepository, FIADO_EXPRESS_LIMITE_DEFAULT


from src.admin.clientes.theme import _CLI

class DialogoRecalculoFiado(QDialog):
    def __init__(self, cliente_id, nombre, parent=None):
        super().__init__(parent)
        self.cliente_id = cliente_id
        self.nombre = nombre
        self.db = db_manager
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setFixedSize(650, 500)
        self.setStyleSheet("background: white; border-radius: 15px; border: 2px solid #3B82F6;")
        self._build()

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(25, 25, 25, 25)
        
        lbl_tit = QLabel(f"📈 SIMULADOR DE INFLACIÓN - {self.nombre.upper()}")
        lbl_tit.setStyleSheet("font-size: 16px; font-weight: 900;  border: none;")
        lay.addWidget(lbl_tit)
        
        lbl_sub = QLabel("Calcula la deuda si los productos fiados se cobraran a los precios de HOY.")
        lbl_sub.setStyleSheet(" font-size: 12px; border: none;")
        lay.addWidget(lbl_sub)
        
        self.tabla = QTableWidget(0, 5)
        self.tabla.setHorizontalHeaderLabels(["Fecha", "Producto", "Cant", "P. Original", "P. Hoy"])
        self.tabla.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tabla.setStyleSheet("QTableWidget { border: 1px solid #E2E8F0; border-radius: 8px; font-size: 12px; }")
        lay.addWidget(self.tabla)
        
        self.lbl_resumen = QLabel("")
        self.lbl_resumen.setStyleSheet("font-size: 16px; font-weight: 900; border: none;")
        lay.addWidget(self.lbl_resumen)
        
        h_btns = QHBoxLayout()
        btn_cerrar = QPushButton("VOLVER")
        btn_cerrar.setStyleSheet("  padding: 10px 20px; border-radius: 8px; font-weight: 900;")
        btn_cerrar.clicked.connect(self.reject)
        
        btn_imprimir = QPushButton("🖨️ IMPRIMIR REPORTE")
        btn_imprimir.setStyleSheet(" background-color: #3b82f6; color: white; padding: 10px 20px; border-radius: 8px; font-weight: 900;")
        btn_imprimir.clicked.connect(self._imprimir)
        
        h_btns.addWidget(btn_cerrar)
        h_btns.addStretch()
        h_btns.addWidget(btn_imprimir)
        lay.addLayout(h_btns)
        
        self._cargar_datos()

    def _cargar_datos(self):
        # Obtener los cargos (fiados) no pagados completamente
        # Simplificación: Asumimos que los detalles de la venta del cargo representan la deuda original
        res = self.db.execute_query('''
            SELECT c.fecha, v.id as venta_id
            FROM cuenta_corriente c
            JOIN ventas v ON c.venta_id = v.id
            WHERE c.cliente_id = ? AND c.tipo = 'CARGO'
            ORDER BY c.fecha DESC
        ''', (self.cliente_id,))
        
        if not res:
            self.lbl_resumen.setText("No hay registros de compras fiadas para analizar.")
            return

        total_original = 0.0
        total_hoy = 0.0
        
        self.detalles_impresion = []
        
        for cargo in res:
            detalles = self.db.execute_query('''
                SELECT dv.cantidad, dv.precio_unitario, p.nombre, p.precio as precio_hoy 
                FROM detalles_ventas dv
                JOIN productos p ON dv.id_producto = p.id OR dv.id_producto = p.codigo
                WHERE dv.id_venta = ?
            ''', (cargo['venta_id'],))
            
            for d in detalles:
                row = self.tabla.rowCount()
                self.tabla.insertRow(row)
                
                f_corta = cargo['fecha'].split(' ')[0]
                cant = float(d['cantidad'])
                p_orig = float(d['precio_unitario'])
                p_hoy = float(d['precio_hoy'])
                
                tot_orig = cant * p_orig
                tot_hoy = cant * p_hoy
                
                total_original += tot_orig
                total_hoy += tot_hoy
                
                self.tabla.setItem(row, 0, QTableWidgetItem(f_corta))
                self.tabla.setItem(row, 1, QTableWidgetItem(d['nombre']))
                self.tabla.setItem(row, 2, QTableWidgetItem(f"{cant:,.2f}"))
                self.tabla.setItem(row, 3, QTableWidgetItem(f"${p_orig:,.2f}"))
                
                it_hoy = QTableWidgetItem(f"${p_hoy:,.2f}")
                if p_hoy > p_orig:
                    it_hoy.setForeground(QColor("#DC2626"))
                self.tabla.setItem(row, 4, it_hoy)
                
                self.detalles_impresion.append({
                    "fecha": f_corta, "nombre": d['nombre'], "cant": cant, "p_orig": p_orig, "p_hoy": p_hoy
                })

        dif = total_hoy - total_original
        color = "#DC2626" if dif > 0 else "#10B981"
        self.lbl_resumen.setText(f"Deuda Histórica: ${total_original:,.2f}  |  Deuda a Precios de Hoy: <span style='color:{color}'>${total_hoy:,.2f}</span> (+${dif:,.2f})")

    def _imprimir(self):
        try:
            from src.hardware.printer import printer_manager
            printer_manager.conectar()
            printer_manager.printer.set(align='center', bold=True, double_height=True)
            printer_manager.printer.text("REPORTE DE INFLACION FIADO\n")
            printer_manager.printer.set(align='center', bold=False, double_height=False)
            printer_manager.printer.text(f"Cliente: {self.nombre}\n")
            printer_manager.printer.text("-" * 32 + "\n")
            
            tot_h = 0
            tot_o = 0
            for d in self.detalles_impresion:
                printer_manager.printer.set(align='left')
                printer_manager.printer.text(f"{d['fecha']} | {d['nombre']}\n")
                printer_manager.printer.text(f"Cant: {d['cant']} | P.Hoy: ${d['p_hoy']} (Antes: ${d['p_orig']})\n")
                tot_h += d['cant'] * d['p_hoy']
                tot_o += d['cant'] * d['p_orig']
                
            printer_manager.printer.text("-" * 32 + "\n")
            printer_manager.printer.set(align='right', bold=True)
            printer_manager.printer.text(f"Deuda Registrada: ${tot_o:,.2f}\n")
            printer_manager.printer.text(f"Deuda Actualizada: ${tot_h:,.2f}\n")
            printer_manager.printer.text(f"Diferencia a favor: ${tot_h - tot_o:,.2f}\n")
            printer_manager.printer.cut()
            QMessageBox.information(self, "Impreso", "Reporte impreso correctamente.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Fallo al imprimir: {e}")


