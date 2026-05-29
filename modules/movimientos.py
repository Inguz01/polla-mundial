import streamlit as st
import pandas as pd

from utils.movimientos import registrar_movimiento
from utils.data_loader import cargar_todo



def movimientos_page():

    # 🔒 CONTROL DE PERMISOS
    if st.session_state.get("rol") != "admin":
        st.error("No tienes permisos para acceder a esta sección")
        st.stop()    

    st.title("Movimientos financieros")


    # ===== carga centralizada =====

    data = cargar_todo()

    df = data["movimientos"].copy()

    # ==============================


    # ======================
    # FORMULARIO ADMIN
    # ======================

    st.subheader("Registrar pago o ajuste")


    df_usuarios = data["usuarios"].copy()

    if len(df_usuarios) > 0:

        usuarios = sorted(df_usuarios["usuario_id"].tolist())

    else:

        usuarios = []


    col1, col2 = st.columns(2)


    with col1:

        opciones_usuario = ["— Selecciona un usuario —"] + usuarios

        usuario = st.selectbox(

            "Usuario",

            opciones_usuario

        )

        tipo = st.selectbox(

            "Tipo de movimiento",

            [

                "Recargar cuenta (ingreso)",

                "Retirar dinero (egreso)",

            ]

        )


    with col2:

        monto = st.number_input(

            "Monto",

            min_value=0,

            step=1000

        )

        referencia = st.text_input(

            "Referencia",

            placeholder="ej: nequi, efectivo, transferencia..."

        )


    # ===== guardar movimiento =====

    if st.button("Guardar movimiento"):


        if usuario == "— Selecciona un usuario —":

            st.warning("Selecciona un usuario para registrar el movimiento")

            st.stop()

        if monto == 0:

            st.warning("Ingrese un monto válido")

            st.stop()

        if not referencia.strip():

            st.warning("El campo Referencia es obligatorio (ej: nequi, efectivo, transferencia...)")

            st.stop()


        if tipo == "Recargar cuenta (ingreso)":

            valor = monto
            tipo_mov = "pago"


        else:  # Retirar dinero (egreso)

            valor = -monto
            tipo_mov = "retiro"


        registrar_movimiento(

            usuario,

            tipo_mov,

            referencia,

            valor

        )


        # refrescar cache global

        cargar_todo.clear()


        st.success("Movimiento registrado")

        st.rerun()


    st.divider()


    # ======================
    # SALDO POR USUARIO
    # ======================

    if len(df) > 0:

        resumen = (

            df.groupby("usuario_id")["monto"]

            .sum()

            .reset_index()

        )

        resumen.columns = ["usuario_id", "saldo"]

        resumen = df_usuarios.merge(

            resumen,

            on="usuario_id",

            how="left"

        )

        resumen["saldo"] = resumen["saldo"].fillna(0)

        resumen = resumen.sort_values(by="saldo")


        st.subheader("Estado de cuentas")

        st.dataframe(

            resumen,

            use_container_width=True

        )


    # ======================
    # HISTORIAL COMPLETO
    # ======================

    st.subheader("Detalle de movimientos")


    if len(df) > 0:

        st.dataframe(

            df.sort_values(by="fecha", ascending=False),

            use_container_width=True

        )

    else:

        st.info("No hay movimientos registrados")