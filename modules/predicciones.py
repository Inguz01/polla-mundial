import streamlit as st
import pandas as pd
from utils.validaciones import apuesta_abierta, validar_marcador
from utils.saldos import saldo_usuario
from utils.flags import bandera as url_bandera
from database.google_sheets import connect
from utils.helpers import generar_id
from utils.data_loader import cargar_todo
from utils.config import (
    valor_apuesta_por_fase,
    porcentaje_admin
)


def safe_int(value):
    if value is None:
        return 0
    try:
        return int(float(value))
    except:
        return 0


def predicciones_page():

    st.title("Registrar predicciones")

    st.markdown("""
    <style>
    /* Campo de goles: centrado, grande, sin decoraciones */
    div[data-testid="stTextInput"] input {
        text-align: center !important;
        font-size: 22px !important;
        font-weight: 700 !important;
    }
    </style>
    """, unsafe_allow_html=True)

    usuario_actual = st.session_state.get("usuario")

    if not usuario_actual:
        st.error("Sesión no válida")
        st.stop()

    data = cargar_todo()

    df_partidos = data["partidos"].copy()
    df_partidos = df_partidos[df_partidos["estado"] == "programado"]

    df_pred = data["predicciones"].copy()

    saldo = saldo_usuario(usuario_actual)

    if saldo < 0:
        st.error(f"Saldo: ${saldo:,.0f}")
    else:
        st.success(f"Saldo: ${saldo:,.0f}")

    if len(df_partidos) == 0:
        st.warning("No hay partidos disponibles")
        return

    if len(df_pred) > 0:
        df_pred = df_pred[df_pred["usuario_id"] == usuario_actual]
    else:
        df_pred = pd.DataFrame(columns=[
            "usuario_id", "partido_id", "goles_local", "goles_visitante"
        ])

    # =========================
    # TIMEZONE
    # =========================

    #tz = pytz.timezone("America/Bogota")

    TZ = "America/Bogota"
    # tz_convert(None) produce un timestamp naive en hora Bogotá
    #ahora = pd.Timestamp.now(tz).tz_convert(None)

    ahora = pd.Timestamp.now(tz=TZ)

    # =========================
    # FECHA COMPLETA PARTIDO
    # =========================

    #df_partidos["fecha_hora"] = pd.to_datetime(
     #   df_partidos["fecha"].astype(str) + " " +
      #  df_partidos["hora"].astype(str),
       # errors="coerce"
    #)

    # forzar naive en todos los registros para evitar TypeError en la comparación
    #df_partidos["fecha_hora"] = df_partidos["fecha_hora"].dt.tz_localize(None)

    df_partidos["fecha_hora"] = pd.to_datetime(
        df_partidos["fecha"].astype(str) + " " +
        df_partidos["hora"].astype(str),
        errors="coerce"
    )

    # asignar timezone Bogotá
    df_partidos["fecha_hora"] = (
        df_partidos["fecha_hora"]
        .dt.tz_localize(TZ)
    )

    df_partidos["horas_restantes"] = (
    df_partidos["fecha_hora"] - ahora
    ).dt.total_seconds() / 3600

    # =========================
    # SOLO PARTIDOS FUTUROS
    # =========================

    df_partidos = df_partidos[
        df_partidos["fecha_hora"] > ahora
    ].copy()

    # =========================
    # VALIDAR DISPONIBLES
    # =========================

    if len(df_partidos) == 0:

        st.warning("No hay partidos disponibles")

        return

    # =========================
    # FECHAS DISPONIBLES
    # =========================

    fechas_disponibles = sorted(
        df_partidos["fecha"].unique()
    )

    # =========================
    # PRÓXIMA FECHA
    # =========================

    proxima_fecha = fechas_disponibles[0]

    # =========================
    # CALENDARIO
    # =========================

    st.info(
    "⏳ Los pronósticos se habilitan únicamente "
    "24 horas antes del inicio de cada partido."
    )
    
    fecha_sel = st.date_input(
        "📅 Selecciona una fecha",
        value=pd.to_datetime(proxima_fecha).date(),
        min_value=pd.to_datetime(proxima_fecha).date(),
        max_value=pd.to_datetime(
            max(fechas_disponibles)
        ).date()
    )

    # =========================
    # FILTRAR FECHA
    # =========================

    df_partidos = df_partidos[
        pd.to_datetime(df_partidos["fecha"]).dt.date == fecha_sel
    ]
    st.write("Seleccione los partidos en los que desea participar")

    resultados = []

    for _, row in df_partidos.iterrows():

        key_check = f"check_{row['id']}"
        key_local = f"local_{row['id']}"
        key_visit = f"visit_{row['id']}"

        pred_existente = df_pred[
            df_pred["partido_id"].astype(str) == str(row["id"])
        ]

        if len(pred_existente) > 0:
            participa_default   = True
            goles_local_default = str(safe_int(pred_existente.iloc[0]["goles_local"]))
            goles_visit_default = str(safe_int(pred_existente.iloc[0]["goles_visitante"]))
        else:
            participa_default   = False
            goles_local_default = "0"
            goles_visit_default = "0"

        if key_check not in st.session_state:
            st.session_state[key_check] = participa_default
        if key_local not in st.session_state:
            st.session_state[key_local] = goles_local_default
        if key_visit not in st.session_state:
            st.session_state[key_visit] = goles_visit_default

        abierto = apuesta_abierta(
            row["fecha"],
            row["hora"],
            row.get("estado", "programado")
        )

        horas_restantes = row["horas_restantes"]

        habilitado_24h = horas_restantes <= 24

        puede_apostar = abierto and habilitado_24h


        codigo_local = url_bandera(row["equipo_local"])
        codigo_visit = url_bandera(row["equipo_visitante"])

        with st.container(border=True):

            # ── Fecha y hora ──────────────────────────
            c_fecha, c_hora = st.columns(2)
            with c_fecha:
                st.caption(f"📅 {row['fecha']}")
            with c_hora:
                st.caption(f"⏰ {row['hora']}")

            

            # ── MINI PANEL DEL PARTIDO ─────────────────────

            predicciones_partido = data["predicciones"].copy()

            if not predicciones_partido.empty and "partido_id" in predicciones_partido.columns:

                predicciones_partido = predicciones_partido[
                    predicciones_partido["partido_id"].astype(str)
                    == str(row["id"])
                ]

            else:

                predicciones_partido = pd.DataFrame()

            participantes = 0

            if not predicciones_partido.empty:

                if "participa" in predicciones_partido.columns:

                    participantes = predicciones_partido[
                        predicciones_partido["participa"].astype(str) == "1"
                    ]["usuario_id"].nunique()

                elif "usuario_id" in predicciones_partido.columns:

                    participantes = predicciones_partido[
                        "usuario_id"
                    ].nunique()

            valor_apuesta = valor_apuesta_por_fase(
                row["fase"]
            )

            pozo_total = participantes * valor_apuesta

            premio_estimado = pozo_total * (1 - porcentaje_admin())

            if participantes > 0:

                col1, col2, col3 = st.columns(3)

                with col1:
                    st.metric(
                        "👥 Participantes",
                        participantes
                    )

                with col2:
                    st.metric(
                        "💰 Pozo",
                        f"${pozo_total:,.0f}"
                    )

                with col3:
                    st.metric(
                        "🏆 Premio Est.",
                        f"${premio_estimado:,.0f}"
                    )

            st.caption(
                f"Comisión administrativa: "
                f"{porcentaje_admin()*100:.0f}%"
            )

            # ── Estado ───────────────────────────────

            if not abierto:

                st.error("🔒 Partido iniciado")

            elif puede_apostar:

                st.success("🟢 Pronósticos habilitados")

            else:

                tiempo_restante = row["fecha_hora"] - ahora

                dias = tiempo_restante.days
                horas = tiempo_restante.seconds // 3600
                minutos = (tiempo_restante.seconds % 3600) // 60

                if dias > 0:

                    st.warning(
                        f"⏳ Pronósticos disponibles en "
                        f"{dias}d {horas}h"
                    )

                else:

                    st.warning(
                        f"⏳ Pronósticos disponibles en "
                        f"{horas}h {minutos}m"
                    )

            # ── Participar ───────────────────────────
            participa = st.checkbox(
                "Participar",
                key=key_check,
                disabled=not puede_apostar
            )

            # ── MARCADOR ─────────────────────────────


            c_info_l, c_num_l = st.columns([3, 1])

            with c_info_l:
                st.markdown(
                    f"""
                    <div style="display:flex; align-items:center;
                                gap:8px; padding-top:8px;">
                        <img src="{codigo_local}"
                             style="width:26px; border-radius:2px; flex-shrink:0;">
                        <span style="font-size:15px; font-weight:600;">
                            {row['equipo_local']}
                        </span>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

            with c_num_l:
                val_local = st.text_input(
                    "Local",
                    key=key_local,
                    disabled=(not participa or not puede_apostar),
                    label_visibility="collapsed",
                    max_chars=2
                )

            c_info_v, c_num_v = st.columns([3, 1])

            with c_info_v:
                st.markdown(
                    f"""
                    <div style="display:flex; align-items:center;
                                gap:8px; padding-top:8px;">
                        <img src="{codigo_visit}"
                             style="width:26px; border-radius:2px; flex-shrink:0;">
                        <span style="font-size:15px; font-weight:600;">
                            {row['equipo_visitante']}
                        </span>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

            with c_num_v:
                val_visit = st.text_input(
                    "Visitante",
                    key=key_visit,
                    disabled=(not participa or not puede_apostar),
                    label_visibility="collapsed",
                    max_chars=2
                )

            resultados.append({
                "partido_id":      row["id"],
                "participa":       participa,
                "goles_local":     val_local,
                "goles_visitante": val_visit,
                "abierto":         abierto
            })

            st.markdown("<br>", unsafe_allow_html=True)

    st.divider()

    if st.button("Guardar predicciones"):

        # ── Validar que todos los campos sean números válidos ──
        for r in resultados:
            if not r["abierto"] or not r["participa"]:
                continue
            for campo in [r["goles_local"], r["goles_visitante"]]:
                if not campo.strip().isdigit():
                    st.error("Solo se permiten números enteros en los marcadores")
                    st.stop()
            gl = int(r["goles_local"].strip())
            gv = int(r["goles_visitante"].strip())
            if not validar_marcador(gl, gv):
                st.error("No puedes ingresar un marcador mayor a 20")
                st.stop()

        db = connect()
        pred_sheet = db.worksheet("predicciones")
        predicciones_existentes = pred_sheet.get_all_records()

        nuevas_predicciones = []
        rows_a_actualizar   = []
        filas_a_borrar      = []
        guardados  = 0
        eliminados = 0

        for r in resultados:

            if not r["abierto"]:
                continue

            partido_df = df_partidos[df_partidos["id"] == r["partido_id"]]
            if len(partido_df) == 0:
                continue

            fila_existente = None
            for i, p in enumerate(predicciones_existentes):
                if (str(p.get("usuario_id", "")) == str(usuario_actual)
                        and str(p.get("partido_id", "")) == str(r["partido_id"])):
                    fila_existente = i + 2
                    break

            if r["participa"]:
                gl = int(r["goles_local"].strip())
                gv = int(r["goles_visitante"].strip())

                if fila_existente:
                    rows_a_actualizar.append((
                        f"D{fila_existente}:G{fila_existente}",
                        [[gl, gv, 1, 0]]
                    ))
                else:
                    nuevas_predicciones.append([
                        generar_id(),
                        usuario_actual,
                        r["partido_id"],
                        gl,
                        gv,
                        1,
                        0
                    ])
                guardados += 1

            elif fila_existente:
                # recolectar filas a borrar en lugar de borrar inmediatamente
                filas_a_borrar.append(fila_existente)
                eliminados += 1

        if nuevas_predicciones:
            pred_sheet.append_rows(nuevas_predicciones, value_input_option="USER_ENTERED")

        for rango, valores in rows_a_actualizar:
            pred_sheet.update(rango, valores)

        # borrar de mayor a menor para que el desplazamiento no afecte las filas pendientes
        for fila in sorted(filas_a_borrar, reverse=True):
            pred_sheet.delete_rows(fila)

        cargar_todo.clear()

        mensajes = []
        if guardados  > 0: mensajes.append(f"{guardados} guardadas")
        if eliminados > 0: mensajes.append(f"{eliminados} eliminadas")

        if mensajes:
            st.success(" / ".join(mensajes))
        else:
            st.info("Sin cambios")