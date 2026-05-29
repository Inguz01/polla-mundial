import streamlit as st
import pandas as pd
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

        # calcular nuevo ID ignorando valores no numéricos que puedan venir de Sheets
        ids_validos = pd.to_numeric(df["id"], errors="coerce").dropna()
        nuevo_id = int(ids_validos.max()) + 1 if len(ids_validos) > 0 else 1

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

    st.divider()

    # =========================
    # CAMBIAR CONTRASEÑA
    # =========================

    st.subheader("Cambiar contraseña")

    usuario_pwd = st.selectbox(
        "Selecciona usuario",
        df["usuario_id"].tolist(),
        key="sel_pwd"
    )

    nueva_pwd = st.text_input(
        "Nueva contraseña",
        type="password",
        key="nueva_pwd"
    )

    confirmar_pwd = st.text_input(
        "Confirmar contraseña",
        type="password",
        key="confirmar_pwd"
    )

    if st.button("Cambiar contraseña"):

        if not nueva_pwd.strip():
            st.warning("Ingresa la nueva contraseña")

        elif nueva_pwd != confirmar_pwd:
            st.error("Las contraseñas no coinciden")

        else:

            db = connect()
            sheet = db.worksheet("usuarios")

            fila = df[df["usuario_id"] == usuario_pwd].index[0] + 2

            sheet.update(f"C{fila}", [[hash_password(nueva_pwd)]])

            cargar_todo.clear()

            st.success(f"Contraseña de {usuario_pwd} actualizada correctamente")

    st.divider()

    # =========================
    # LISTADO
    # =========================

    st.subheader("Usuarios registrados")

    df_view = df.copy()

    # estado legible
    df_view["estado"] = df_view["activo"].apply(
        lambda x: "Activo" if int(x) == 1 else "Inactivo"
    )

    # columnas visibles
    df_view = df_view[[
        "usuario_id",
        "rol",
        "estado"
    ]]

    st.dataframe(
        df_view,
        use_container_width=True,
        hide_index=True
    )