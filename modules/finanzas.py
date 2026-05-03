import streamlit as st
import pandas as pd

from utils.data_loader import cargar_todo
from utils.config import valor_apuesta_por_fase, porcentaje_admin


def finanzas_page():

    # 🔒 solo admin
    if st.session_state.get("rol") != "admin":
        st.error("No tienes permisos")
        st.stop()

    st.title("Panel financiero")

    data = cargar_todo()

    df_pred = data["predicciones"].copy()
    df_part = data["partidos"].copy()
    df_mov = data["movimientos"].copy()

    if len(df_pred) == 0:
        st.info("Aún no hay datos")
        return

    # =========================
    # 💰 TOTAL RECAUDADO
    # =========================

    df_pred = df_pred.merge(
        df_part[["id", "fase"]],
        left_on="partido_id",
        right_on="id",
        how="left"
    )

    df_pred["valor"] = df_pred["fase"].apply(valor_apuesta_por_fase)

    total_recaudado = df_pred["valor"].sum()

    # =========================
    # 🧾 COMISIÓN
    # =========================

    comision = total_recaudado * porcentaje_admin()

    # =========================
    # 💸 PAGOS REALIZADOS
    # =========================

    pagos = df_mov[df_mov["tipo"] == "premio"]["monto"].sum()

    # =========================
    # 🔁 REVERSOS
    # =========================

    reversos = df_mov[df_mov["tipo"] == "reverso_premio"]["monto"].sum()

    total_pagado = pagos + reversos  # reversos son negativos

    # =========================
    # 💰 JACKPOT
    # =========================

    jackpot = total_recaudado - comision - total_pagado

    # =========================
    # 📊 DISPLAY
    # =========================

    c1, c2 = st.columns(2)

    c1.metric("Total recaudado", f"${total_recaudado:,.0f}")
    c2.metric("Comisión", f"${comision:,.0f}")

    c3, c4 = st.columns(2)

    c3.metric("Total pagado", f"${total_pagado:,.0f}")
    c4.metric("Jackpot actual", f"${jackpot:,.0f}")

    st.divider()

    # =========================
    # 📋 DETALLE
    # =========================

    st.subheader("Movimientos")

    st.dataframe(df_mov.sort_values(by="id", ascending=False), use_container_width=True)