"""Funciones puras de apoyo (sin base de datos), cubiertas por pruebas unitarias."""
import base64
import os
from datetime import datetime

# Cobertura aproximada del estado de San Luis Potosí (propuesta, ajustable).
LON_MIN, LON_MAX = -102.4, -98.3
LAT_MIN, LAT_MAX = 21.1, 24.6


def generar_folio(anio=None, aleatorio=None):
    """Folio VIG-AAAA-XXXXXXXX con 8 caracteres base32 aleatorios."""
    anio = anio or datetime.now().year
    sufijo = base64.b32encode(aleatorio or os.urandom(5)).decode()[:8]
    return f"VIG-{anio}-{sufijo}"


def ofuscar(valor, decimales):
    """Reduce la precisión de una coordenada pública (3 decimales ≈ 110 m)."""
    return round(valor, decimales)


def dentro_cobertura(latitud, longitud):
    return LAT_MIN <= latitud <= LAT_MAX and LON_MIN <= longitud <= LON_MAX


def parsear_bbox(texto):
    """'min_lon,min_lat,max_lon,max_lat' -> tupla de floats; ValueError si es inválido."""
    partes = [float(x) for x in texto.split(",")]
    if len(partes) != 4:
        raise ValueError("bbox requiere 4 valores")
    min_lon, min_lat, max_lon, max_lat = partes
    if min_lon >= max_lon or min_lat >= max_lat:
        raise ValueError("bbox con mínimos mayores o iguales a máximos")
    return min_lon, min_lat, max_lon, max_lat
