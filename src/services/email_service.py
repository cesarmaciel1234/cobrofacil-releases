import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.header import Header
import datetime
from src.config import config
try:
    from src.base_de_datos.database import db_manager
except ImportError:
    from database import db_manager
import logging

logger = logging.getLogger(__name__)

def obtener_datos_semana_anterior():
    """
    Obtiene los datos de ventas de la semana pasada (lunes a domingo).
    Retorna (total_semana, top7_cantidad, top7_recaudacion, inicio_sem, fin_sem)
    """
    hoy = datetime.datetime.now().date()
    # Si hoy es lunes (0) a domingo (6), restar días para llegar al domingo de la semana pasada
    # Por ejemplo, si hoy es lunes (0), restamos 1 para llegar al domingo (-1 = 6)
    dias_para_domingo_pasado = hoy.weekday() + 1
    fin_sem = hoy - datetime.timedelta(days=dias_para_domingo_pasado)
    inicio_sem = fin_sem - datetime.timedelta(days=6)
    
    # Formato para la query (inicio del lunes hasta el final del domingo)
    fecha_ini = inicio_sem.strftime('%Y-%m-%d 00:00:00')
    fecha_fin = fin_sem.strftime('%Y-%m-%d 23:59:59')

    # Total de ventas de la semana
    q_ventas = """
        SELECT SUM(total) as total
        FROM ventas 
        WHERE estado = 'COMPLETADA' 
          AND fecha >= ? AND fecha <= ?
    """
    res_ventas = db_manager.execute_query(q_ventas, (fecha_ini, fecha_fin))
    total_semana = res_ventas[0]['total'] if res_ventas and res_ventas[0]['total'] else 0.0

    # Top 7 más vendidos por CANTIDAD
    q_top_cant = """
        SELECT d.nombre_producto, SUM(d.cantidad) as total_cant, SUM(d.subtotal) as total_rec
        FROM detalles_ventas d
        JOIN ventas v ON d.id_venta = v.id
        WHERE v.estado = 'COMPLETADA'
          AND v.fecha >= ? AND v.fecha <= ?
        GROUP BY d.nombre_producto
        ORDER BY total_cant DESC
        LIMIT 7
    """
    top7_cantidad = db_manager.execute_query(q_top_cant, (fecha_ini, fecha_fin)) or []

    # Top 7 mayor RECAUDACIÓN
    q_top_rec = """
        SELECT d.nombre_producto, SUM(d.cantidad) as total_cant, SUM(d.subtotal) as total_rec
        FROM detalles_ventas d
        JOIN ventas v ON d.id_venta = v.id
        WHERE v.estado = 'COMPLETADA'
          AND v.fecha >= ? AND v.fecha <= ?
        GROUP BY d.nombre_producto
        ORDER BY total_rec DESC
        LIMIT 7
    """
    top7_recaudacion = db_manager.execute_query(q_top_rec, (fecha_ini, fecha_fin)) or []

    return total_semana, top7_cantidad, top7_recaudacion, inicio_sem, fin_sem

def generar_html_reporte(total, top7_cant, top7_rec, inicio, fin):
    """
    Genera el HTML bonito del reporte.
    """
    moneda = config.get("currency_symbol", "$")
    nombre_negocio = config.get("business_name", "Mi Negocio")
    fecha_str = f"Del {inicio.strftime('%d/%m/%Y')} al {fin.strftime('%d/%m/%Y')}"
    
    html = f"""
    <html>
    <body style="font-family: Arial, sans-serif; background-color: #f3f4f6; margin: 0; padding: 20px;">
        <div style="max-width: 600px; margin: auto; background: white; border-radius: 10px; padding: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
            <h2 style="color: #1e3a8a; text-align: center; border-bottom: 2px solid #e5e7eb; padding-bottom: 10px;">
                📊 Reporte Semanal de Ventas
            </h2>
            <h3 style="color: #4b5563; text-align: center; margin-top: 5px;">{nombre_negocio}</h3>
            <p style="text-align: center; color: #6b7280; font-size: 14px;">{fecha_str}</p>
            
            <div style="background-color: #ecfdf5; border-left: 4px solid #10b981; padding: 15px; margin: 20px 0;">
                <p style="margin: 0; color: #065f46; font-size: 16px;">Ventas Totales de la Semana:</p>
                <h1 style="margin: 5px 0 0 0; color: #047857; font-size: 28px;">{moneda} {total:,.2f}</h1>
            </div>
            
            <h3 style="color: #374151; margin-top: 30px;">🏆 Top 7: Productos Más Vendidos (Por Cantidad)</h3>
            <table style="width: 100%; border-collapse: collapse; margin-bottom: 20px;">
                <tr style="background-color: #f9fafb; text-align: left;">
                    <th style="padding: 10px; border-bottom: 1px solid #e5e7eb; width: 60%;">Producto</th>
                    <th style="padding: 10px; border-bottom: 1px solid #e5e7eb; text-align: right;">Cantidad</th>
                </tr>
    """
    
    for row in top7_cant:
        html += f"""
                <tr>
                    <td style="padding: 10px; border-bottom: 1px solid #f3f4f6; color: #4b5563;">{row['nombre_producto']}</td>
                    <td style="padding: 10px; border-bottom: 1px solid #f3f4f6; text-align: right; font-weight: bold; color: #111827;">{row['total_cant']:.2f}</td>
                </tr>
        """
        
    html += f"""
            </table>
            
            <h3 style="color: #374151; margin-top: 30px;">💰 Top 7: Productos de Mayor Recaudación</h3>
            <table style="width: 100%; border-collapse: collapse; margin-bottom: 20px;">
                <tr style="background-color: #f9fafb; text-align: left;">
                    <th style="padding: 10px; border-bottom: 1px solid #e5e7eb; width: 60%;">Producto</th>
                    <th style="padding: 10px; border-bottom: 1px solid #e5e7eb; text-align: right;">Recaudación</th>
                </tr>
    """
    
    for row in top7_rec:
        html += f"""
                <tr>
                    <td style="padding: 10px; border-bottom: 1px solid #f3f4f6; color: #4b5563;">{row['nombre_producto']}</td>
                    <td style="padding: 10px; border-bottom: 1px solid #f3f4f6; text-align: right; font-weight: bold; color: #047857;">{moneda} {row['total_rec']:.2f}</td>
                </tr>
        """
        
    html += """
            </table>
            <div style="text-align: center; margin-top: 40px; padding-top: 20px; border-top: 1px solid #e5e7eb;">
                <p style="color: #9ca3af; font-size: 12px;">Generado automáticamente por TPV PRO.</p>
            </div>
        </div>
    </body>
    </html>
    """
    return html

