import streamlit as st
import pandas as pd

from utils.data_loader import cargar_todo
from utils.dataframe_utils import safe_int
from utils.config import valor_apuesta_por_fase, porcentaje_admin


def resultados_partido_page():

    st.title("Resultados por partido")

    data = cargar_todo()

    df_pred = data["predicciones"].copy()
    df_res = data["resultados"].copy()
    df_part = data["partidos"].copy()

    if len(df_res) == 0:
        st.info("Aún no hay resultados registrados")
        return

    # =========================
    # LIMPIEZA
    # =========================

    df_res["goles_local"] = df_res["goles_local"].apply(safe_int)
    df_res["goles_visitante"] = df_res["goles_visitante"].apply(safe_int)

    # =========================
    # SELECTOR DE PARTIDO
    # =========================

    df_res = df_res.merge(
        df_part[["id", "equipo_local", "equipo_visitante", "fase"]],
        left_on="partido_id",
        right_on="id",
        how="left"
    )

    df_res["partido"] = (
        df_res["equipo_local"] + " vs " + df_res["equipo_visitante"]
    )

    partido_sel = st.selectbox(
        "Selecciona un partido",
        df_res["partido"].unique()
    )

    row_partido = df_res[df_res["partido"] == partido_sel].iloc[0]

    partido_id = row_partido["partido_id"]
    fase = row_partido["fase"]

    real_local = row_partido["goles_local"]
    real_visit = row_partido["goles_visitante"]

    # =========================
    # MOSTRAR RESULTADO
    # =========================

    st.subheader(partido_sel)
    st.write(f"Resultado: {real_local} - {real_visit}")

    # =========================
    # PARTICIPANTES
    # =========================

    df_pred_part = df_pred[
        df_pred["partido_id"].astype(str) == str(partido_id)
    ].copy()

    participantes = len(df_pred_part)

    if participantes == 0:
        st.warning("No hubo participantes en este partido")
        return

    # =========================
    # POZO
    # =========================

    valor = valor_apuesta_por_fase(fase)

    pozo_bruto = participantes * valor
    comision = pozo_bruto * porcentaje_admin()
    pozo = pozo_bruto - comision

    st.divider()

    st.write(f"Participantes: {participantes}")
    st.write(f"Pozo bruto: ${pozo_bruto:,.0f}")
    st.write(f"Comisión: ${comision:,.0f}")
    st.write(f"Pozo a repartir: ${pozo:,.0f}")

    st.divider()

    # =========================
    # GANADORES
    # =========================

    df_pred_part["goles_local"] = df_pred_part["goles_local"].apply(safe_int)
    df_pred_part["goles_visitante"] = df_pred_part["goles_visitante"].apply(safe_int)

    ganadores = df_pred_part[
        (df_pred_part["goles_local"] == real_local)
        &
        (df_pred_part["goles_visitante"] == real_visit)
    ]

    if len(ganadores) > 0:

        premio = pozo / len(ganadores)

        st.success(f"{len(ganadores)} ganador(es)")

        tabla = ganadores[["usuario_id"]].copy()
        tabla["premio"] = premio

        st.dataframe(tabla, use_container_width=True)

    else:

        st.warning("No hubo ganadores")
        st.info(f"💰 ${pozo:,.0f} se acumula al jackpot")