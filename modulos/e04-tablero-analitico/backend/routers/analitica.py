from __future__ import annotations

from datetime import date
from typing import Literal, Optional

from fastapi import APIRouter, Query

from backend.services.comparativo import calcular_comparativo, calcular_resumen
from backend.services.hotspots import calcular_hotspots
from backend.services.tendencias import calcular_tendencias, calcular_tipos_delito

router = APIRouter(prefix="/api/v1/analitica", tags=["analitica"])


@router.get("/tendencias")
def obtener_tendencias(
    periodo: Literal["dia", "semana", "mes"] = "semana",
    tipo_delito: Optional[str] = None,
    fecha_inicio: Optional[date] = None,
    fecha_fin: Optional[date] = None,
    colonia: Optional[str] = None,
    ageb: Optional[str] = None,
):
    return calcular_tendencias(
        periodo=periodo,
        tipo_delito=tipo_delito,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        colonia=colonia,
        ageb=ageb,
    )


@router.get("/hotspots")
def obtener_hotspots(
    tipo_delito: Optional[str] = None,
    fecha_inicio: Optional[date] = None,
    fecha_fin: Optional[date] = None,
    limite: int = Query(10, ge=1, le=50),
):
    return calcular_hotspots(
        tipo_delito=tipo_delito,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        limite=limite,
    )


@router.get("/comparativo")
def obtener_comparativo(
    tipo_delito: Optional[str] = None,
    fecha_inicio: Optional[date] = None,
    fecha_fin: Optional[date] = None,
):
    return calcular_comparativo(
        tipo_delito=tipo_delito,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
    )


@router.get("/resumen")
def obtener_resumen(
    fecha_inicio: Optional[date] = None,
    fecha_fin: Optional[date] = None,
    colonia: Optional[str] = None,
):
    return calcular_resumen(
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        colonia=colonia,
    )


@router.get("/tipos-delito")
def obtener_tipos_delito(
    fecha_inicio: Optional[date] = None,
    fecha_fin: Optional[date] = None,
    colonia: Optional[str] = None,
    ageb: Optional[str] = None,
):
    return calcular_tipos_delito(
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        colonia=colonia,
        ageb=ageb,
    )
