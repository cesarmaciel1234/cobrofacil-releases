from src.utils.qt_compat import qt_exec
from src.utils.theme_manager import theme_manager
from PyQt6.QtWidgets import (

    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, 
    QScrollArea, QPushButton, QGridLayout, QSizePolicy,
    QDialog, QTableWidget, QTableWidgetItem, QHeaderView, QLineEdit, QComboBox, QMessageBox, QInputDialog, QCheckBox,
    QFileDialog, QTextEdit, QGraphicsDropShadowEffect
)
from PyQt6.QtCore import Qt, pyqtSignal, QThread
from PyQt6.QtGui import QCursor, QFont, QColor
import os, shutil, datetime, glob
from src.config import config
try:
    from src.base_de_datos.database import db_manager
except ImportError:
    from database import db_manager


class DialogoImpuestos(QDialog):
    """Configuración de IVA General e IVA por Departamentos."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("💰 Configuración de Impuestos e IVA")
        self.setFixedSize(560, 520)
        self.setStyleSheet("background-color: white; font-family: 'Segoe UI', sans-serif;")
        self._build()

    def _build(self):
        main_lay = QVBoxLayout(self)
        main_lay.setContentsMargins(25, 25, 25, 25)
        main_lay.setSpacing(15)

        # Encabezado
        header = QLabel("💰 Impuestos e IVA por Departamento")
        header.setStyleSheet("font-size: 18px; font-weight: bold;  border:none;")
        main_lay.addWidget(header)

        # Sección IVA General
        general_box = QFrame()
        general_box.setStyleSheet(" border: 1px solid #E2E8F0; border-radius: 8px;")
        gen_lay = QHBoxLayout(general_box)
        gen_lay.setContentsMargins(15, 12, 15, 12)
        
        lbl_gen = QLabel("Tasa de IVA General por defecto (%):")
        lbl_gen.setStyleSheet("font-size: 13px;  font-weight: bold; border:none;")
        
        self.txt_iva_gen = QLineEdit(str(config.get("tax_percentage", 21.0)))
        self.txt_iva_gen.setFixedWidth(80)
        self.txt_iva_gen.setStyleSheet("background: white; border: 1px solid #CBD5E1; border-radius: 4px; padding: 6px; font-size: 13px;")
        
        gen_lay.addWidget(lbl_gen)
        gen_lay.addWidget(self.txt_iva_gen)
        gen_lay.addStretch()
        main_lay.addWidget(general_box)

        # Título Tabla
        lbl_tbl = QLabel("Tasas de IVA específicas por Departamento:")
        lbl_tbl.setStyleSheet("font-size: 13px;  font-weight: bold; border:none;")
        main_lay.addWidget(lbl_tbl)

        # Tabla
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["ID", "Nombre Departamento", "Tasa IVA (%)"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.horizontalHeader().setStyleSheet("QHeaderView::section {   font-weight: bold; border: 1px solid #E2E8F0; padding: 5px; }")
        self.table.setStyleSheet("""
            QTableWidget { background-color: white; border: 1px solid #E2E8F0; border-radius: 6px; }
            QTableWidget::item { padding: 8px;  }
        """)
        main_lay.addWidget(self.table)

        self._cargar_departamentos()

        # Botones de Acción
        h_act = QHBoxLayout()
        btn_add = QPushButton("➕ Agregar Departamento")
        btn_add.setStyleSheet(" background-color: #3B82F6; color: white; font-weight: bold; padding: 8px 12px; border-radius: 6px; border: none;")
        btn_add.setCursor(Qt.PointingHandCursor)
        btn_add.clicked.connect(self._agregar_departamento)
        
        btn_del = QPushButton("🗑️ Eliminar Seleccionado")
        btn_del.setStyleSheet(" background-color: #3B82F6; color: white; font-weight: bold; padding: 8px 12px; border-radius: 6px; border: none;")
        btn_del.setCursor(Qt.PointingHandCursor)
        btn_del.clicked.connect(self._eliminar_departamento)

        h_act.addWidget(btn_add)
        h_act.addWidget(btn_del)
        h_act.addStretch()
        main_lay.addLayout(h_act)

        # Botones Inferiores (Guardar/Cancelar)
        h_btns = QHBoxLayout()
        btn_cancel = QPushButton("Cancelar")
        btn_cancel.setStyleSheet("padding: 10px 18px; font-weight: bold;   border-radius: 8px; border: none;")
        btn_cancel.setCursor(Qt.PointingHandCursor)
        btn_cancel.clicked.connect(self.reject)
        
        btn_save = QPushButton("💾 Guardar Todo")
        btn_save.setStyleSheet("padding: 10px 18px; font-weight: bold;  background-color: #3B82F6; color: white; border-radius: 8px; border: none;")
        btn_save.setCursor(Qt.PointingHandCursor)
        btn_save.clicked.connect(self._guardar)
        
        h_btns.addWidget(btn_cancel)
        h_btns.addStretch()
        h_btns.addWidget(btn_save)
        main_lay.addLayout(h_btns)

    def _cargar_departamentos(self):
        from src.base_de_datos.database import db_manager
        rows = db_manager.execute_query("SELECT id, nombre, iva FROM departamentos ORDER BY id ASC")
        self.table.setRowCount(0)
        if rows:
            for r in rows:
                row_idx = self.table.rowCount()
                self.table.insertRow(row_idx)
                
                # ID (No editable)
                id_item = QTableWidgetItem(str(r['id']))
                id_item.setFlags(id_item.flags() & ~Qt.ItemIsEditable)
                self.table.setItem(row_idx, 0, id_item)
                
                # Nombre
                self.table.setItem(row_idx, 1, QTableWidgetItem(r['nombre']))
                
                # IVA (%)
                self.table.setItem(row_idx, 2, QTableWidgetItem(f"{r['iva']:.1f}"))

    def _agregar_departamento(self):
        row_idx = self.table.rowCount()
        self.table.insertRow(row_idx)
        
        id_item = QTableWidgetItem("NUEVO")
        id_item.setFlags(id_item.flags() & ~Qt.ItemIsEditable)
        self.table.setItem(row_idx, 0, id_item)
        
        self.table.setItem(row_idx, 1, QTableWidgetItem("NUEVO_DEP"))
        self.table.setItem(row_idx, 2, QTableWidgetItem("21.0"))

    def _eliminar_departamento(self):
        curr_row = self.table.currentRow()
        if curr_row < 0:
            QMessageBox.warning(self, "Eliminar", "Por favor selecciona un departamento en la tabla.")
            return
            
        id_val = self.table.item(curr_row, 0).text()
        nombre_val = self.table.item(curr_row, 1).text()
        
        confirm = QMessageBox.question(
            self, "Confirmar", 
            f"¿Estás seguro de que deseas eliminar el departamento '{nombre_val}'?\n"
            f"Los productos asociados a este departamento quedarán sin asignación.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if confirm == QMessageBox.StandardButton.Yes:
            if id_val != "NUEVO":
                from src.base_de_datos.database import db_manager
                db_manager.execute_non_query("DELETE FROM departamentos WHERE id = ?", (int(id_val),))
            self.table.removeRow(curr_row)

    def _guardar(self):
        try:
            # 1. Guardar IVA General en Config
            try:
                iva_gen = float(self.txt_iva_gen.text().strip())
                if iva_gen < 0: raise ValueError()
                config.set("tax_percentage", iva_gen)
            except ValueError:
                QMessageBox.warning(self, "Error", "La tasa de IVA General debe ser un número positivo.")
                return

            # 2. Guardar departamentos en la base de datos
            from src.base_de_datos.database import db_manager
            
            for row in range(self.table.rowCount()):
                id_item = self.table.item(row, 0)
                name_item = self.table.item(row, 1)
                iva_item = self.table.item(row, 2)
                
                if not name_item or not iva_item:
                    continue
                    
                id_val = id_item.text()
                name_val = name_item.text().strip().upper()
                
                try:
                    iva_val = float(iva_item.text().strip())
                    if iva_val < 0: raise ValueError()
                except ValueError:
                    QMessageBox.warning(self, "Error", f"Tasa de IVA inválida para el departamento '{name_val}'. Debe ser un número positivo.")
                    return
                
                if id_val == "NUEVO":
                    # Insertar nuevo
                    insert_keyword = "INSERT IGNORE INTO" if getattr(db_manager, "db_engine_type", "sqlite") == "mariadb" else "INSERT OR IGNORE INTO"
                    db_manager.execute_non_query(
                        f"{insert_keyword} departamentos (nombre, iva) VALUES (?, ?)",
                        (name_val, iva_val)
                    )
                else:
                    # Actualizar existente
                    db_manager.execute_non_query(
                        "UPDATE departamentos SET nombre = ?, iva = ? WHERE id = ?",
                        (name_val, iva_val, int(id_val))
                    )

            QMessageBox.information(self, "Impuestos Guardados", "Los impuestos generales y por departamento se han guardado exitosamente.")
            self.accept()
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Error al guardar: {e}")
