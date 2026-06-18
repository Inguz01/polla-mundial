from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
import streamlit as st

DATABASE_URL = st.secrets.get("DATABASE_URL")

if DATABASE_URL is None:
    raise Exception(
        f"DATABASE_URL no encontrada. Secrets disponibles: {list(st.secrets.keys())}"
    )

engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()