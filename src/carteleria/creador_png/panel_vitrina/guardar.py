"""Asocia el PNG al producto y avisa en castellano. El error HTTP no tapa el listo local."""


def asociar(producto_id, filename, producto_nombre="") -> tuple[bool, str]:
    from src.carteleria.assets_paths import png_productos_dir
    from src.carteleria.creador_png.panel_vitrina.archivo import asegurar_vivo
    from src.motor_inventario.base.productos_db import guardar_icono_producto

    vivo = filename
    if filename and producto_nombre:
        vivo = asegurar_vivo(filename, producto_nombre, png_productos_dir())
    ok, msg = guardar_icono_producto(producto_id, vivo)
    if ok:
        return True, vivo or ""
    return False, msg


def copiar_a_maestra(filename: str) -> str:
    """Texto extra para el cartel. Vacío si no hay que decir nada."""
    from src.central_red_global.sync_tienda.png.esclava import enviar_png_a_maestra

    _ok, msg = enviar_png_a_maestra(filename)
    return msg or ""


def texto_listo(aviso_red: str) -> str:
    base = "Listo. La cartelería va a mostrar ese PNG en las tarjetas de ese producto."
    extra = (aviso_red or "").strip()
    if extra.startswith("HTTP") or "401" in extra or "Unauthorized" in extra:
        extra = (
            "El PNG quedó en esta PC. La TV de acá ya lo puede mostrar. "
            "La copia a otra máquina no se hizo."
        )
    if extra:
        return base + "\n\n" + extra
    return base
