from __future__ import annotations

from datetime import date
from typing import Optional

from pydantic import BaseModel, Field


class FiltrosQuery(BaseModel):
    tipo_delito: Optional[str] = Field(None, description="Clave del tipo de delito (ej: RTR)")
    fecha_inicio: Optional[date] = None
    fecha_fin: Optional[date] = None
    colonia: Optional[str] = None
    ageb: Optional[str] = None


class PuntoTendencia(BaseModel):
    fecha: str
    total: int
    por_tipo: dict[str, int]


class TendenciasResponse(BaseModel):
    periodo: str
    datos: list[PuntoTendencia]
    disclaimer: str


class Hotspot(BaseModel):
    colonia: str
    ageb: Optional[str] = None
    total_reportes: int
    tipos_frecuentes: list[str]
    lat: float
    lng: float


class HotspotsResponse(BaseModel):
    hotspots: list[Hotspot]
    disclaimer: str


class PuntoComparativo(BaseModel):
    mes: str
    ciudadano: int
    oficial: int
    tipo_delito: Optional[str] = None


class ComparativoResponse(BaseModel):
    datos: list[PuntoComparativo]
    nota: str = "El dato oficial del SESNSP es municipal y mensual."
    disclaimer: str


class TipoDelitoConteo(BaseModel):
    clave: str
    nombre: str
    total: int


class ResumenResponse(BaseModel):
    total_reportes: int
    reportes_semana: int
    tipo_mas_frecuente: TipoDelitoConteo
    colonia_mas_reportes: dict[str, object]
    tendencia: str
    disclaimer: str


class TiposDelitoResponse(BaseModel):
    tipos: list[TipoDelitoConteo]
    disclaimer: str
