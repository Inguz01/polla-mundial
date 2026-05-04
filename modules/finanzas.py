import streamlit as st
import pandas as pd

from utils.data_loader import cargar_todo


def finanzas_page():

    # 🔒 solo admin
    if st.session_state.get("rol") != "admin":
        st.error("No tienes permisos")
        st.stop()

    st.title("Panel financiero")

    data = cargar_todo()

    df_mov = data["movimientos"].copy()

    if len(df_mov) == 0:
        st.info("Aún no hay movimientos")
        return

    # =========================
    # LIMPIEZA
    # =========================

    df_mov["monto"] = pd.to_numeric(df_mov["monto"], errors="coerce").fillna(0)

    # =========================
    # 💰 TOTAL RECAUDADO REAL
    # =========================

    total_recaudado = df_mov[df_mov["tipo"] == "apuesta"]["monto"].abs().sum()

    # =========================
    # 🧾 COMISIÓN REAL
    # =========================

    comision = df_mov[df_mov["tipo"] == "comision"]["monto"].sum()

    # =========================
    # 💸 PAGOS REALES
    # =========================

    pagos = df_mov[df_mov["tipo"] == "premio"]["monto"].sum()

    jackpot_pagado = df_mov[df_mov["tipo"] == "jackpot_pago"]["monto"].sum()

    total_pagado = pagos + jackpot_pagado

    # =========================
    # 💰 JACKPOT REAL
    # =========================

    jackpot_aporte = df_mov[df_mov["tipo"] == "jackpot_aporte"]["monto"].sum()

    jackpot = jackpot_aporte - jackpot_pagado

    # =========================
    # 📊 SALDO DE USUARIOS (CLAVE)
    # =========================

    saldo_usuarios = (
        df_mov.groupby("usuario")["monto"]
        .sum()
        .sort_values(ascending=True)
        .reset_index()
    )

    # separar deuda vs saldo
    saldo_usuarios["estado"] = saldo_usuarios["monto"].apply(
        lambda x: "Deuda" if x < 0 else "A favor"
    )

    # =========================
    # 📊 DISPLAY
    # =========================

    c1, c2 = st.columns(2)

    c1.metric("Total recaudado", f"${total_recaudado:,.0f}")
    c2.metric("Comisión (casa)", f"${comision:,.0f}")

    c3, c4 = st.columns(2)

    c3.metric("Total pagado", f"${total_pagado:,.0f}")
    c4.metric("Jackpot actual", f"${jackpot:,.0f}")

    st.divider()

    # =========================
    # 💳 CUENTA CORRIENTE
    # =========================

    st.subheader("Saldo por usuario")

    st.dataframe(saldo_usuarios, use_container_width=True)

    # =========================
    # 📋 MOVIMIENTOS
    # =========================

    st.subheader("Movimientos")

    st.dataframe(
        df_mov.sort_values(by="partido_id", ascending=False),
        use_container_width=True
    )