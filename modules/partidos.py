import streamlit as st

from utils.data_loader import cargar_todo


def partidos_page():

    st.title("Partidos disponibles")

    data = cargar_todo()

    df = data["partidos"].copy()

    if len(df) == 0:

        st.warning("no hay partidos cargados")

        return

    st.dataframe(df, use_container_width=True)

    st.write("total partidos:", len(df))