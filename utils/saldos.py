import pandas as pd

from database.google_sheets import connect

from utils.dataframe_utils import normalizar_columnas



def saldo_usuario(usuario_id):

    db = connect()

    sheet = db.worksheet("movimientos")

    data = sheet.get_all_records()

    df = pd.DataFrame(data)

    if len(df) == 0:

        return 0


    df = normalizar_columnas(df)


    df = df[

        df["usuario_id"] == usuario_id

    ]


    df["monto"] = df["monto"].astype(float)


    return df["monto"].sum()