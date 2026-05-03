import streamlit as st
import pandas as pd

from utils.data_loader import cargar_todo
from services.calculo_puntos import calcular_puntos
from utils.dataframe_utils import (
    safe_int,
    asegurar_columnas
)


USUARIO_ACTUAL = "usuario_demo"

def historial_page():

    st.title("Mi historial de apuestas")


    # ===== carga centralizada =====

    data = cargar_todo()

    df_pred = data["predicciones"].copy()

    df_res = data["resultados"].copy()

    df_part = data["partidos"].copy()

    # ==============================

    if st.session_state.get("rol") == "admin":
        st.warning("Este módulo es solo para participantes")
        st.stop()

    if len(df_pred) == 0:

        st.info("Aún no tienes apuestas")

        return


    df_pred = df_pred[

        df_pred["usuario_id"] == USUARIO_ACTUAL

    ]


    if len(df_pred) == 0:

        st.info("Aún no tienes apuestas")

        return


    # asegurar columnas necesarias

    df_pred = asegurar_columnas(

        df_pred,

        ["usuario_id","partido_id","goles_local","goles_visitante"]

    )


    df_res = asegurar_columnas(

        df_res,

        ["partido_id","goles_local","goles_visitante"]

    )


    # unir datos

    df = df_pred.merge(

        df_res,

        on="partido_id",

        suffixes=("_pred","_real"),

        how="left"

    )


    df = df.merge(

        df_part[

            ["id","equipo_local","equipo_visitante","fecha"]

        ],

        left_on="partido_id",

        right_on="id",

        how="left"

    )


    # convertir valores

    for col in [

        "goles_local_pred",
        "goles_visitante_pred",
        "goles_local_real",
        "goles_visitante_real"

    ]:

        df[col] = df[col].apply(safe_int)


    # calcular puntos

    df["puntos"] = df.apply(
        lambda x: calcular_puntos(
            x["goles_local_pred"],
            x["goles_visitante_pred"],
            x["goles_local_real"],
            x["goles_visitante_real"],
            x.get("participa", 1)  # 👈 CLAVE
        ),
        axis=1
    )


    # formato tabla

    df["partido"] = (

        df["equipo_local"]

        + " vs "

        + df["equipo_visitante"]

    )


    df["prediccion"] = (

        df["goles_local_pred"].astype(str)

        + " - "

        + df["goles_visitante_pred"].astype(str)

    )


    df["resultado"] = (

        df["goles_local_real"].astype(str)

        + " - "

        + df["goles_visitante_real"].astype(str)

    )


    df["premio"] = 0

    data = cargar_todo()
    df_mov = data["movimientos"]

    # ❌ ocultar reversos al usuario
    df_mov = df_mov[df_mov["tipo"] != "reverso_premio"]

    for i, row in df.iterrows():

        mov = df_mov[
            (df_mov["usuario_id"] == USUARIO_ACTUAL)
            &
            (df_mov["referencia"] == f"partido_{row['partido_id']}")
            &
            (df_mov["tipo"] == "premio")
        ]

        if len(mov) > 0:
            df.at[i, "premio"] = mov["monto"].sum()


    tabla = df[
        [
            "fecha",
            "partido",
            "prediccion",
            "resultado",
            "puntos",
            "premio"
        ]
    
    ].sort_values(

        by="fecha"

    )


    st.dataframe(

        tabla,

        use_container_width=True

    )