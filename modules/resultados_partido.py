import streamlit as st
import pandas as pd

from utils.data_loader import cargar_todo
from utils.dataframe_utils import safe_int
from utils.config import valor_apuesta_por_fase, porcentaje_admin
from services.calculo_pozo import liquidar_partido


def resultados_partido_page():

    st.title("Resultados por partido")

    data = cargar_todo()

    df_pred = data["predicciones"].copy()
    df_res = data["resultados"].copy()
    df_part = data["partidos"].copy()
    df_mov = data["movimientos"].copy()

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
    # RESULTADO
    # =========================

    st.subheader(partido_sel)
    st.write(f"Resultado: {real_local} - {real_visit}")

    # =========================
    # APUESTAS DEL PARTIDO
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

    st.divider()

    if len(ganadores) > 0:

        premio = pozo / len(ganadores)

        st.success(f"{len(ganadores)} ganador(es)")

        tabla = ganadores[["usuario_id"]].copy()
        tabla["premio_estimado"] = round(premio, 2)

        st.dataframe(tabla, use_container_width=True)

    else:

        st.warning("No hubo ganadores")
        st.info(f"💰 ${pozo:,.0f} se acumula al jackpot")

    # =========================
    # JACKPOT ACTUAL
    # =========================

    jackpot_actual = (
        df_mov[df_mov["tipo"] == "jackpot_aporte"]["monto"].sum()
        -
        df_mov[df_mov["tipo"] == "jackpot_pago"]["monto"].sum()
    )

    st.info(f"Jackpot actual: ${jackpot_actual:,.0f}")

    # =========================
    # CONTROL DOBLE LIQUIDACIÓN
    # =========================

    ya_liquidado = df_mov[
        (df_mov["partido_id"].astype(str) == str(partido_id)) &
        (df_mov["tipo"] == "comision")
    ].shape[0] > 0

    st.divider()

    if ya_liquidado:
        st.warning("⚠️ Este partido ya fue liquidado")
        return

    # =========================
    # BOTÓN LIQUIDAR
    # =========================

    if st.button("💰 Liquidar partido"):

        df_liq = df_pred_part.copy()

        # normalizar columnas para el servicio
        df_liq["usuario"] = df_liq["usuario_id"]
        df_liq["valor"] = valor
        df_liq["prediccion"] = (
            df_liq["goles_local"].astype(str)
            + "-"
            + df_liq["goles_visitante"].astype(str)
        )

        resultado_real = f"{real_local}-{real_visit}"

        transacciones, jackpot_nuevo = liquidar_partido(
            df_liq,
            resultado_real,
            jackpot_actual
        )

        # agregar partido_id
        for t in transacciones:
            t["partido_id"] = partido_id

        df_nuevos = pd.DataFrame(transacciones)

        df_mov = pd.concat([df_mov, df_nuevos], ignore_index=True)

        # guardar cambios
        data["movimientos"] = df_mov

        st.success("✅ Partido liquidado correctamente")

        st.rerun()