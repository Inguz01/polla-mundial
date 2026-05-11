from datetime import datetime

from database.google_sheets import connect
from utils.helpers import generar_id


def registrar_movimiento(usuario_id, tipo, referencia, monto):
    """Registra un solo movimiento en Sheets."""
    registrar_movimientos([{
        "usuario_id": usuario_id,
        "tipo": tipo,
        "referencia": referencia,
        "monto": monto
    }])


def registrar_movimientos(lista):
    """
    Registra múltiples movimientos en una sola llamada a Sheets.
    lista: [{"usuario_id", "tipo", "referencia", "monto"}, ...]
    """
    if not lista:
        return

    db = connect()
    sheet = db.worksheet("movimientos")
    fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    filas = [
        [
            generar_id(),
            str(m["usuario_id"]).strip().lower(),  # normalizar a minúsculas
            fecha,
            m["tipo"],
            m["referencia"],
            m["monto"]
        ]
        for m in lista
    ]

    sheet.append_rows(filas, value_input_option="USER_ENTERED")