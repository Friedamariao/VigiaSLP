"""API central de VigíaSLP (E01) · RF-01.1 a RF-01.8 (versión de construcción, Avance 3)."""
import json
import logging
import os
import time
import uuid
from datetime import datetime, timezone
from typing import Literal, Optional

from fastapi import FastAPI, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from psycopg.errors import UniqueViolation
from starlette.exceptions import HTTPException as StarletteHTTPException

from .db import conexion
from .util import dentro_cobertura, generar_folio, ofuscar, parsear_bbox

VERSION = "0.1.0"
logger = logging.getLogger("vigiaslp.api")
logging.basicConfig(level=os.environ.get("API_LOG_LEVEL", "INFO").upper(), format="%(message)s")

app = FastAPI(
    title="VigíaSLP · API central",
    version=VERSION,
    description="API REST del módulo E01. Coordenadas WGS 84 (EPSG:4326). Los reportes ciudadanos no son cifras oficiales.",
)
ESTADOS = ("PENDIENTE", "PUBLICADO", "RECHAZADO", "DUPLICADO")
ORIENTACION_VFS = "Este tipo de caso no se publica en el mapa. Si estás en peligro llama al 911; para orientación y denuncia anónima, al 089."


# ---------- Errores (RFC 9457, application/problem+json) ----------
class ErrorApi(Exception):
    def __init__(self, estado, codigo, titulo, detalle=None, **extra):
        self.estado, self.codigo, self.titulo, self.detalle, self.extra = estado, codigo, titulo, detalle, extra


def problema(estado, codigo, titulo, detalle=None, **extra):
    cuerpo = {"type": f"https://vigiaslp.local/errores/{codigo.lower()}", "title": titulo, "status": estado, "code": codigo}
    if detalle:
        cuerpo["detail"] = detalle
    cuerpo.update(extra)
    return JSONResponse(cuerpo, status_code=estado, media_type="application/problem+json")


@app.exception_handler(ErrorApi)
async def _error_api(_req, exc):
    return problema(exc.estado, exc.codigo, exc.titulo, exc.detalle, **exc.extra)


@app.exception_handler(RequestValidationError)
async def _error_validacion(_req, exc):
    errores = [{"campo": ".".join(str(x) for x in e["loc"]), "mensaje": e["msg"]} for e in exc.errors()]
    return problema(422, "VALIDACION_FALLIDA", "Los datos enviados no son válidos", errores=errores)


@app.exception_handler(StarletteHTTPException)
async def _error_http(_req, exc):
    return problema(exc.status_code, "ERROR_HTTP", str(exc.detail))


# ---------- Bitácora estructurada (RF-01.8) ----------
@app.middleware("http")
async def bitacora(request: Request, call_next):
    inicio, id_solicitud = time.perf_counter(), request.headers.get("x-request-id") or str(uuid.uuid4())
    respuesta = await call_next(request)
    respuesta.headers["x-request-id"] = id_solicitud
    logger.info(json.dumps({
        "evento": "peticion", "id_solicitud": id_solicitud, "metodo": request.method, "ruta": request.url.path,
        "estado": respuesta.status_code, "duracion_ms": round((time.perf_counter() - inicio) * 1000, 2),
    }))
    return respuesta


# ---------- Modelos ----------
class TipoDelitoIn(BaseModel):
    codigo: str = Field(min_length=3, max_length=20)
    categoria: str = Field(min_length=1, max_length=80)
    tipo: str = Field(min_length=1, max_length=80)
    subtipo: str = Field(min_length=1, max_length=120)
    es_vfs: bool = False


class ReporteIn(BaseModel):
    tipo_delito_id: int = Field(gt=0)
    descripcion: Optional[str] = Field(default=None, max_length=500)
    fecha_hecho: datetime
    latitud: float = Field(ge=-90, le=90)
    longitud: float = Field(ge=-180, le=180)


