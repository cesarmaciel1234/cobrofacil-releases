# Crédito Aprobado (Paso 2)

Qué hace: Contiene la interfaz visual que se muestra cuando el motor principal confirma que un cliente tiene crédito aprobado, antes de cobrarle o añadir a su cuenta.
Qué función: PanelCreditoAprobado en panel_aprobado.py
Cómo funciona: Se instancia y se inyectan los datos (nombre, límite, compra). El botón emite confirmado al darle Enter.
Qué no debe cambiar una mejora futura: Debe mantenerse desacoplado del motor de base de datos; solo recibe variables y emite clics.
