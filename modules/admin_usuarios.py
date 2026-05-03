import streamlit as st
from database.google_sheets import connect
from utils.data_loader import cargar_todo
from utils.dataframe_utils import normalizar_columnas


def admin_usuarios_page():

    if st.session_state.get("rol") != "admin":
        st.error("No tienes permisos")
        st.stop()

    st.title("Administración de usuarios")

    data = cargar_todo()
    df = data["usuarios"]
    df = normalizar_columnas(df)

    # =========================
    # LISTADO
    # =========================

    st.subheader("Usuarios")

    st.dataframe(df, use_container_width=True)

    st.divider()

    # =========================
    # CREAR USUARIO
    # =========================

    st.subheader("Crear usuario")

    nuevo_usuario = st.text_input("Usuario")
    password = st.text_input("Contraseña", type="password")
    rol = st.selectbox("Rol", ["usuario", "admin"])

    if st.button("Crear usuario"):

        if not nuevo_usuario or not password:
            st.warning("Completa todos los campos")
            return

        if len(df[df["usuario_id"] == nuevo_usuario]) > 0:
            st.error("El usuario ya existe")
            return

        db = connect()
        sheet = db.worksheet("usuarios")

        nuevo_id = len(df) + 1

        sheet.append_row([
            nuevo_id,
            nuevo_usuario,
            password,
            rol,
            1
        ])

        st.success("Usuario creado")
        st.rerun()

    st.divider()

    # =========================
    # ACTIVAR / DESACTIVAR
    # =========================

    st.subheader("Activar / Desactivar usuario")

    usuario_sel = st.selectbox(
        "Selecciona usuario",
        df["usuario_id"].tolist()
    )

    estado_actual = df[df["usuario_id"] == usuario_sel]["activo"].iloc[0]

    nuevo_estado = 0 if estado_actual == 1 else 1

    if st.button("Cambiar estado"):

        db = connect()
        sheet = db.worksheet("usuarios")

        fila = df[df["usuario_id"] == usuario_sel].index[0] + 2

        sheet.update(f"E{fila}", [[nuevo_estado]])

        st.success("Estado actualizado")
        st.rerun()