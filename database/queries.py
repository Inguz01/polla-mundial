import pandas as pd

from sqlalchemy import text

from database.postgres import engine
from database.postgres import SessionLocal
from database.models import Configuracion
from database.models import Resultado
#from utils.helpers import generar_id

from database.models import Movimiento
from utils.helpers import generar_id
from datetime import datetime
from database.models import Prediccion


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

def guardar_movimientos(lista):

    if not lista:
        return

    session = SessionLocal()

    try:

        for m in lista:

            fecha_liquidacion = m.get(
                "fecha_liquidacion"
            )

            if isinstance(
                fecha_liquidacion,
                str
            ):
                fecha_liquidacion = pd.to_datetime(
                    fecha_liquidacion
                ).to_pydatetime()

            movimiento = Movimiento(
                id=generar_id(),
                usuario_id=str(
                    m["usuario_id"]
                ).strip().lower(),
                fecha=datetime.now(),
                tipo=m["tipo"],
                referencia=m["referencia"],
                monto=m["monto"],
                fecha_liquidacion=fecha_liquidacion
            )

            session.add(movimiento)

        session.commit()

    finally:

        session.close()

def guardar_prediccion(
    usuario_id,
    partido_id,
    goles_local,
    goles_visitante
):

    session = SessionLocal()

    try:

        existente = (
            session.query(Prediccion)
            .filter(
                Prediccion.usuario_id == usuario_id,
                Prediccion.partido_id == partido_id
            )
            .first()
        )

        if existente:

            existente.goles_local = goles_local
            existente.goles_visitante = goles_visitante
            existente.participa = True
            existente.pago_validado = False

        else:

            nueva = Prediccion(
                id=generar_id(),
                usuario_id=usuario_id,
                partido_id=partido_id,
                goles_local=goles_local,
                goles_visitante=goles_visitante,
                participa=True,
                pago_validado=False
            )

            session.add(nueva)

        session.commit()

    finally:

        session.close()

def eliminar_prediccion(
    usuario_id,
    partido_id
):

    session = SessionLocal()

    try:

        filas = (
            session.query(Prediccion)
            .filter(
                Prediccion.usuario_id == usuario_id,
                Prediccion.partido_id == partido_id
            )
            .delete()
        )

        session.commit()

        return filas > 0

    finally:

        session.close()