def enviar_reporte_semanal_si_es_necesario(forzar_envio=False):
    """
    Comprueba si se debe enviar el correo y lo envía.
    Para que se envíe, la configuración de correo debe estar activa, y
    hoy debe ser lunes o el reporte debe estar atrasado.
    Retorna True si envió exitosamente, False de lo contrario.
    """
    activo = config.get("email_report_active", False)
    
    # CONFIGURACIÓN MAESTRA DEL CORREO DE ENVÍO
    # TODO: Cuando crees tu correo de Gmail para el sistema, colócalo aquí abajo
    email_origen = "notificaciones.tpvpro@gmail.com"
    pwd_origen = "TU_CONTRASENA_DE_APLICACION_AQUI"
    
    email_destino = config.get("email_dest", "")

    if not activo or not email_origen or not pwd_origen or not email_destino:
        return False

    hoy = datetime.datetime.now()
    # Identificar la semana del año actual para el control
    # year_week es algo como "2026-W42"
    año, semana, _ = (hoy - datetime.timedelta(days=hoy.weekday())).isocalendar() # Tomar isocalendar del lunes de esta semana
    semana_id = f"{año}-W{semana}"
    
    ultimo_enviado = config.get("last_weekly_report_sent", "")

    # No enviar si no estamos forzando y ya se envió esta semana
    if ultimo_enviado == semana_id and not forzar_envio:
        return False

    # Proceder al envío
    try:
        total, t7c, t7r, inicio, fin = obtener_datos_semana_anterior()
        html_content = generar_html_reporte(total, t7c, t7r, inicio, fin)

        msg = MIMEMultipart("alternative")
        msg['Subject'] = Header(f"📊 Reporte Semanal TPV PRO: {inicio.strftime('%d/%m')} al {fin.strftime('%d/%m')}", "utf-8")
        msg['From'] = email_origen
        msg['To'] = email_destino

        part1 = MIMEText(html_content, 'html', 'utf-8')
        msg.attach(part1)

        # Enviar vía SMTP Gmail (puerto 465 SSL o 587 TLS)
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(email_origen, pwd_origen)
            server.sendmail(email_origen, email_destino, msg.as_string())

        logger.info(f"Reporte semanal enviado con éxito a {email_destino} para la semana {semana_id}")
        config.set("last_weekly_report_sent", semana_id)
        return True

    except Exception as e:
        logger.error(f"Error enviando correo semanal: {e}")
        return False

# -------------------------------------------------------------------------
# REPORTE DIARIO DE CIERRE Z
# -------------------------------------------------------------------------

