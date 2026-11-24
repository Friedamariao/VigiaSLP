"""Datos sintéticos para desarrollo independiente de E01."""

import random
from datetime import date, timedelta

CATALOGO_DELITOS = {
    "RTR": "Robo a transeúnte",
    "RCH": "Robo a casa habitación",
    "RVE": "Robo de vehículo",
    "RAP": "Robo de autopartes",
    "RNE": "Robo a negocio",
    "RTP": "Robo en transporte público",
    "LES": "Lesiones / riña",
    "DAN": "Daño a la propiedad / vandalismo",
    "FRA": "Fraude o extorsión",
    "ACO": "Acoso en vía pública",
    "SOS": "Actividad sospechosa",
}

COLONIAS = [
    {"nombre": "Centro Histórico", "ageb": "2404800010259", "lat": 22.1565, "lng": -100.9855},
    {"nombre": "Jardín", "ageb": "2404800010263", "lat": 22.1480, "lng": -100.9780},
    {"nombre": "Tequisquiapan", "ageb": "2404800010382", "lat": 22.1420, "lng": -100.9700},
    {"nombre": "San Luis", "ageb": "2404800010278", "lat": 22.1500, "lng": -100.9900},
    {"nombre": "Himno Nacional", "ageb": "2404800010297", "lat": 22.1350, "lng": -100.9650},
    {"nombre": "Industrial Aviación", "ageb": "2404800010301", "lat": 22.1600, "lng": -101.0100},
    {"nombre": "Del Valle", "ageb": "2404800010316", "lat": 22.1300, "lng": -100.9500},
    {"nombre": "Lomas", "ageb": "2404800010320", "lat": 22.1700, "lng": -100.9600},
    {"nombre": "Tangamanga", "ageb": "2404800010335", "lat": 22.1250, "lng": -100.9850},
    {"nombre": "Morales", "ageb": "2404800010340", "lat": 22.1650, "lng": -100.9750},
    {"nombre": "Saucito", "ageb": "2404800010355", "lat": 22.1800, "lng": -100.9700},
    {"nombre": "Prados del Sur", "ageb": "2404800010360", "lat": 22.1150, "lng": -100.9800},
]

random.seed(42)


def _generar_reportes():
    reportes = []
    inicio = date(2026, 7, 1)
    for i in range(600):
        dia = inicio + timedelta(days=random.randint(0, 145))
        tipo = random.choice(list(CATALOGO_DELITOS.keys()))
        colonia = random.choice(COLONIAS)
        reportes.append({
            "id": i + 1,
            "fecha": dia.isoformat(),
            "tipo_delito": tipo,
            "colonia": colonia["nombre"],
            "ageb": colonia["ageb"],
            "lat": colonia["lat"] + random.uniform(-0.005, 0.005),
            "lng": colonia["lng"] + random.uniform(-0.005, 0.005),
            "estado": "validado",
        })
    return reportes


REPORTES = _generar_reportes()


def _generar_datos_oficiales():
    datos = []
    for mes_offset in range(6):
        mes = date(2026, 7 + mes_offset, 1)
        for clave in CATALOGO_DELITOS:
            datos.append({
                "mes": mes.strftime("%Y-%m"),
                "tipo_delito": clave,
                "total": random.randint(5, 40),
            })
    return datos


DATOS_OFICIALES_SESNSP = _generar_datos_oficiales()
