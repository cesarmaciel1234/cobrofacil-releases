from PyQt6.QtCore import QTimer
from src.utils.qt_compat import qt_exec
from src.cajero.paso5_terminal.componentes_paso5_terminal.componente_tabla_de_productos.mensaje_eliminacion import MensajeEliminacion

def suprimir_articulo(terminal, row):
    """
    Maneja la lógica para eliminar un artículo de la tabla del Paso 5.
    Muestra el cuadro de diálogo de confirmación y, si se acepta, elimina la fila
    y actualiza los totales.
    """
    if row == -1:
        return False
        
    nombre_articulo = ""
    try:
        item_nombre = terminal.tabla.item(row, 1)
        if item_nombre:
            nombre_articulo = item_nombre.text()
    except Exception:
        pass

    dlg = MensajeEliminacion(nombre_articulo=nombre_articulo, parent=terminal)
    
    # En PyQt6, qt_exec retorna Enum o int con comportamiento booleano
    if qt_exec(dlg):
        try:
            terminal.tabla.removeRow(row)
            terminal.actualizar_totales()
        except Exception as e:
            print(f"Error eliminando fila: {e}")
        
        QTimer.singleShot(50, terminal.txt_scan.setFocus)
        return True
        
    QTimer.singleShot(50, terminal.txt_scan.setFocus)
    return False
