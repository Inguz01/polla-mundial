import streamlit as st
import pandas as pd

from utils.validaciones import apuesta_abierta, validar_marcador
from utils.saldos import saldo_usuario
from database.google_sheets import connect
from utils.helpers import generar_id
from utils.data_loader import cargar_todo


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

    df_equipos = data["equipos"].copy()

    mapa_codigos = dict(
        zip(
            df_equipos["equipo"].str.strip(),
            df_equipos["codigo"].str.strip()
        )
    )

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

    fechas = sorted(df_partidos["fecha"].unique())
    fecha_sel = st.selectbox("Seleccione fecha", fechas)
    df_partidos = df_partidos[df_partidos["fecha"] == fecha_sel]

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

        codigo_local = mapa_codigos.get(row["equipo_local"].strip(), "xx")
        codigo_visit = mapa_codigos.get(row["equipo_visitante"].strip(), "xx")

        with st.container(border=True):

            # ── Fecha y hora ──────────────────────────
            c_fecha, c_hora = st.columns(2)
            with c_fecha:
                st.caption(f"📅 {row['fecha']}")
            with c_hora:
                st.caption(f"⏰ {row['hora']}")

            # ── Estado ───────────────────────────────
            if abierto:
                st.success("🟢 Apuestas abiertas")
            else:
                st.error("🔒 Partido iniciado")

            # ── Participar ───────────────────────────
            participa = st.checkbox(
                "Participar",
                key=key_check,
                disabled=not abierto
            )

            # ── MARCADOR ─────────────────────────────
            #
            #  🇩🇪  Alemania        [ 2 ]
            #  🇨🇼  Curazao         [ 0 ]
            #
            # text_input: campo libre, sin botones +/-, el usuario
            # escribe el número directamente. Simple y funciona igual
            # en web y mobile.

            c_info_l, c_num_l = st.columns([3, 1])

            with c_info_l:
                st.markdown(
                    f"""
                    <div style="display:flex; align-items:center;
                                gap:8px; padding-top:8px;">
                        <img src="https://flagcdn.com/w40/{codigo_local}.png"
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
                    disabled=(not participa or not abierto),
                    label_visibility="collapsed",
                    max_chars=2
                )

            c_info_v, c_num_v = st.columns([3, 1])

            with c_info_v:
                st.markdown(
                    f"""
                    <div style="display:flex; align-items:center;
                                gap:8px; padding-top:8px;">
                        <img src="https://flagcdn.com/w40/{codigo_visit}.png"
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
                    disabled=(not participa or not abierto),
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
                pred_sheet.delete_rows(fila_existente)
                eliminados += 1

        if nuevas_predicciones:
            pred_sheet.append_rows(nuevas_predicciones, value_input_option="USER_ENTERED")

        for rango, valores in rows_a_actualizar:
            pred_sheet.update(rango, valores)

        cargar_todo.clear()

        mensajes = []
        if guardados  > 0: mensajes.append(f"{guardados} guardadas")
        if eliminados > 0: mensajes.append(f"{eliminados} eliminadas")

        if mensajes:
            st.success(" / ".join(mensajes))
        else:
            st.info("Sin cambios")