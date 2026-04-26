import streamlit as st
import pandas as pd

from utils.movimientos import registrar_movimiento
from utils.data_loader import cargar_todo



def movimientos_page():

    st.title("Movimientos financieros")


    # ===== carga centralizada =====

    data = cargar_todo()

    df = data["movimientos"].copy()

    # ==============================


    # ======================
    # FORMULARIO ADMIN
    # ======================

    st.subheader("Registrar pago o ajuste")


    if len(df) > 0:

        usuarios = sorted(df["usuario_id"].unique())

    else:

        usuarios = []


    col1, col2 = st.columns(2)


    with col1:

        usuario = st.selectbox(

            "Usuario",

            usuarios

        )

        tipo = st.selectbox(

            "Tipo movimiento",

            [

                "pago recibido",

                "pago realizado",

                "ajuste manual"

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


        if monto == 0:

            st.warning("Ingrese un monto válido")

            st.stop()


        if tipo == "pago recibido":

            valor = monto
            tipo_mov = "pago"


        elif tipo == "pago realizado":

            valor = -monto
            tipo_mov = "retiro"


        else:

            valor = monto
            tipo_mov = "ajuste"


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

            .sort_values(by="monto")

        )


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