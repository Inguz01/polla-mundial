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