class BusquedaIn(BaseModel):
    poligono: dict = Field(description="GeoJSON de tipo Polygon (longitud, latitud)")
    tipo_delito_id: Optional[int] = None
    desde: Optional[datetime] = None
    hasta: Optional[datetime] = None
    estado: Literal["PENDIENTE", "PUBLICADO", "RECHAZADO", "DUPLICADO"] = "PUBLICADO"
    pagina: int = Field(default=1, ge=1)
    tamano: int = Field(default=50, ge=1, le=200)


# ---------- Salud y versión (RF-01.7) ----------
@app.get("/health", tags=["Operación"])
def salud():
    try:
        with conexion() as con:
            con.execute("SELECT 1")
        return {"estado": "ok", "base_datos": "ok"}
    except Exception:
        return JSONResponse({"estado": "degradado", "base_datos": "sin_conexion"}, status_code=503)


@app.get("/version", tags=["Operación"])
def version():
    return {"nombre": "vigiaslp-api", "version": VERSION, "api": "v1"}


# ---------- Catálogo de tipos de delito (RF-01.1) ----------
@app.get("/api/v1/tipos-delito", tags=["Catálogo"])
def listar_tipos(categoria: Optional[str] = None, incluir_inactivos: bool = False):
    sql = "SELECT id, codigo, categoria, tipo, subtipo, codigo_sesnsp, version_catalogo, es_vfs, publicable_mapa, activo FROM tipos_delito WHERE true"
    params = {}
    if categoria:
        sql += " AND categoria = %(categoria)s"
        params["categoria"] = categoria
    if not incluir_inactivos:
        sql += " AND activo"
    sql += " ORDER BY codigo"
    with conexion() as con:
        return {"datos": con.execute(sql, params).fetchall()}


@app.post("/api/v1/tipos-delito", status_code=201, tags=["Catálogo"])
def crear_tipo(t: TipoDelitoIn):
    try:
        with conexion() as con:
            fila = con.execute(
                """INSERT INTO tipos_delito (codigo, categoria, tipo, subtipo, version_catalogo, es_vfs, publicable_mapa)
                   VALUES (%s,%s,%s,%s,(SELECT version FROM catalogo_version WHERE vigente LIMIT 1),%s,%s)
                   RETURNING id, codigo, categoria, tipo, subtipo, es_vfs, publicable_mapa, activo""",
                (t.codigo, t.categoria, t.tipo, t.subtipo, t.es_vfs, not t.es_vfs),
            ).fetchone()
        return fila
    except UniqueViolation:
        raise ErrorApi(409, "TIPO_DUPLICADO", "Ya existe un tipo con ese código", f"codigo={t.codigo}")


@app.delete("/api/v1/tipos-delito/{tipo_id}", status_code=204, tags=["Catálogo"])
def baja_tipo(tipo_id: int):
    with conexion() as con:
        fila = con.execute("UPDATE tipos_delito SET activo = false WHERE id = %s RETURNING id", (tipo_id,)).fetchone()
    if not fila:
        raise ErrorApi(404, "TIPO_NO_ENCONTRADO", "El tipo de delito no existe")


# ---------- Reportes (RF-01.2) ----------
def _publico(fila):
    dec = int(os.environ.get("OFUSCACION_DECIMALES", "3"))
    fila["latitud"], fila["longitud"] = ofuscar(fila["latitud"], dec), ofuscar(fila["longitud"], dec)
    return fila


SELECT_REPORTE = """SELECT r.folio, r.estado, r.descripcion, r.fecha_hecho, r.creado_en,
       t.id AS tipo_delito_id, t.codigo AS tipo_codigo, t.subtipo AS tipo_nombre,
       c.id AS colonia_id, c.nombre AS colonia, c.ageb,
       ST_Y(r.ubicacion) AS latitud, ST_X(r.ubicacion) AS longitud"""
FROM_REPORTE = """ FROM reportes r JOIN tipos_delito t ON t.id = r.tipo_delito_id LEFT JOIN colonias c ON c.id = r.colonia_id"""


