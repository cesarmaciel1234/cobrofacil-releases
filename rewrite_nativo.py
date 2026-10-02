code = '''import traceback
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QLineEdit, QHBoxLayout, QPushButton
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QDoubleValidator

from src.utils.dinero import redondear_dinero

class DialogoAbonoNativo(QDialog):
    def __init__(self, cliente, monto_sugerido, parent=None):
        super().__init__(parent)
        self.cliente = cliente
        self.deuda_actual = float(cliente.get('deuda_actual', 0) or 0)
        self.monto_sugerido = monto_sugerido
        
        self.cliente_id = cliente.get('id')
        self.monto_ingresado = 0.0
        self.tipo_ingreso = 'FIADO'
        self.resultado = None
        
        self.setWindowTitle('Abonar Cuenta')
        self.setFixedSize(540, 480)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setStyleSheet(
            "QDialog { background: #FFFFFF; border-radius: 16px; border: 2px solid #3B82F6; }"
            "QLabel { font-family: 'Segoe UI', Arial; }"
        )
        
        lay = QVBoxLayout(self)
        lay.setContentsMargins(24, 24, 24, 24)
        lay.setSpacing(16)
        
        lbl_titulo = QLabel('PAGO DE CUENTA CORRIENTE')
        lbl_titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_titulo.setStyleSheet('color: #1E3A8A; font-size: 20px; font-weight: 900;')
        lay.addWidget(lbl_titulo)
        
        nombre = cliente.get('nombre', 'Cliente')
        lbl_cliente = QLabel(nombre)
        lbl_cliente.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_cliente.setStyleSheet('color: #475569; font-size: 18px; font-weight: 700;')
        lay.addWidget(lbl_cliente)
        
        info_lay = QHBoxLayout()
        lbl_deuda = QLabel(f'Deuda Previa:\\n')
        lbl_deuda.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_deuda.setStyleSheet('color: #EF4444; font-size: 16px; font-weight: 800;')
        
        venta_actual = monto_sugerido - self.deuda_actual
        lbl_venta = QLabel(f'Venta Actual:\\n')
        lbl_venta.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_venta.setStyleSheet('color: #10B981; font-size: 16px; font-weight: 800;')
        
        info_lay.addWidget(lbl_deuda)
        info_lay.addWidget(lbl_venta)
        lay.addLayout(info_lay)
        
        lbl_input = QLabel('MONTO A ABONAR')
        lbl_input.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_input.setStyleSheet('color: #0F172A; font-size: 14px; font-weight: 800; margin-top: 10px;')
        lay.addWidget(lbl_input)
        
        self.txt_monto = QLineEdit(f'{monto_sugerido:.2f}')
        self.txt_monto.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.txt_monto.setFixedHeight(64)
        self.txt_monto.setValidator(QDoubleValidator(0.0, 9999999.0, 2))
        self.txt_monto.setStyleSheet(
            "QLineEdit { background: #F8FAFC; color: #0F172A; border: 2px solid #CBD5E1; "
            "border-radius: 12px; font-size: 32px; font-weight: 900; }"
            "QLineEdit:focus { border-color: #3B82F6; }"
        )
        lay.addWidget(self.txt_monto)
        
        grid_lay = QHBoxLayout()
        
        self.btn_efectivo = self._crear_boton('Efectivo', '#10B981', '#059669', Qt.Key.Key_F1)
        self.btn_transf = self._crear_boton('Transferencia', '#3B82F6', '#2563EB', Qt.Key.Key_F2)
        self.btn_tarjeta = self._crear_boton('Tarjeta', '#8B5CF6', '#7C3AED', Qt.Key.Key_F3)
        self.btn_mixto = self._crear_boton('Mixto', '#F59E0B', '#D97706', Qt.Key.Key_F4)
        
        grid_lay.addWidget(self.btn_efectivo)
        grid_lay.addWidget(self.btn_transf)
        grid_lay.addWidget(self.btn_tarjeta)
        grid_lay.addWidget(self.btn_mixto)
        lay.addLayout(grid_lay)
        
        self.btn_cancelar = QPushButton('ESC Cancelar')
        self.btn_cancelar.setFixedHeight(44)
        self.btn_cancelar.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_cancelar.setStyleSheet('QPushButton { background: #FFFFFF; color: #64748B; border: 1px solid #CBD5E1; border-radius: 8px; font-weight: 800; } QPushButton:hover { background: #F1F5F9; }')
        self.btn_cancelar.clicked.connect(self.reject)
        lay.addWidget(self.btn_cancelar)
        
        self.txt_monto.setFocus()
        self.txt_monto.selectAll()

    def _crear_boton(self, texto, bg, hover, key):
        btn = QPushButton(texto)
        btn.setFixedHeight(64)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setStyleSheet(
            f"QPushButton {{ background: {bg}; color: #FFFFFF; border: none; border-radius: 12px; font-size: 14px; font-weight: 900; }}"
            f"QPushButton:hover {{ background: {hover}; }}"
        )
        btn.clicked.connect(lambda: self._procesar_medio(texto))
        return btn

    def keyPressEvent(self, event):
        k = event.key()
        if k == Qt.Key.Key_Escape:
            self.reject()
            return
        if k == Qt.Key.Key_F1:
            self._procesar_medio('Efectivo')
            return
        if k == Qt.Key.Key_F2:
            self._procesar_medio('Transferencia')
            return
        if k == Qt.Key.Key_F3:
            self._procesar_medio('Tarjeta')
            return
        if k == Qt.Key.Key_F4:
            self._procesar_medio('Mixto')
            return
        super().keyPressEvent(event)

    def _procesar_medio(self, medio):
        texto = self.txt_monto.text().replace(',', '.')
        if not texto.strip(): return
        monto = redondear_dinero(float(texto))
        if monto <= 0: return
        
        self.monto_ingresado = monto
        
        if medio == 'Mixto':
            from src.clientes_fiado.interfaz.cobro.medios.hoja import pedir_partes
            res = pedir_partes(self, monto)
        else:
            from src.clientes_fiado.interfaz.cobro.medios.puerta import cobrar
            res = cobrar(medio, monto)
            
        if not res or not getattr(res, 'ok', False):
            return
            
        self.resultado = res
        self.accept()
'''

with open('src/cajero/paso6_cobro/fiado_en_cobro/nativo.py', 'w', encoding='utf8') as f:
    f.write(code.replace('\\$', '$'))