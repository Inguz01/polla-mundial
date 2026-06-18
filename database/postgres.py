from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
import streamlit as st
import os

# Primero intenta leer desde Streamlit Secrets
try:
    DATABASE_URL = st.secrets["DATABASE_URL"]
except Exception:
    # Si no existe (ejecución local), usa .env
    from dotenv import load_dotenv
    load_dotenv()
    DATABASE_URL = os.getenv("DATABASE_URL")

print("SECRETS:", st.secrets)
print("DATABASE_URL:", st.secrets.get("DATABASE_URL"))

engine = create_engine(DATABASE_URL)

assert st.secrets.get("DATABASE_URL") is not None

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()