@app.post("/api/v1/reportes", status_code=201, tags=["Reportes"])
def crear_reporte(r: ReporteIn):
    if not dentro_cobertura(r.latitud, r.longitud):
        raise ErrorApi(422, "UBICACION_FUERA_DE_COBERTURA", "La ubicación está fuera de San Luis Potosí")
    fecha = r.fecha_hecho if r.fecha_hecho.tzinfo else r.fecha_hecho.replace(tzinfo=timezone.utc)
    if fecha > datetime.now(timezone.utc):
        raise ErrorApi(422, "FECHA_FUTURA", "La fecha del hecho no puede ser futura")
    with conexion() as con:
        tipo = con.execute("SELECT id, es_vfs, activo FROM tipos_delito WHERE id = %s", (r.tipo_delito_id,)).fetchone()
        if not tipo or not tipo["activo"]:
            raise ErrorApi(422, "TIPO_INVALIDO", "El tipo de delito no existe o está dado de baja")
        if tipo["es_vfs"]:
            raise ErrorApi(422, "TIPO_NO_PUBLICABLE", "Este tipo de caso no se registra en el mapa", ORIENTACION_VFS)
        for _ in range(3):
            folio = generar_folio()
            try:
                with con.transaction():
                    fila = con.execute(
                        """INSERT INTO reportes (folio, tipo_delito_id, descripcion, fecha_hecho, ubicacion, colonia_id)
                           VALUES (%(f)s, %(t)s, %(d)s, %(fh)s, ST_SetSRID(ST_MakePoint(%(lon)s, %(lat)s), 4326),
                                   (SELECT id FROM colonias WHERE ST_Covers(geom, ST_SetSRID(ST_MakePoint(%(lon)s, %(lat)s), 4326)) LIMIT 1))
                           RETURNING id, folio""",
                        {"f": folio, "t": r.tipo_delito_id, "d": r.descripcion, "fh": fecha, "lon": r.longitud, "lat": r.latitud},
                    ).fetchone()
                    con.execute("INSERT INTO historial_estado_reporte (reporte_id, estado_anterior, estado_nuevo, motivo) VALUES (%s, NULL, 'PENDIENTE', 'Alta del reporte')", (fila["id"],))
                break
            except UniqueViolation:
                continue
        else:
            raise ErrorApi(500, "FOLIO_NO_GENERADO", "No se pudo generar un folio único")
    return {"folio": fila["folio"], "estado": "PENDIENTE"}


@app.get("/api/v1/reportes/{folio}", tags=["Reportes"])
def obtener_reporte(folio: str):
    with conexion() as con:
        fila = con.execute(SELECT_REPORTE + FROM_REPORTE + " WHERE r.folio = %s", (folio,)).fetchone()
    if not fila:
        raise ErrorApi(404, "REPORTE_NO_ENCONTRADO", "No existe un reporte con ese folio")
    return _publico(fila)


# ---------- Consultas geoespaciales (RF-01.3 y RF-01.4) ----------
def _consultar(extra_sql, params, pagina, tamano):
    cond = ["r.estado = %(estado)s"] + extra_sql
    sql = (SELECT_REPORTE + ", COUNT(*) OVER() AS total" + FROM_REPORTE + " WHERE " + " AND ".join(cond)
           + " ORDER BY r.fecha_hecho DESC, r.id DESC LIMIT %(limite)s OFFSET %(desplazamiento)s")
    params = {**params, "limite": tamano, "desplazamiento": (pagina - 1) * tamano}
    with conexion() as con:
        filas = con.execute(sql, params).fetchall()
    total = filas[0]["total"] if filas else 0
    datos = [_publico({k: v for k, v in f.items() if k != "total"}) for f in filas]
    return {"datos": datos, "paginacion": {"pagina": pagina, "tamano": tamano, "total": total}}


def _comunes(tipo_delito_id, desde, hasta, extra_sql, params):
    if desde and hasta and desde > hasta:
        raise ErrorApi(422, "RANGO_FECHAS_INVALIDO", "'desde' no puede ser posterior a 'hasta'")
    if tipo_delito_id:
        extra_sql.append("r.tipo_delito_id = %(tipo)s")
        params["tipo"] = tipo_delito_id
    if desde:
        extra_sql.append("r.fecha_hecho >= %(desde)s")
        params["desde"] = desde
    if hasta:
        extra_sql.append("r.fecha_hecho <= %(hasta)s")
        params["hasta"] = hasta


