from __future__ import annotations

from collections import Counter, defaultdict
from datetime import date

from backend.config import DISCLAIMER, TIPOS_EXCLUIDOS, UMBRAL_MINIMO_REPORTES
from backend.mock_data import COLONIAS, REPORTES


def calcular_hotspots(
    tipo_delito: str | None = None,
    fecha_inicio: date | None = None,
    fecha_fin: date | None = None,
    limite: int = 10,
) -> dict:
    reportes_filtrados = []
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
        reportes_filtrados.append(r)

    por_colonia: dict[str, list[dict]] = defaultdict(list)
    for r in reportes_filtrados:
        por_colonia[r["colonia"]].append(r)

    hotspots = []
    colonia_info = {c["nombre"]: c for c in COLONIAS}
    for nombre_colonia, reportes_col in por_colonia.items():
        if len(reportes_col) < UMBRAL_MINIMO_REPORTES:
            continue
        tipos = Counter(r["tipo_delito"] for r in reportes_col)
        tipos_frecuentes = [t for t, _ in tipos.most_common(3)]
        info = colonia_info.get(nombre_colonia, {})
        hotspots.append({
            "colonia": nombre_colonia,
            "ageb": info.get("ageb"),
            "total_reportes": len(reportes_col),
            "tipos_frecuentes": tipos_frecuentes,
            "lat": info.get("lat", 0.0),
            "lng": info.get("lng", 0.0),
        })

    hotspots.sort(key=lambda h: h["total_reportes"], reverse=True)
    return {
        "hotspots": hotspots[:limite],
        "disclaimer": DISCLAIMER,
    }
