import streamlit as st
from database.google_sheets import connect
from utils.data_loader import cargar_todo
from utils.dataframe_utils import normalizar_columnas
from utils.security import hash_password


def admin_usuarios_page():

    if st.session_state.get("rol") != "admin":
        st.error("No tienes permisos")
        st.stop()

    st.title("Administración de usuarios")

    data = cargar_todo()
    df = data["usuarios"]
    df = normalizar_columnas(df)

    # Asegurar columnas
    if "usuario_id" not in df.columns:
        df["usuario_id"] = ""

    if "activo" not in df.columns:
        df["activo"] = 1

    df["usuario_id"] = df["usuario_id"].astype(str).str.strip()
    df["activo"] = df["activo"].astype(int)

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

        nuevo_usuario = nuevo_usuario.strip().lower()

        if not nuevo_usuario or not password:
            st.warning("Completa todos los campos")
            return

        usuarios_existentes = (
            df["usuario_id"]
            .astype(str)
            .str.strip()
            .str.lower()
        )

        if nuevo_usuario in usuarios_existentes.values:
            st.error("El usuario ya existe")
            return

        db = connect()
        sheet = db.worksheet("usuarios")

        nuevo_id = 1 if len(df) == 0 else int(df["id"].max()) + 1

        sheet.append_row([
            nuevo_id,
            nuevo_usuario,
            hash_password(password),
            rol,
            1
        ])

        # Refrescar cache
        cargar_todo.clear()

        st.success("Usuario creado")
        st.rerun()

    st.divider()

    # =========================
    # ACTIVAR / DESACTIVAR
    # =========================

    st.subheader("Activar / Desactivar usuario")

    if len(df) == 0:
        st.info("No hay usuarios")
        return

    usuario_sel = st.selectbox(
        "Selecciona usuario",
        df["usuario_id"].tolist()
    )

    estado_actual = int(
        df[df["usuario_id"] == usuario_sel]["activo"].iloc[0]
    )

    nuevo_estado = 0 if estado_actual == 1 else 1

    if st.button("Cambiar estado"):

        db = connect()
        sheet = db.worksheet("usuarios")

        fila = df[df["usuario_id"] == usuario_sel].index[0] + 2

        sheet.update(f"E{fila}", [[nuevo_estado]])

        # Refrescar cache
        cargar_todo.clear()

        st.success("Estado actualizado")
        st.rerun()