@app.get("/api/v1/reportes", tags=["Reportes"])
def buscar_reportes(
    latitud: Optional[float] = Query(None, ge=-90, le=90),
    longitud: Optional[float] = Query(None, ge=-180, le=180),
    radio_m: Optional[int] = Query(None, ge=1, le=5000, description="Radio en metros (máx. 5000)"),
    colonia_id: Optional[int] = None,
    bbox: Optional[str] = Query(None, description="min_lon,min_lat,max_lon,max_lat"),
    tipo_delito_id: Optional[int] = None,
    desde: Optional[datetime] = None,
    hasta: Optional[datetime] = None,
    estado: Literal["PENDIENTE", "PUBLICADO", "RECHAZADO", "DUPLICADO"] = "PUBLICADO",
    pagina: int = Query(1, ge=1),
    tamano: int = Query(50, ge=1, le=200),
):
    extra_sql, params = [], {"estado": estado}
    radio_args = (latitud, longitud, radio_m)
    if any(v is not None for v in radio_args):
        if not all(v is not None for v in radio_args):
            raise ErrorApi(422, "RADIO_INCOMPLETO", "Para consultar por radio envía latitud, longitud y radio_m")
        extra_sql.append("ST_DWithin(r.ubicacion::geography, ST_SetSRID(ST_MakePoint(%(lon)s, %(lat)s), 4326)::geography, %(radio)s)")
        params.update({"lon": longitud, "lat": latitud, "radio": radio_m})
    if colonia_id:
        extra_sql.append("r.colonia_id = %(colonia)s")
        params["colonia"] = colonia_id
    if bbox:
        try:
            x1, y1, x2, y2 = parsear_bbox(bbox)
        except ValueError as e:
            raise ErrorApi(422, "BBOX_INVALIDO", "El parámetro bbox no es válido", str(e))
        extra_sql.append("r.ubicacion && ST_MakeEnvelope(%(x1)s, %(y1)s, %(x2)s, %(y2)s, 4326)")
        params.update({"x1": x1, "y1": y1, "x2": x2, "y2": y2})
    _comunes(tipo_delito_id, desde, hasta, extra_sql, params)
    return _consultar(extra_sql, params, pagina, tamano)


@app.post("/api/v1/reportes/buscar", tags=["Reportes"])
def buscar_por_poligono(b: BusquedaIn):
    if b.poligono.get("type") != "Polygon":
        raise ErrorApi(422, "POLIGONO_INVALIDO", "El polígono debe ser GeoJSON de tipo Polygon")
    extra_sql, params = [], {"estado": b.estado}
    extra_sql.append("ST_Covers(ST_SetSRID(ST_GeomFromGeoJSON(%(geojson)s), 4326), r.ubicacion)")
    params["geojson"] = json.dumps(b.poligono)
    _comunes(b.tipo_delito_id, b.desde, b.hasta, extra_sql, params)
    try:
        return _consultar(extra_sql, params, b.pagina, b.tamano)
    except Exception as e:
        if "geometry" in str(e).lower() or "geojson" in str(e).lower():
            raise ErrorApi(422, "POLIGONO_INVALIDO", "El polígono no es una geometría válida")
        raise


# ---------- Geocodificación inversa (RF-01.5) ----------
@app.get("/api/v1/geo/colonia", tags=["Geografía"])
def colonia_de_coordenada(latitud: float = Query(ge=-90, le=90), longitud: float = Query(ge=-180, le=180)):
    with conexion() as con:
        fila = con.execute(
            "SELECT id, clave, nombre, ageb, fuente FROM colonias WHERE ST_Covers(geom, ST_SetSRID(ST_MakePoint(%s, %s), 4326)) LIMIT 1",
            (longitud, latitud),
        ).fetchone()
    if not fila:
        raise ErrorApi(404, "COLONIA_NO_ENCONTRADA", "No hay colonia registrada para esa coordenada")
    return fila
