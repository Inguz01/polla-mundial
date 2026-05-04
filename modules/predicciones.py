import streamlit as st
import pandas as pd

from utils.validaciones import apuesta_abierta, validar_marcador
from utils.saldos import saldo_usuario
from database.google_sheets import connect
from utils.helpers import generar_id
from utils.movimientos import registrar_movimiento
from utils.config import valor_apuesta_por_fase
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

        # 🔒 BLOQUEAR ADMIN
    if st.session_state.get("rol") == "admin":
        st.warning("Los administradores no pueden realizar predicciones")
        st.stop()
    
    
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


    h1, h2, h3 = st.columns([1,4,3])

    h1.write("✔")

    h2.write("Partido")

    h3.write("Marcador")

    st.divider()



    for _, row in df_partidos.iterrows():

        col_check, col_partido, col_score = st.columns([1,4,3])


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


        with col_check:

            participa = st.checkbox(

                "",

                key=key_check,

                disabled=not abierto

            )


        with col_partido:

            codigo_local = mapa_codigos.get(row["equipo_local"].strip(), "xx")
            codigo_visit = mapa_codigos.get(row["equipo_visitante"].strip(), "xx")

            col_a, col_b, col_c = st.columns([1,4,1])

            with col_a:
                st.image(f"https://flagcdn.com/w40/{codigo_local}.png", width=30)

            with col_b:
                st.write(f"{row['equipo_local']} vs {row['equipo_visitante']}")

            with col_c:
                st.image(f"https://flagcdn.com/w40/{codigo_visit}.png", width=30)


        with col_score:

            c1, c2, c3 = st.columns([1,0.3,1])


            with c1:

                goles_local = st.number_input(

                    " ",

                    min_value=0,

                    max_value=20,

                    step=1,

                    format="%d",

                    key=key_local,

                    disabled=(not participa or not abierto)

                )


            with c2:

                st.markdown(

                    "<div style='text-align:center;margin-top:8px'>-</div>",

                    unsafe_allow_html=True

                )


            with c3:

                goles_visitante = st.number_input(

                    " ",

                    min_value=0,

                    max_value=20,

                    step=1,

                    format="%d",

                    key=key_visit,

                    disabled=(not participa or not abierto)

                )


        resultados.append({

            "partido_id": row["id"],

            "participa": participa,

            "goles_local": goles_local,

            "goles_visitante": goles_visitante,

            "abierto": abierto

        })


    st.divider()


    if st.button("Guardar predicciones"):

        db = connect()
        pred_sheet = db.worksheet("predicciones")
        predicciones_existentes = pred_sheet.get_all_records()

        # Leer movimientos una sola vez para verificar apuestas ya registradas
        mov_sheet = db.worksheet("movimientos")
        movimientos_existentes = mov_sheet.get_all_records()

        referencias_pagadas = {
            m["referencia"]
            for m in movimientos_existentes
            if str(m.get("usuario_id", "")) == str(usuario_actual)
            and m.get("tipo") == "apuesta"
        }

        # Acumular todas las filas nuevas de predicciones y movimientos
        nuevas_predicciones = []
        nuevos_movimientos  = []
        rows_a_actualizar   = []  # (rango, valores) para predicciones existentes
        rows_a_eliminar     = []  # filas a borrar (reversas)

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

            fase = partido_df.iloc[0]["fase"]

            fila_existente = None
            for i, p in enumerate(predicciones_existentes):
                if (str(p.get("usuario_id", "")) == str(usuario_actual)
                        and str(p.get("partido_id", "")) == str(r["partido_id"])):
                    fila_existente = i + 2
                    break

            ref = f"partido_{r['partido_id']}"

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
                    # Registrar apuesta solo si no existe ya
                    if ref not in referencias_pagadas:
                        nuevos_movimientos.append({
                            "usuario_id": usuario_actual,
                            "tipo": "apuesta",
                            "referencia": ref,
                            "monto": -valor_apuesta_por_fase(fase)
                        })

                guardados += 1

            elif fila_existente:
                rows_a_eliminar.append((fila_existente, fase, ref))
                eliminados += 1

        # ── Escribir todo en batch ──────────────────────────────

        # 1. Nuevas predicciones en una sola llamada
        if nuevas_predicciones:
            pred_sheet.append_rows(nuevas_predicciones, value_input_option="USER_ENTERED")

        # 2. Actualizaciones de marcadores (una llamada por fila, pero solo si cambio)
        for rango, valores in rows_a_actualizar:
            pred_sheet.update(rango, valores)

        # 3. Borrar filas de reversas (de abajo a arriba para no desplazar indices)
        for fila, fase, ref in sorted(rows_a_eliminar, reverse=True):
            pred_sheet.delete_rows(fila)
            nuevos_movimientos.append({
                "usuario_id": usuario_actual,
                "tipo": "reverso_apuesta",
                "referencia": ref,
                "monto": valor_apuesta_por_fase(fase)
            })

        # 4. Todos los movimientos en una sola llamada
        if nuevos_movimientos:
            from utils.movimientos import registrar_movimientos
            registrar_movimientos(nuevos_movimientos)

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