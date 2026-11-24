from __future__ import annotations

from collections import defaultdict
from datetime import date

from backend.config import DISCLAIMER, TIPOS_EXCLUIDOS
from backend.mock_data import DATOS_OFICIALES_SESNSP, REPORTES


def calcular_comparativo(
    tipo_delito: str | None = None,
    fecha_inicio: date | None = None,
    fecha_fin: date | None = None,
) -> dict:
    ciudadano_por_mes: dict[str, int] = defaultdict(int)
    for r in REPORTES:
        if r["tipo_delito"] in TIPOS_EXCLUIDOS:
            continue
        if r["estado"] != "validado":
            continue
        if tipo_delito and r["tipo_delito"] != tipo_delito:
            continue
        fecha_r = date.fromisoformat(r["fecha"])
        if fecha_inicio and fecha_r < fecha_inicio:
            continue
        if fecha_fin and fecha_r > fecha_fin:
            continue
        mes = fecha_r.strftime("%Y-%m")
        ciudadano_por_mes[mes] += 1

    oficial_por_mes: dict[str, int] = defaultdict(int)
    for d in DATOS_OFICIALES_SESNSP:
        if tipo_delito and d["tipo_delito"] != tipo_delito:
            continue
        if d["tipo_delito"] in TIPOS_EXCLUIDOS:
            continue
        oficial_por_mes[d["mes"]] += d["total"]

    meses = sorted(set(ciudadano_por_mes) | set(oficial_por_mes))
    datos = []
    for mes in meses:
        datos.append({
            "mes": mes,
            "ciudadano": ciudadano_por_mes.get(mes, 0),
            "oficial": oficial_por_mes.get(mes, 0),
            "tipo_delito": tipo_delito,
        })

    return {
        "datos": datos,
        "nota": "El dato oficial del SESNSP es municipal y mensual.",
        "disclaimer": DISCLAIMER,
    }


def calcular_resumen(
    fecha_inicio: date | None = None,
    fecha_fin: date | None = None,
    colonia: str | None = None,
) -> dict:
    reportes_validos = []
    reportes_semana = 0
    hoy = date.today()
    inicio_semana = date.fromordinal(hoy.toordinal() - hoy.weekday())

    conteo_tipo: dict[str, int] = defaultdict(int)
    conteo_colonia: dict[str, int] = defaultdict(int)
    conteo_mes_actual = 0
    conteo_mes_anterior = 0
    mes_actual = hoy.strftime("%Y-%m")
    mes_anterior = (hoy.replace(day=1) - __import__("datetime").timedelta(days=1)).strftime("%Y-%m")

    for r in REPORTES:
        if r["tipo_delito"] in TIPOS_EXCLUIDOS:
            continue
        if r["estado"] != "validado":
            continue
        fecha_r = date.fromisoformat(r["fecha"])
        if fecha_inicio and fecha_r < fecha_inicio:
            continue
        if fecha_fin and fecha_r > fecha_fin:
            continue
        if colonia and r["colonia"] != colonia:
            continue

        reportes_validos.append(r)
        conteo_tipo[r["tipo_delito"]] += 1
        conteo_colonia[r["colonia"]] += 1

        if fecha_r >= inicio_semana:
            reportes_semana += 1
        if fecha_r.strftime("%Y-%m") == mes_actual:
            conteo_mes_actual += 1
        elif fecha_r.strftime("%Y-%m") == mes_anterior:
            conteo_mes_anterior += 1

    if conteo_mes_anterior > 0:
        tendencia = "alza" if conteo_mes_actual > conteo_mes_anterior else "baja"
    else:
        tendencia = "sin datos previos"

    tipo_top = max(conteo_tipo.items(), key=lambda x: x[1]) if conteo_tipo else ("N/A", 0)
    colonia_top = max(conteo_colonia.items(), key=lambda x: x[1]) if conteo_colonia else ("N/A", 0)

    from backend.mock_data import CATALOGO_DELITOS

    return {
        "total_reportes": len(reportes_validos),
        "reportes_semana": reportes_semana,
        "tipo_mas_frecuente": {
            "clave": tipo_top[0],
            "nombre": CATALOGO_DELITOS.get(tipo_top[0], tipo_top[0]),
            "total": tipo_top[1],
        },
        "colonia_mas_reportes": {
            "nombre": colonia_top[0],
            "total": colonia_top[1],
        },
        "tendencia": tendencia,
        "disclaimer": DISCLAIMER,
    }