def generar_html_cierre_z(datos_cierre):
    """
    Genera el HTML para el reporte diario del Cierre Z.
    """
    moneda = config.get("currency_symbol", "$")
    nombre_negocio = config.get("business_name", "Mi Negocio")
    fecha_str = datetime.datetime.now().strftime('%d/%m/%Y %H:%M')
    
    # Extraer datos con defaults seguros
    caja_id = datos_cierre.get('caja_id', 'Global')
    usuario = datos_cierre.get('usuario', 'SISTEMA')
    tipo_cierre = datos_cierre.get('tipo_cierre', 'CIERRE Z MANUAL')
    efectivo_esp = datos_cierre.get('efectivo_esperado', 0.0)
    efectivo_fis = datos_cierre.get('efectivo_fisico', 0.0)
    diferencia = datos_cierre.get('diferencia', 0.0)
    total_ventas = datos_cierre.get('total_ventas', 0.0)
    
    color_diferencia = "#10b981" # Verde ok
    if diferencia < 0: color_diferencia = "#ef4444" # Rojo faltante
    elif diferencia > 0: color_diferencia = "#f59e0b" # Amarillo sobrante

    html = f"""
    <html>
    <body style="font-family: Arial, sans-serif; background-color: #f3f4f6; margin: 0; padding: 20px;">
        <div style="max-width: 600px; margin: auto; background: white; border-radius: 10px; padding: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
            <h2 style="color: #1e3a8a; text-align: center; border-bottom: 2px solid #e5e7eb; padding-bottom: 10px;">
                🧾 Reporte de {tipo_cierre}
            </h2>
            <h3 style="color: #4b5563; text-align: center; margin-top: 5px;">{nombre_negocio} - Caja {caja_id}</h3>
            <p style="text-align: center; color: #6b7280; font-size: 14px;">{fecha_str}</p>
            
            <table style="width: 100%; border-collapse: collapse; margin-top: 20px;">
                <tr>
                    <td style="padding: 10px; border-bottom: 1px solid #f3f4f6; color: #4b5563;">Operador:</td>
                    <td style="padding: 10px; border-bottom: 1px solid #f3f4f6; text-align: right; font-weight: bold; color: #111827;">{usuario}</td>
                </tr>
                <tr>
                    <td style="padding: 10px; border-bottom: 1px solid #f3f4f6; color: #4b5563;">Total Ventas Registradas:</td>
                    <td style="padding: 10px; border-bottom: 1px solid #f3f4f6; text-align: right; font-weight: bold; color: #111827;">{moneda} {total_ventas:,.2f}</td>
                </tr>
                <tr>
                    <td style="padding: 10px; border-bottom: 1px solid #f3f4f6; color: #4b5563;">Efectivo Esperado en Caja:</td>
                    <td style="padding: 10px; border-bottom: 1px solid #f3f4f6; text-align: right; font-weight: bold; color: #111827;">{moneda} {efectivo_esp:,.2f}</td>
                </tr>
                <tr>
                    <td style="padding: 10px; border-bottom: 1px solid #e5e7eb; color: #4b5563;">Efectivo Físico Declarado:</td>
                    <td style="padding: 10px; border-bottom: 1px solid #e5e7eb; text-align: right; font-weight: bold; color: #111827;">{moneda} {efectivo_fis:,.2f}</td>
                </tr>
            </table>

            <div style="background-color: #f9fafb; border-left: 4px solid {color_diferencia}; padding: 15px; margin: 20px 0;">
                <p style="margin: 0; color: #374151; font-size: 14px;">Diferencia (Descuadre):</p>
                <h2 style="margin: 5px 0 0 0; color: {color_diferencia}; font-size: 24px;">{moneda} {diferencia:,.2f}</h2>
            </div>
            
            <div style="text-align: center; margin-top: 40px; padding-top: 20px; border-top: 1px solid #e5e7eb;">
                <p style="color: #9ca3af; font-size: 12px;">Generado automáticamente por TPV PRO.</p>
            </div>
        </div>
    </body>
    </html>
    """
    return html

def enviar_reporte_cierre_z(datos_cierre):
    """
    Envía un correo con el resumen del Cierre Z al administrador.
    datos_cierre = {
        'caja_id': 1, 'usuario': 'Admin', 'tipo_cierre': 'CIERRE Z MANUAL',
        'efectivo_esperado': 1000, 'efectivo_fisico': 1000, 'diferencia': 0, 'total_ventas': 5000
    }
    """
    activo = config.get("email_report_active", False)
    
    email_origen = "notificaciones.tpvpro@gmail.com"
    pwd_origen = "TU_CONTRASENA_DE_APLICACION_AQUI"
    email_destino = config.get("email_dest", "")

    if not activo or not email_origen or not pwd_origen or not email_destino:
        logger.info("Envío de email omitido: configuración incompleta o desactivada.")
        return False

    try:
        html_content = generar_html_cierre_z(datos_cierre)
        caja = datos_cierre.get('caja_id', '?')
        
        msg = MIMEMultipart("alternative")
        msg['Subject'] = Header(f"🔒 TPV PRO: Cierre de Caja {caja} - {datetime.datetime.now().strftime('%d/%m')}", "utf-8")
        msg['From'] = email_origen
        msg['To'] = email_destino

        part1 = MIMEText(html_content, 'html', 'utf-8')
        msg.attach(part1)

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(email_origen, pwd_origen)
            server.sendmail(email_origen, email_destino, msg.as_string())

        logger.info(f"Reporte de Cierre Z enviado a {email_destino}")
        return True

    except Exception as e:
        logger.error(f"Error enviando correo de Cierre Z: {e}")
        return False

