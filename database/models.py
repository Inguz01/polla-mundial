from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    Date,
    Time,
    DateTime,
    Numeric
)

#from sqlalchemy.orm import declarative_base
from sqlalchemy import UniqueConstraint
from database.postgres import Base

#Base = declarative_base()


class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True)
    usuario_id = Column(String(50), unique=True)
    password = Column(String)
    rol = Column(String(20))
    activo = Column(Boolean)


class Partido(Base):
    __tablename__ = "partidos"

    id = Column(Integer, primary_key=True)

    equipo_local = Column(String(100))
    equipo_visitante = Column(String(100))

    fecha = Column(Date)
    hora = Column(Time)

    fase = Column(String(50))
    grupo = Column(String(10))

    estado = Column(String(20))


class Equipo(Base):
    __tablename__ = "equipos"

    equipo = Column(String(100), primary_key=True)

    codigo = Column(String(100))


class Prediccion(Base):
    __tablename__ = "predicciones"

    __table_args__ = (
        UniqueConstraint(
            "usuario_id",
            "partido_id",
            name="uq_pred_usuario_partido"
        ),
    )

    id = Column(String, primary_key=True)

    usuario_id = Column(String(50), nullable=False)

    partido_id = Column(Integer, nullable=False)

    goles_local = Column(Integer)

    goles_visitante = Column(Integer)

    participa = Column(Boolean, default=False)

    pago_validado = Column(Boolean, default=False)


class Resultado(Base):
    __tablename__ = "resultados"

    id = Column(String, primary_key=True)

    partido_id = Column(Integer)

    goles_local = Column(Integer)

    goles_visitante = Column(Integer)


class Movimiento(Base):
    __tablename__ = "movimientos"

    id = Column(String, primary_key=True)

    usuario_id = Column(String(50))

    fecha = Column(DateTime)

    tipo = Column(String(50))

    referencia = Column(String(100))

    monto = Column(Numeric)

    fecha_liquidacion = Column(DateTime, nullable=True)


class Configuracion(Base):
    __tablename__ = "configuracion"

    clave = Column(String(100), primary_key=True)

    valor = Column(String(100))