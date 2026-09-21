from PyQt6.QtWidgets import (
    QGridLayout, QLabel, QDateEdit, QPushButton, QComboBox,
    QHBoxLayout, QTimeEdit, QFrame, QVBoxLayout,
)
from PyQt6.QtCore import Qt, QDate, QTime


def armar_filtros(dialogo, left_vbox, on_cargar):
    filter_grid = QGridLayout()
    filter_grid.setColumnStretch(1, 1)

    filter_grid.addWidget(QLabel("Del día:"), 0, 0)
    dialogo.date_filt = QDateEdit(QDate.currentDate())
    dialogo.date_filt.setCalendarPopup(True)
    dialogo.date_filt.dateChanged.connect(on_cargar)
    filter_grid.addWidget(dialogo.date_filt, 0, 1)

    btn_hoy = QPushButton("Hoy")
    btn_hoy.clicked.connect(lambda: dialogo.date_filt.setDate(QDate.currentDate()))
    filter_grid.addWidget(btn_hoy, 0, 2)

    btn_refresh = QPushButton("Actualizar")
    btn_refresh.setObjectName("BtnRefresh")
    btn_refresh.setFixedHeight(40)
    btn_refresh.clicked.connect(on_cargar)
    filter_grid.addWidget(btn_refresh, 0, 3)

    lbl_met = QLabel("Método:")
    lbl_met.hide()
    filter_grid.addWidget(lbl_met, 2, 0)
    dialogo.cb_metodo = QComboBox()
    dialogo.cb_metodo.addItems(["TODOS", "EFECTIVO", "TARJETA", "TRANSFERENCIA", "MIXTO"])
    dialogo.cb_metodo.hide()
    filter_grid.addWidget(dialogo.cb_metodo, 2, 1, 1, 2)

    time_layout = QHBoxLayout()
    dialogo.time_desde = QTimeEdit(QTime(0, 0, 0))
    dialogo.time_hasta = QTimeEdit(QTime(23, 59, 59))
    dialogo.time_desde.hide()
    dialogo.time_hasta.hide()
    lbl_de = QLabel("De:")
    lbl_de.hide()
    lbl_a = QLabel("A:")
    lbl_a.hide()
    time_layout.addWidget(lbl_de)
    time_layout.addWidget(dialogo.time_desde)
    time_layout.addWidget(lbl_a)
    time_layout.addWidget(dialogo.time_hasta)
    filter_grid.addLayout(time_layout, 3, 1, 1, 2)

    dialogo.total_card = QFrame()
    dialogo.total_card.hide()
    dialogo.total_card.setObjectName("HistorialTotalCard")
    t_lay = QVBoxLayout(dialogo.total_card)
    t_lay.setContentsMargins(15, 15, 15, 15)
    dialogo.lbl_total_filtrado = QLabel("Ventas en tabla: $0.00")
    dialogo.lbl_total_filtrado.setObjectName("HistorialTotalFiltered")
    dialogo.lbl_total_filtrado.setAlignment(Qt.AlignmentFlag.AlignCenter)
    t_lay.addWidget(dialogo.lbl_total_filtrado)
    filter_grid.addWidget(dialogo.total_card, 4, 0, 1, 3)

    left_vbox.addLayout(filter_grid)
