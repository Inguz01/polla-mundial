import streamlit as st
import pandas as pd

from database.google_sheets import connect
from utils.dataframe_utils import normalizar_columnas


def worksheet_to_df(db, sheet_name):

    try:

        sheet = db.worksheet(sheet_name)

        data = sheet.get_all_records()

        df = pd.DataFrame(data)

        if df.empty:
            return df

        # normalizar columnas
        df.columns = [str(c).strip().lower() for c in df.columns]

        # corregir nombre de columna con typo en Google Sheets
        df = df.rename(columns={"goles_visitantes": "goles_visitante"})

        # eliminar filas completamente vacías que Google Sheets a veces incluye
        df = df.dropna(how="all")
        df = df[~df.apply(lambda r: all(str(v).strip() == "" for v in r), axis=1)]

        # normalizar usuario_id a minúsculas en todas las hojas que lo tengan
        # evita que 'Amaury' en predicciones no matchee con 'amaury' en session_state
        if "usuario_id" in df.columns:
            df["usuario_id"] = df["usuario_id"].astype(str).str.strip().str.lower()

        # normalizar hora: Sheets puede devolver datetime.time → convertir a string "HH:MM"
        if "hora" in df.columns:
            def normalizar_hora(h):
                if hasattr(h, "strftime"):        # datetime.time object
                    return h.strftime("%H:%M")
                h = str(h).strip()
                if len(h) >= 8 and ":" in h:      # "HH:MM:SS" → recortar
                    return h[:5]
                return h                           # ya es "HH:MM" u otro
            df["hora"] = df["hora"].apply(normalizar_hora)

        return df

    except Exception as e:

        st.error(f"Error cargando hoja {sheet_name}: {e}")

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