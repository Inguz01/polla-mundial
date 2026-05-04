import streamlit as st
import pandas as pd

from utils.data_loader import cargar_todo
from utils.dataframe_utils import safe_int
from utils.config import valor_apuesta_por_fase, porcentaje_admin
from utils.movimientos import registrar_movimientos
from database.google_sheets import connect


def resultados_partido_page():

    st.title("Resultados por partido")

    data = cargar_todo()

    df_pred = data["predicciones"].copy()
    df_res  = data["resultados"].copy()
    df_part = data["partidos"].copy()
    df_mov  = data["movimientos"].copy()

    if len(df_res) == 0:
        st.info("Aún no hay resultados registrados")
        return

    # =========================
    # LIMPIEZA
    # =========================

    df_res["goles_local"]     = df_res["goles_local"].apply(safe_int)
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

    partido_id  = str(row_partido["partido_id"])
    fase        = row_partido["fase"]
    real_local  = row_partido["goles_local"]
    real_visit  = row_partido["goles_visitante"]

    # =========================
    # RESULTADO
    # =========================

    st.subheader(partido_sel)
    st.write(f"Resultado real: **{real_local} - {real_visit}**")

    # =========================
    # APUESTAS DEL PARTIDO
    # =========================

    df_pred_part = df_pred[
        df_pred["partido_id"].astype(str) == partido_id
    ].copy()

    participantes = len(df_pred_part)

    if participantes == 0:
        st.warning("No hubo participantes en este partido")
        return

    # =========================
    # POZO  (solo sobre los que apostaron ESTE partido)
    # =========================

    valor = valor_apuesta_por_fase(fase)

    # Fallback de seguridad: si config devuelve 0, usar 5000
    if valor <= 0:
        valor = 5000
        st.warning(f"⚠️ No se encontró valor para fase '{fase}' en config. Usando $5.000 por defecto.")

    pozo_bruto = participantes * valor
    comision   = round(pozo_bruto * porcentaje_admin(), 2)
    pozo       = round(pozo_bruto - comision, 2)

    st.divider()
    st.write(f"Participantes: **{participantes}**")
    st.write(f"Valor apuesta: **${valor:,.0f}**")
    st.write(f"Pozo bruto: **${pozo_bruto:,.0f}**")
    st.write(f"Comisión (10 %): **${comision:,.0f}**")
    st.write(f"Pozo a repartir: **${pozo:,.0f}**")

    # =========================
    # GANADORES  — comparar columnas numéricas, no string
    # =========================

    df_pred_part["goles_local"]     = df_pred_part["goles_local"].apply(safe_int)
    df_pred_part["goles_visitante"] = df_pred_part["goles_visitante"].apply(safe_int)

    ganadores = df_pred_part[
        (df_pred_part["goles_local"]     == real_local) &
        (df_pred_part["goles_visitante"] == real_visit)
    ]

    st.divider()

    if len(ganadores) > 0:
        premio = round(pozo / len(ganadores), 2)
        st.success(f"✅ {len(ganadores)} ganador(es) — premio: **${premio:,.0f}** c/u")
        tabla = ganadores[["usuario_id"]].copy()
        tabla["premio"] = f"${premio:,.0f}"
        st.dataframe(tabla, use_container_width=True)
    else:
        st.warning("Sin ganadores — el pozo va al jackpot")
        st.info(f"💰 ${pozo:,.0f} se acumula al jackpot")

    # =========================
    # JACKPOT ACTUAL
    # =========================

    if "tipo" in df_mov.columns and len(df_mov) > 0:
        df_mov["monto"] = pd.to_numeric(df_mov["monto"], errors="coerce").fillna(0)
        jackpot_actual = (
            df_mov[df_mov["tipo"] == "jackpot_aporte"]["monto"].sum()
            - df_mov[df_mov["tipo"] == "jackpot_pago"]["monto"].sum()
        )
    else:
        jackpot_actual = 0

    st.info(f"Jackpot acumulado: **${jackpot_actual:,.0f}**")

    # =========================
    # ESTADO: leer de la hoja partidos (fuente de verdad)
    # =========================

    df_mov["monto"] = pd.to_numeric(df_mov["monto"], errors="coerce").fillna(0)

    estado_partido = df_part[
        df_part["id"].astype(str) == partido_id
    ]["estado"].values

    ya_liquidado = len(estado_partido) > 0 and str(estado_partido[0]).strip() == "liquidado"

    st.divider()

    if ya_liquidado:
        st.success("Este partido ya fue liquidado")
        if "referencia" in df_mov.columns:
            premios = df_mov[
                (df_mov["referencia"].astype(str) == f"partido_{partido_id}") &
                (df_mov["tipo"] == "premio")
            ]
            if not premios.empty:
                st.dataframe(premios[["usuario_id", "monto"]], use_container_width=True)
        return

    if st.button("Liquidar partido"):
        _liquidar(partido_id, ganadores, pozo, comision, jackpot_actual)


# =============================================================
# HELPERS
# =============================================================

def _liquidar(partido_id, ganadores, pozo, comision, jackpot_actual):
    """Registra todos los movimientos de la liquidacion en una sola llamada a Sheets."""

    ref = f"partido_{partido_id}"
    movimientos = []

    # 1. Comision (siempre)
    movimientos.append({"usuario_id": "admin", "tipo": "comision", "referencia": ref, "monto": comision})

    # 2. Premios o aporte jackpot
    if len(ganadores) > 0:
        premio_por_usuario = round(pozo / len(ganadores), 2)
        for _, g in ganadores.iterrows():
            movimientos.append({"usuario_id": g["usuario_id"], "tipo": "premio", "referencia": ref, "monto": premio_por_usuario})
        if jackpot_actual > 0:
            extra = round(jackpot_actual / len(ganadores), 2)
            for _, g in ganadores.iterrows():
                movimientos.append({"usuario_id": g["usuario_id"], "tipo": "jackpot_pago", "referencia": ref, "monto": extra})
    else:
        movimientos.append({"usuario_id": "sistema", "tipo": "jackpot_aporte", "referencia": ref, "monto": pozo})

    # Escribir todo de una vez — evita fallos parciales por rate limit
    registrar_movimientos(movimientos)

    # 3. Marcar partido como liquidado en Sheets
    # Esto impide que los usuarios puedan seguir editando su prediccion
    try:
        db = connect()
        sheet_partidos = db.worksheet("partidos")
        headers = sheet_partidos.row_values(1)
        if "estado" in headers:
            col_estado = headers.index("estado") + 1
            celdas = sheet_partidos.col_values(1)  # columna id
            for i, val in enumerate(celdas):
                if str(val) == str(partido_id):
                    sheet_partidos.update_cell(i + 1, col_estado, "liquidado")
                    break
    except Exception as e:
        st.warning(f"Advertencia: no se pudo actualizar el estado del partido en Sheets: {e}")

    cargar_todo.clear()
    st.success("Partido liquidado correctamente")
    st.rerun()