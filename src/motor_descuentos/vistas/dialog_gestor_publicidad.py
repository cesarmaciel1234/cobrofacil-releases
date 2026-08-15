from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QListWidget, QListWidgetItem, QMessageBox
)
from PyQt6.QtCore import Qt
from src.carteleria.el_cerebro.las_manos.elegir_publicidad import motor_publicidad
from src.motor_descuentos.cerebro.motor_ofertas import MotorOfertas
import random

class DialogGestorPublicidad(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("⭐ Gestor Global de Publicidad")
        self.resize(600, 700)
        
        self.motor_db = MotorOfertas()
        self.productos_db = []
        
        self._init_ui()
        self.cargar_datos()
        
    def _init_ui(self):
        lay = QVBoxLayout(self)
        
        # Header
        lbl_info = QLabel("Selecciona qué productos deseas inyectar en la TV como <b>PRODUCTO PROMOCIONADO</b>.<br>Se mostrarán con diseño exclusivo (fondo amarillo, texto rojo) en la cuadrícula y laterales.")
        lbl_info.setWordWrap(True)
        lay.addWidget(lbl_info)
        
        # Botonera superior
        btn_azar = QPushButton("🎲 Seleccionar 5 al Azar")
        btn_azar.clicked.connect(self.seleccionar_azar)
        btn_limpiar = QPushButton("🧹 Limpiar Todo")
        btn_limpiar.clicked.connect(self.limpiar_seleccion)
        
        top_lay = QHBoxLayout()
        top_lay.addWidget(btn_azar)
        top_lay.addWidget(btn_limpiar)
        lay.addLayout(top_lay)
        
        # Lista
        self.list_widget = QListWidget()
        lay.addWidget(self.list_widget)
        
        # Footer
        btn_guardar = QPushButton("💾 GUARDAR PUBLICIDAD")
        btn_guardar.setStyleSheet("background-color: #FACC15; color: #000000; font-weight: bold; padding: 10px; border-radius: 5px;")
        btn_guardar.clicked.connect(self.guardar_cambios)
        lay.addWidget(btn_guardar)
        
    def cargar_datos(self):
        # Obtener todos los productos (optimizamos para no traer millones si no es necesario, pero como es lista...)
        self.productos_db = self.motor_db.buscar_productos("", None, False) or []
        
        # Llenar lista
        motor_publicidad.cargar_configuracion()
        promos_actuales = motor_publicidad._promocionados_cache
        
        for r in self.productos_db:
            nombre = r.get("nombre", "")
            if not nombre: continue
            
            item = QListWidgetItem(nombre.upper())
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            
            # Verificar si está en la caché de promocionados
            esta_promo = any(p in str(nombre).lower().strip() for p in promos_actuales) if promos_actuales else False
            item.setCheckState(Qt.CheckState.Checked if esta_promo else Qt.CheckState.Unchecked)
            
            self.list_widget.addItem(item)
            
        # Si no hay ninguno seleccionado jamás, autoseleccionar 5 al azar (UX Inicial)
        if not promos_actuales and self.list_widget.count() > 0:
            self.seleccionar_azar()

    def seleccionar_azar(self):
        self.limpiar_seleccion()
        indices = list(range(self.list_widget.count()))
        random.shuffle(indices)
        for i in indices[:5]:
            item = self.list_widget.item(i)
            item.setCheckState(Qt.CheckState.Checked)
            
    def limpiar_seleccion(self):
        for i in range(self.list_widget.count()):
            self.list_widget.item(i).setCheckState(Qt.CheckState.Unchecked)

    def guardar_cambios(self):
        seleccionados = []
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if item.checkState() == Qt.CheckState.Checked:
                seleccionados.append(item.text().strip())
                
        motor_publicidad.guardar_configuracion(seleccionados)
        QMessageBox.information(self, "Éxito", f"Se han configurado {len(seleccionados)} productos como Publicidad.")
        self.accept()
