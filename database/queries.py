import pandas as pd

from sqlalchemy import text

from database.postgres import engine
from database.postgres import SessionLocal
from database.models import Configuracion


def obtener_config():

    session = SessionLocal()

    try:

        registros = session.query(
            Configuracion
        ).all()

        return [
            {
                "clave": r.clave,
                "valor": r.valor
            }
            for r in registros
        ]

    finally:
        session.close()

def obtener_tabla(nombre_tabla):

    query = f"SELECT * FROM {nombre_tabla}"

    return pd.read_sql(
        text(query),
        engine
    )