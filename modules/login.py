import streamlit as st

from database.google_sheets import connect
from services.auth import verify_password


def login_page():

    st.title("login")

    email = st.text_input("email")

    password = st.text_input(
        "password",
        type="password"
    )

    if st.button("ingresar"):

        db = connect()

        sheet = db.worksheet("usuarios")

        usuarios = sheet.get_all_records()

        for u in usuarios:

            if u["email"] == email:

                if verify_password(
                    password,
                    u["password"]
                ):

                    st.session_state.user = u

                    st.success("bienvenido")

                    return

        st.error("credenciales incorrectas")