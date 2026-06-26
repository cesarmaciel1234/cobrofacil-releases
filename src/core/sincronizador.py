from src.utils.qt_compat import qt_exec
import sqlite3
from PyQt6.QtWidgets import QMessageBox
from src.base_de_datos.database import db_manager

def sincronizar_facturas(sqlite_db_path, parent_widget=None):
    """
    Motor de sincronización bidireccional contable (MariaDB en red <-> SQLite portátil).
    Utiliza una clave combinada: Proveedor + Número de Factura.
    """
    
    # 4. MODO OFFLINE SEGURO
    try:
        # Hacemos un ping ligero a MariaDB para comprobar la conexión del Local
        res = db_manager.execute_query("SELECT 1")
        if res is None:
            raise Exception("Base de datos retornó None")
    except Exception as e:
        if parent_widget:
            QMessageBox.warning(parent_widget, "Modo Offline", 
                "No se detecta conexión con MariaDB del local.\n"
                "Se activará el Modo Offline.\n"
                "Puedes seguir trabajando y cargar datos en la base local (SQLite) para la próxima sincronización."
            )
        return

    # Conectar a SQLite Portátil (Notebook del Jefe)
    try:
        conn = sqlite3.connect(sqlite_db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
    except Exception as e:
        if parent_widget:
            QMessageBox.critical(parent_widget, "Error", f"No se pudo abrir la base SQLite portátil:\n{e}")
        return

    try:
        # 1. SUBIDA (SQLite -> MariaDB del Local)
        # Buscar en la SQLite local los registros cargados en casa que no se han subido
        cursor.execute("SELECT * FROM facturas WHERE sincronizado = 0")
        facturas_locales = cursor.fetchall()
        
        for f in facturas_locales:
            prov = str(f['proveedor'])
            num_fac = str(f['numero_factura'])
            
            # Verificar si existe en MariaDB (Clave Combinada)
            res_mariadb = db_manager.execute_query(
                "SELECT * FROM facturas WHERE proveedor = ? AND numero_factura = ?", 
                (prov, num_fac)
            )
            
            if not res_mariadb:
                # No existe en MariaDB, lo insertamos
                query_insert = """
                    INSERT INTO facturas (proveedor, numero_factura, total_factura, fecha, estado_pago) 
                    VALUES (?, ?, ?, ?, ?)
                """
                db_manager.execute_query(query_insert, (prov, num_fac, f['total_factura'], f['fecha'], f['estado_pago']))
                
                # Marcar como sincronizado en SQLite
                cursor.execute("UPDATE facturas SET sincronizado = 1 WHERE id = ?", (f['id'],))
            else:
                # 2. DETECCIÓN DE COMPATIBILIDAD Y CONFLICTOS
                mdb = res_mariadb[0]
                total_mdb = float(mdb['total_factura'] if mdb['total_factura'] else 0)
                total_sql = float(f['total_factura'] if f['total_factura'] else 0)
                
                if (total_mdb != total_sql or 
                    str(mdb['fecha']) != str(f['fecha']) or 
                    str(mdb['estado_pago']) != str(f['estado_pago'])):
                    
                    if parent_widget:
                        msg = f"Conflicto detectado en la Factura {num_fac} del Proveedor {prov}.\n\n"
                        msg += f"📦 Versión Local (MariaDB):\n"
                        msg += f"   Total: ${total_mdb:.2f} | Fecha: {mdb['fecha']} | Estado: {mdb['estado_pago']}\n\n"
                        msg += f"💻 Versión Notebook (SQLite):\n"
                        msg += f"   Total: ${total_sql:.2f} | Fecha: {f['fecha']} | Estado: {f['estado_pago']}\n\n"
                        msg += "¿Qué versión desea conservar y unificar en ambos lados?"
                        
                        mbox = QMessageBox(parent_widget)
                        mbox.setWindowTitle("Conflicto de Sincronización")
                        mbox.setText(msg)
                        mbox.setIcon(QMessageBox.Warning)
                        
                        btn_local = mbox.addButton("Conservar versión del Local", QMessageBox.AcceptRole)
                        btn_notebook = mbox.addButton("Conservar versión de la Notebook", QMessageBox.RejectRole)
                        qt_exec(mbox)
                        
                        if mbox.clickedButton() == btn_notebook:
                            # Sobrescribir en MariaDB con los datos de SQLite
                            query_update = "UPDATE facturas SET total_factura = ?, fecha = ?, estado_pago = ? WHERE proveedor = ? AND numero_factura = ?"
                            db_manager.execute_query(query_update, (f['total_factura'], f['fecha'], f['estado_pago'], prov, num_fac))
                    
                    # Sea cual sea la decisión (o si se omite la UI), en SQLite queda marcado como sincronizado
                    cursor.execute("UPDATE facturas SET sincronizado = 1 WHERE id = ?", (f['id'],))

        conn.commit()

        # 3. BAJADA (De MariaDB del Local a SQLite de la Notebook)
        # Trae desde MariaDB todas las facturas y verifica cuáles faltan en la SQLite local
        todas_mariadb = db_manager.execute_query("SELECT * FROM facturas")
        if todas_mariadb:
            for mdb in todas_mariadb:
                prov = str(mdb['proveedor'])
                num_fac = str(mdb['numero_factura'])
                
                # Verificar si ya la tenemos en la Notebook
                cursor.execute("SELECT id FROM facturas WHERE proveedor = ? AND numero_factura = ?", (prov, num_fac))
                exists_sql = cursor.fetchone()
                
                if not exists_sql:
                    # Insertar la factura nueva creada en el local mientras el Jefe no estaba
                    cursor.execute("""
                        INSERT INTO facturas (proveedor, numero_factura, total_factura, fecha, estado_pago, sincronizado) 
                        VALUES (?, ?, ?, ?, ?, 1)
                    """, (prov, num_fac, mdb['total_factura'], mdb['fecha'], mdb['estado_pago']))
            
            conn.commit()
            
        if parent_widget:
            QMessageBox.information(parent_widget, "Sincronización Exitosa", "La sincronización bidireccional contable se ha completado correctamente.")

    except Exception as e:
        if parent_widget:
            QMessageBox.critical(parent_widget, "Error en Sincronización", f"Hubo un error fatal durante la sincronización:\n{e}")
    finally:
        conn.close()