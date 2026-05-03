import streamlit as st
import pandas as pd

from database.google_sheets import connect
from utils.dataframe_utils import normalizar_columnas


def worksheet_to_df(db, sheet_name):

    try:

        sheet = db.worksheet(sheet_name)

        data = sheet.get_all_records()

        df = pd.DataFrame(data)

        if len(df) > 0:

            df = normalizar_columnas(df)

        return df

    except:

        return pd.DataFrame()


@st.cache_data(ttl=1800)
def cargar_todo():

    db = connect()

    partidos = worksheet_to_df(db, "partidos")
    predicciones = worksheet_to_df(db, "predicciones")
    resultados = worksheet_to_df(db, "resultados")
    movimientos = worksheet_to_df(db, "movimientos")
    config = worksheet_to_df(db, "config")
    equipos = worksheet_to_df(db, "equipos")
    usuarios = worksheet_to_df(db, "usuarios")

    return {

        "partidos": partidos,
        "predicciones": predicciones,
        "resultados": resultados,
        "movimientos": movimientos,
        "config": config,
        "equipos": equipos,
        "usuarios": usuarios}