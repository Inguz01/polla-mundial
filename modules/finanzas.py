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

    df_mov = data.get("movimientos", pd.DataFrame()).copy()

    # =========================
    # NORMALIZAR MOVIMIENTOS
    # =========================

    if df_mov is None or df_mov.empty:
        df_mov = pd.DataFrame(columns=[
            "usuario_id", "tipo", "referencia", "monto", "partido_id"
        ])

    if "usuario_id" not in df_mov.columns and "usuario" in df_mov.columns:
        df_mov["usuario_id"] = df_mov["usuario"]

    for col in ["usuario_id", "tipo", "monto", "partido_id", "referencia"]:
        if col not in df_mov.columns:
            df_mov[col] = None

    df_mov["usuario_id"] = df_mov["usuario_id"].astype(str)
    df_mov["monto"]      = pd.to_numeric(df_mov["monto"], errors="coerce").fillna(0)

    # =========================
    # MÉTRICAS DEL TORNEO
    # Se calculan directamente desde movimientos, sin depender
    # del campo "estado" de la hoja partidos (que nunca se actualiza)
    # Un partido está liquidado si tiene al menos un movimiento tipo "comision"
    # =========================

    # Referencias de partidos que ya tienen comisión registrada = liquidados
    refs_liquidadas = df_mov[
        df_mov["tipo"] == "comision"
    ]["referencia"].unique().tolist()

    df_liq = df_mov[df_mov["referencia"].isin(refs_liquidadas)]

    # Recaudado: apuestas de partidos liquidados (valor absoluto porque son negativos)
    total_recaudado = df_liq[
        df_liq["tipo"] == "apuesta"
    ]["monto"].abs().sum()

    # Comisión cobrada por la casa
    comision = df_liq[
        df_liq["tipo"] == "comision"
    ]["monto"].sum()

    # Premios pagados a usuarios
    premios_pagados = df_liq[
        df_liq["tipo"] == "premio"
    ]["monto"].sum()

    jackpot_pagado = df_mov[
        df_mov["tipo"] == "jackpot_pago"
    ]["monto"].sum()

    total_pagado = premios_pagados + jackpot_pagado

    # Jackpot acumulado (aportes - pagos, sobre todos los movimientos)
    jackpot_actual = (
        df_mov[df_mov["tipo"] == "jackpot_aporte"]["monto"].sum()
        - jackpot_pagado
    )

    # =========================
    # MÉTRICAS DISPLAY
    # =========================

    c1, c2 = st.columns(2)
    c1.metric("Total recaudado (liquidado)", f"${total_recaudado:,.0f}")
    c2.metric("Comisión (casa)", f"${comision:,.0f}")

    c3, c4 = st.columns(2)
    c3.metric("Premios pagados", f"${total_pagado:,.0f}")
    c4.metric("Jackpot acumulado", f"${jackpot_actual:,.0f}")

    st.divider()

    # =========================
    # CUENTA CORRIENTE DE USUARIOS
    # La cuenta corriente usa TODOS los movimientos (incluyendo apuestas futuras)
    # Negativo = el usuario nos debe  |  Positivo = le debemos al usuario
    # =========================

    st.subheader("Cuenta corriente por usuario")

    tipos_usuario = ["apuesta", "reverso_apuesta", "premio", "jackpot_pago", "pago", "retiro", "ajuste"]

    df_usuarios = df_mov[df_mov["tipo"].isin(tipos_usuario)]

    if not df_usuarios.empty:
        saldo_usuarios = (
            df_usuarios
            .groupby("usuario_id")["monto"]
            .sum()
            .reset_index()
            .rename(columns={"monto": "saldo"})
            .sort_values("saldo")
        )
        saldo_usuarios["estado"] = saldo_usuarios["saldo"].apply(
            lambda x: "🔴 Debe" if x < 0 else "🟢 A favor"
        )
        st.dataframe(saldo_usuarios, use_container_width=True)
    else:
        st.info("No hay movimientos de usuarios aún")

    st.divider()

    # =========================
    # DETALLE DE MOVIMIENTOS
    # =========================

    st.subheader("Todos los movimientos")

    col_mostrar = [c for c in ["fecha", "usuario_id", "tipo", "referencia", "monto"]
                   if c in df_mov.columns]

    st.dataframe(
        df_mov[col_mostrar].sort_values(
            by="fecha" if "fecha" in df_mov.columns else col_mostrar[0],
            ascending=False
        ),
        use_container_width=True
    )

def reversar_partido(df_mov, partido_id):

    df_partido = df_mov[
        df_mov["referencia"] == f"partido_{partido_id}"
    ]

    transacciones = []

    for _, mov in df_partido.iterrows():

        transacciones.append({
            "usuario_id": mov["usuario_id"],
            "tipo": "reverso",
            "referencia": f"reverso_partido_{partido_id}",
            "monto": -float(mov["monto"])
        })

    return transacciones