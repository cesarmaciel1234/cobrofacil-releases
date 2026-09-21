from PyQt6.QtWidgets import QVBoxLayout, QHBoxLayout, QFrame

from src.cajero.paso8_historial.componentes_paso8_historial.panel_detalle import PanelDetalle
from src.cajero.paso8_historial.ui.cabecera import armar_cabecera
from src.cajero.paso8_historial.ui.filtros import armar_filtros
from src.cajero.paso8_historial.ui.lista_tickets import armar_busqueda_y_tabla


def setup_ui(dialogo):
    layout = QVBoxLayout(dialogo)
    layout.setContentsMargins(40, 40, 40, 40)

    main_container = QFrame()
    main_container.setObjectName("HistorialMain")
    layout.addWidget(main_container)

    main_vbox = QVBoxLayout(main_container)
    main_vbox.setContentsMargins(0, 0, 0, 0)
    main_vbox.setSpacing(0)
    main_vbox.addWidget(armar_cabecera(dialogo.accept))

    content_hbox = QHBoxLayout()
    content_hbox.setContentsMargins(10, 10, 10, 10)
    content_hbox.setSpacing(15)

    left_vbox = QVBoxLayout()
    left_vbox.setSpacing(8)
    armar_busqueda_y_tabla(dialogo, left_vbox)
    armar_filtros(dialogo, left_vbox, dialogo.cargar_ventas)

    dialogo.txt_search.textChanged.connect(dialogo.cargar_ventas)
    dialogo.cb_metodo.currentIndexChanged.connect(dialogo.cargar_ventas)
    dialogo.time_desde.timeChanged.connect(dialogo.cargar_ventas)
    dialogo.time_hasta.timeChanged.connect(dialogo.cargar_ventas)
    dialogo.tabla_tickets.itemSelectionChanged.connect(dialogo.mostrar_detalle)

    content_hbox.addLayout(left_vbox, 45)

    dialogo.panel_detalle = PanelDetalle(dialogo)
    dialogo.panel_detalle.set_callbacks(
        dialogo.cancelar_venta_accion, dialogo.reimprimir_ticket_accion
    )
    content_hbox.addWidget(dialogo.panel_detalle, 55)
    main_vbox.addLayout(content_hbox)
