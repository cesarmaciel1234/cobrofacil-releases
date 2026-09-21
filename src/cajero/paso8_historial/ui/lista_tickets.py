from PyQt6.QtWidgets import (
    QHBoxLayout, QLabel, QPushButton, QLineEdit, QTableWidget,
    QHeaderView, QAbstractItemView,
)


def armar_busqueda_y_tabla(dialogo, left_vbox):
    left_vbox.addWidget(QLabel("Puedes buscar por folio o nombre del ticket:"))

    search_bar = QHBoxLayout()
    btn_search = QPushButton()
    btn_search.setFixedWidth(35)
    dialogo.txt_search = QLineEdit()
    search_bar.addWidget(btn_search)
    search_bar.addWidget(dialogo.txt_search)
    left_vbox.addLayout(search_bar)

    tabla = QTableWidget()
    tabla.setColumnCount(4)
    tabla.setHorizontalHeaderLabels(["Folio", "Arts", "Hora", "Total"])
    tabla.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
    tabla.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
    tabla.setColumnWidth(0, 68)
    tabla.setColumnWidth(1, 52)
    tabla.setColumnWidth(2, 96)
    tabla.verticalHeader().setVisible(False)
    tabla.setSelectionBehavior(QAbstractItemView.SelectRows)
    tabla.setEditTriggers(QAbstractItemView.NoEditTriggers)
    dialogo.tabla_tickets = tabla
    left_vbox.addWidget(tabla)
