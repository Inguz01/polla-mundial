from datetime import datetime

from database.google_sheets import connect

from utils.helpers import generar_id



def registrar_movimiento(

    usuario_id,

    tipo,

    referencia,

    monto

):

    db = connect()

    sheet = db.worksheet("movimientos")


    fecha = datetime.now().strftime(

        "%Y-%m-%d %H:%M:%S"

    )


    sheet.append_row([

        generar_id(),

        usuario_id,

        fecha,

        tipo,

        referencia,

        monto

    ])