import streamlit as st
import pandas as pd

from database.google_sheets import connect


def partidos_page():

    st.title("Partidos disponibles")

    db = connect()

    sheet = db.worksheet("partidos")

    data = sheet.get_all_records()

    df = pd.DataFrame(data)

    if len(df) == 0:

        st.warning("no hay partidos cargados")

        return

    st.dataframe(df)

    st.write("total partidos:", len(df))