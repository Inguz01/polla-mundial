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

    # ========= CARGA CENTRALIZADA =========

    usuario_actual = st.session_state.get("usuario")

    if not usuario_actual:
        st.error("Sesión no válida")
        st.stop()
        
    data = cargar_todo()

    df_partidos = data["partidos"].copy()

    df_partidos = df_partidos[
    df_partidos["estado"] == "programado"
]

    df_pred = data["predicciones"].copy()

    df_equipos = data["equipos"].copy()

    mapa_codigos = dict(
        zip(
            df_equipos["equipo"].str.strip(),
            df_equipos["codigo"].str.strip()
        )
    )

    # ======================================


    saldo = saldo_usuario(usuario_actual)

    if saldo < 0:

        st.error(f"Saldo: ${saldo:,.0f}")

    else:

        st.success(f"Saldo: ${saldo:,.0f}")


    if len(df_partidos) == 0:

        st.warning("No hay partidos disponibles")

        return


    # predicciones del usuario

    if len(df_pred) > 0:

        df_pred = df_pred[

            df_pred["usuario_id"] == usuario_actual

        ]

    else:

        df_pred = pd.DataFrame(columns=[

            "usuario_id",
            "partido_id",
            "goles_local",
            "goles_visitante"

        ])


    fechas = sorted(df_partidos["fecha"].unique())


    fecha_sel = st.selectbox(

        "Seleccione fecha",

        fechas

    )


    df_partidos = df_partidos[

        df_partidos["fecha"] == fecha_sel

    ]


    st.write("Seleccione los partidos en los que desea participar")


    resultados = []


    for _, row in df_partidos.iterrows():

        key_check = f"check_{row['id']}"
        key_local = f"local_{row['id']}"
        key_visit = f"visit_{row['id']}"

        pred_existente = df_pred[
            df_pred["partido_id"].astype(str)
            == str(row["id"])
        ]

        if len(pred_existente) > 0:

            participa_default = True

            goles_local_default = safe_int(
                pred_existente.iloc[0]["goles_local"]
            )

            goles_visit_default = safe_int(
                pred_existente.iloc[0]["goles_visitante"]
            )

        else:

            participa_default = False
            goles_local_default = 0
            goles_visit_default = 0

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

        codigo_local = mapa_codigos.get(
            row["equipo_local"].strip(),
            "xx"
        )

        codigo_visit = mapa_codigos.get(
            row["equipo_visitante"].strip(),
            "xx"
        )

        with st.container(border=True):

            # =========================
            # PARTIDO
            # =========================

            st.markdown(
                f"""
                ### ⚽ {row['equipo_local']} vs {row['equipo_visitante']}
                """
            )

            # =========================
            # FECHA Y HORA
            # =========================

            c_fecha, c_hora = st.columns(2)

            with c_fecha:
                st.caption(f"📅 {row['fecha']}")

            with c_hora:
                st.caption(f"⏰ {row['hora']}")

            # =========================
            # ESTADO
            # =========================

            if abierto:
                st.success("🟢 Apuestas abiertas")
            else:
                st.error("🔒 Partido iniciado")

            # =========================
            # PARTICIPAR
            # =========================

            participa = st.checkbox(
                "Participar",
                key=key_check,
                disabled=not abierto
            )

            # =========================
            # MARCADOR
            # =========================

            c1, c2, c3 = st.columns(
                [3,1,3],
                vertical_alignment="center"
            )

            # =========================
            # LOCAL
            # =========================

            with c1:

                cc1, cc2 = st.columns([1,2])

                with cc1:

                    st.image(
                        f"https://flagcdn.com/w40/{codigo_local}.png",
                        width=28
                    )

                with cc2:

                    goles_local = st.number_input(
                        "",
                        min_value=0,
                        max_value=20,
                        step=1,
                        format="%d",
                        key=key_local,
                        disabled=(not participa or not abierto),
                        label_visibility="collapsed"
                    )

            # =========================
            # VS
            # =========================

            with c2:

                st.markdown(
                    """
                    <div style='text-align:center;
                                font-size:18px;
                                font-weight:700;
                                padding-top:8px'>
                        VS
                    </div>
                    """,
                    unsafe_allow_html=True
                )

            # =========================
            # VISITANTE
            # =========================

            with c3:

                cc3, cc4 = st.columns([2,1])

                with cc3:

                    goles_visitante = st.number_input(
                        "",
                        min_value=0,
                        max_value=20,
                        step=1,
                        format="%d",
                        key=key_visit,
                        disabled=(not participa or not abierto),
                        label_visibility="collapsed"
                    )

                with cc4:

                    st.image(
                        f"https://flagcdn.com/w40/{codigo_visit}.png",
                        width=28
                    )

            resultados.append({

                "partido_id": row["id"],
                "participa": participa,
                "goles_local": goles_local,
                "goles_visitante": goles_visitante,
                "abierto": abierto

            })

            st.markdown("<br>", unsafe_allow_html=True)


    st.divider()


    if st.button("Guardar predicciones"):

        db = connect()
        pred_sheet = db.worksheet("predicciones")
        predicciones_existentes = pred_sheet.get_all_records()

        # Acumular todas las filas nuevas de predicciones y movimientos
        nuevas_predicciones = []
        rows_a_actualizar   = []  # (rango, valores) para predicciones existentes

        guardados = 0
        eliminados = 0

        for r in resultados:

            if not r["abierto"]:
                continue

            if r["participa"]:
                if not validar_marcador(r["goles_local"], r["goles_visitante"]):
                    st.error("Marcador invalido")
                    st.stop()

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

                if fila_existente:
                    # Actualizar marcador existente (no genera nuevo movimiento)
                    rows_a_actualizar.append((
                        f"D{fila_existente}:G{fila_existente}",
                        [[int(r["goles_local"]), int(r["goles_visitante"]), 1, 0]]
                    ))
                else:
                    # Nueva prediccion
                    nuevas_predicciones.append([
                        generar_id(),
                        usuario_actual,
                        r["partido_id"],
                        int(r["goles_local"]),
                        int(r["goles_visitante"]),
                        1,
                        0
                    ])

                guardados += 1

            elif fila_existente:
                pred_sheet.delete_rows(fila_existente)
                eliminados += 1

        # ── Escribir todo en batch ──────────────────────────────

        # 1. Nuevas predicciones en una sola llamada
        if nuevas_predicciones:
            pred_sheet.append_rows(nuevas_predicciones, value_input_option="USER_ENTERED")

        # 2. Actualizaciones de marcadores (una llamada por fila, pero solo si cambio)
        for rango, valores in rows_a_actualizar:
            pred_sheet.update(rango, valores)

        cargar_todo.clear()

        mensajes = []
        if guardados > 0:
            mensajes.append(f"{guardados} guardadas")
        if eliminados > 0:
            mensajes.append(f"{eliminados} eliminadas")

        if mensajes:
            st.success(" / ".join(mensajes))
        else:
            st.info("Sin cambios")