"""Persiste config. Memoria y disco en el hilo de la UI. MariaDB en el hilo de trabajo."""

from __future__ import annotations

import json


def persistir_memoria(datos: dict) -> None:
    from src.carteleria.lanzador_tv.perfil_pc import limpiar_cache_perfil
    from src.carteleria.lanzador_tv.cerebro_lanzador_tv import aplicar_config_tv_memoria

    limpiar_cache_perfil()
    aplicar_config_tv_memoria(datos)


def persistir_local(datos: dict) -> None:
    from src.config import config

    for clave, valor in datos.items():
        config.set(clave, valor)
    config.save()


def persistir_db(datos: dict) -> tuple[bool, str]:
    from src.base_de_datos.database import db_manager

    db_manager.execute_non_query(
        "CREATE TABLE IF NOT EXISTS carteleria_config (id INT PRIMARY KEY, config_json TEXT)"
    )
    ok = db_manager.execute_non_query(
        "REPLACE INTO carteleria_config (id, config_json) VALUES (1, ?)",
        (json.dumps(datos),),
    )
    if not ok:
        return False, str(getattr(db_manager, "last_error", "") or "REPLACE carteleria_config falló")
    return True, ""


def revertir_memoria() -> None:
    from src.carteleria.lanzador_tv.cerebro_lanzador_tv import invalidar_cache_config_tv

    invalidar_cache_config_tv()
