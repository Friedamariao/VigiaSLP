from __future__ import annotations

from collections import defaultdict
from datetime import date, timedelta

from backend.config import DISCLAIMER, TIPOS_EXCLUIDOS
from backend.mock_data import CATALOGO_DELITOS, REPORTES


def calcular_tendencias(
    periodo: str = "semana",
    tipo_delito: str | None = None,
    fecha_inicio: date | None = None,
    fecha_fin: date | None = None,
    colonia: str | None = None,
    ageb: str | None = None,
) -> dict:
    reportes = _filtrar_reportes(tipo_delito, fecha_inicio, fecha_fin, colonia, ageb)

    agrupados: dict[str, list[dict]] = defaultdict(list)
    for r in reportes:
        clave = _clave_periodo(r["fecha"], periodo)
        agrupados[clave].append(r)

    datos = []
    for fecha_clave in sorted(agrupados):
        grupo = agrupados[fecha_clave]
        por_tipo: dict[str, int] = defaultdict(int)
        for r in grupo:
            por_tipo[r["tipo_delito"]] += 1
        datos.append({
            "fecha": fecha_clave,
            "total": len(grupo),
            "por_tipo": dict(por_tipo),
        })

    return {
        "periodo": periodo,
        "datos": datos,
        "disclaimer": DISCLAIMER,
    }


def _filtrar_reportes(
    tipo_delito: str | None,
    fecha_inicio: date | None,
    fecha_fin: date | None,
    colonia: str | None,
    ageb: str | None,
) -> list[dict]:
    resultado = []
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
        if colonia and r["colonia"] != colonia:
            continue
        if ageb and r["ageb"] != ageb:
            continue
        resultado.append(r)
    return resultado


def _clave_periodo(fecha_str: str, periodo: str) -> str:
    fecha = date.fromisoformat(fecha_str)
    if periodo == "dia":
        return fecha.isoformat()
    if periodo == "semana":
        inicio_semana = fecha - timedelta(days=fecha.weekday())
        return inicio_semana.isoformat()
    if periodo == "mes":
        return fecha.strftime("%Y-%m")
    return fecha.isoformat()


def calcular_tipos_delito(
    fecha_inicio: date | None = None,
    fecha_fin: date | None = None,
    colonia: str | None = None,
    ageb: str | None = None,
) -> dict:
    reportes = _filtrar_reportes(None, fecha_inicio, fecha_fin, colonia, ageb)
    conteo: dict[str, int] = defaultdict(int)
    for r in reportes:
        conteo[r["tipo_delito"]] += 1

    tipos = sorted(
        [
            {"clave": k, "nombre": CATALOGO_DELITOS.get(k, k), "total": v}
            for k, v in conteo.items()
        ],
        key=lambda x: x["total"],
        reverse=True,
    )
    return {"tipos": tipos, "disclaimer": DISCLAIMER}
