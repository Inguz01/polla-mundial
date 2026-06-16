import pandas as pd

from sqlalchemy import text

from database.postgres import engine
from database.postgres import SessionLocal
from database.models import Configuracion
from database.models import Resultado
#from utils.helpers import generar_id


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

def guardar_resultado(
    partido_id,
    goles_local,
    goles_visitante
):

    session = SessionLocal()

    try:

        existente = (
            session.query(Resultado)
            .filter(
                Resultado.partido_id == partido_id
            )
            .first()
        )

        if existente:

            existente.goles_local = goles_local
            existente.goles_visitante = goles_visitante

        else:

            nuevo = Resultado(
                id=generar_id(),
                partido_id=partido_id,
                goles_local=goles_local,
                goles_visitante=goles_visitante
            )

            session.add(nuevo)

        session.commit()

    finally:

        session.close()