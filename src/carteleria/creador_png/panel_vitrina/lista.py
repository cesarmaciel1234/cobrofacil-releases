"""Lista de productos con PNG."""

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QTreeWidgetItem


def cargar(tree, texto):
    from src.motor_inventario.base.productos_db import listar_productos_png

    tree.clear()
    rows = listar_productos_png(texto)
    for r in rows:
        png = str(r.get("icono") or "").strip()
        it = QTreeWidgetItem(tree, [
            str(r.get("nombre") or ""),
            str(r.get("departamento") or r.get("categoria") or "—"),
            png or "—",
        ])
        it.setData(0, Qt.ItemDataRole.UserRole, r.get("id"))
        it.setData(0, Qt.ItemDataRole.UserRole + 1, png)
        it.setData(0, Qt.ItemDataRole.UserRole + 2, str(r.get("departamento") or r.get("categoria") or ""))


def reseleccionar(tree, nombre, al_elegir):
    for i in range(tree.topLevelItemCount()):
        item = tree.topLevelItem(i)
        if item.text(0) == nombre:
            tree.setCurrentItem(item)
            al_elegir(item, 0)
            break
