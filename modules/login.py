import streamlit as st
from utils.data_loader import cargar_todo
from utils.security import verificar_password


def login_page():

    st.title("Iniciar sesión")

    usuario = st.text_input("Usuario")
    password = st.text_input("Contraseña", type="password")

    if st.button("Ingresar"):

        # =========================
        # VALIDACIÓN INPUT
        # =========================

        if usuario.strip() == "" or password.strip() == "":
            st.warning("Ingresa usuario y contraseña")
            return

        # =========================
        # CARGA DATOS
        # =========================

        data = cargar_todo()
        df_users = data.get("usuarios")

        if df_users is None or len(df_users) == 0:
            st.error("No hay usuarios registrados")
            return

        # =========================
        # 🔥 LIMPIEZA SEGURA COLUMNAS (SIN ROMPER DATA)
        # =========================

        df_users.columns = [str(c).strip().lower() for c in df_users.columns]

        # DEBUG TEMPORAL (puedes borrar luego)
        # st.write(df_users)

        # =========================
        # VALIDAR ESTRUCTURA
        # =========================

        columnas_requeridas = ["usuario_id", "password", "rol", "activo"]

        for col in columnas_requeridas:
            if col not in df_users.columns:
                st.error(f"Falta columna: {col}")
                st.write("Columnas detectadas:", df_users.columns)
                return

        # =========================
        # LIMPIEZA DE DATOS
        # =========================

        df_users["usuario_id"] = df_users["usuario_id"].astype(str).str.strip()
        df_users["password"] = df_users["password"].astype(str)
        df_users["rol"] = df_users["rol"].astype(str).str.strip()

        # ⚠️ cuidado con NaN en activo
        df_users["activo"] = df_users["activo"].fillna(0).astype(int)

        usuario_input = str(usuario).strip()
        password_input = str(password)

        # =========================
        # VALIDAR USUARIO EXISTE
        # =========================

        user_all = df_users[df_users["usuario_id"] == usuario_input]

        if len(user_all) == 0:
            st.error("Credenciales incorrectas")
            return

        # =========================
        # VALIDAR ACTIVO
        # =========================

        if int(user_all.iloc[0]["activo"]) == 0:
            st.warning("Usuario inactivo")
            return

        # =========================
        # VALIDAR PASSWORD
        # =========================

        hashed = str(user_all.iloc[0]["password"]).strip()

        if hashed.startswith("$2b$"):
            if not verificar_password(password_input, hashed):
                st.error("Credenciales incorrectas")
                return
        else:
            if password_input != hashed:
                st.error("Credenciales incorrectas")
                return

        # =========================
        # LOGIN OK
        # =========================

        st.session_state["usuario"] = user_all.iloc[0]["usuario_id"]
        st.session_state["rol"] = user_all.iloc[0]["rol"]

        st.success("Bienvenido")
        st.rerun()