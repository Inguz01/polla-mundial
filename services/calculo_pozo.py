from config.settings import (
    PORCENTAJE_ADMIN,
    PORCENTAJE_DESARROLLADOR
)

def calcular_pozo(total_recaudado):

    admin = total_recaudado * PORCENTAJE_ADMIN

    desarrollador = total_recaudado * PORCENTAJE_DESARROLLADOR

    pozo = total_recaudado - admin - desarrollador

    return admin, desarrollador, pozo