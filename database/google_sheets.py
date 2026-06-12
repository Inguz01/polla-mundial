import streamlit as st
import gspread

from google.oauth2.service_account import Credentials

@st.cache_resource
def connect():

    scope = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]

    creds = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=scope
    )

    client = gspread.authorize(creds)

    return client.open_by_key("1r6JrtNhWMbdPdawy8nxT_9pROQLn1O0Yad3gWo3nm7U")