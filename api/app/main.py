"""API central de VigíaSLP (E01) · RF-01.1 a RF-01.8 e interfaces con E5 (ingesta), E8 (estados) y E9 (roles)."""
import json
import logging
import os
import time
import uuid
from datetime import datetime, timezone
from typing import Literal, Optional

from fastapi import Depends, FastAPI, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from psycopg.errors import UniqueViolation
from starlette.exceptions import HTTPException as StarletteHTTPException

from .db import conexion
from .util import dentro_cobertura, generar_folio, ofuscar, parsear_bbox

VERSION = "0.2.0"
logger = logging.getLogger("vigiaslp.api")
logging.basicConfig(level=os.environ.get("API_LOG_LEVEL", "INFO").upper(), format="%(message)s")

app = FastAPI(
    title="VigíaSLP · API central",
    version=VERSION,
    description="API REST del módulo E01. Coordenadas WGS 84 (EPSG:4326). Los reportes ciudadanos no son cifras oficiales.",
)
ESTADOS = ("PENDIENTE", "PUBLICADO", "RECHAZADO", "DUPLICADO")
ORIENTACION_VFS = "Este tipo de caso no se publica en el mapa. Si estás en peligro llama al 911; para orientación y denuncia anónima, al 089."


# ---------- Roles (interfaz con E9) ----------
# AUTH_MODO=off (por defecto, desarrollo) | cabecera: el middleware de E9 valida el token y envía X-Rol.
def requiere(*roles):
    def verificar(request: Request):
        if os.environ.get("AUTH_MODO", "off") != "cabecera":
            return None
        rol = request.headers.get("x-rol")
        if not rol:
            raise ErrorApi(401, "NO_AUTENTICADO", "Se requiere autenticación")
        if rol not in roles and rol != "administrador":
            raise ErrorApi(403, "ROL_INSUFICIENTE", "El rol no tiene permiso para esta operación", f"rol={rol}")
        return rol
    return verificar


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
    canal_origen: Literal["web", "telegram"] = "web"
    fecha_hecho: datetime
    latitud: float = Field(ge=-90, le=90)
    longitud: float = Field(ge=-180, le=180)


ORDENES = {"fecha_desc": "r.fecha_hecho DESC, r.id DESC", "fecha_asc": "r.fecha_hecho ASC, r.id ASC"}
Orden = Literal["fecha_desc", "fecha_asc", "distancia"]
TRANSICIONES = {"PENDIENTE": ("PUBLICADO", "RECHAZADO", "DUPLICADO"), "PUBLICADO": ("RECHAZADO",), "RECHAZADO": ("PENDIENTE",), "DUPLICADO": ()}


class CambioEstadoIn(BaseModel):
    estado_nuevo: Literal["PENDIENTE", "PUBLICADO", "RECHAZADO", "DUPLICADO"]
    motivo: Optional[str] = Field(default=None, max_length=300)


class RegistroIngesta(BaseModel):
    tipo_delito_id: int = Field(gt=0)
    fecha_hecho: datetime
    latitud: float = Field(ge=-90, le=90)
    longitud: float = Field(ge=-180, le=180)
    descripcion: Optional[str] = Field(default=None, max_length=500)
    referencia_externa: Optional[str] = Field(default=None, max_length=120)


class IngestaIn(BaseModel):
    fuente: str = Field(min_length=2, max_length=60)
    registros: list[RegistroIngesta] = Field(min_length=1, max_length=1000)


class BusquedaIn(BaseModel):
    poligono: dict = Field(description="GeoJSON de tipo Polygon (longitud, latitud)")
    tipo_delito_id: Optional[int] = None
    desde: Optional[datetime] = None
    hasta: Optional[datetime] = None
    estado: Literal["PENDIENTE", "PUBLICADO", "RECHAZADO", "DUPLICADO"] = "PUBLICADO"
    orden: Literal["fecha_desc", "fecha_asc"] = "fecha_desc"
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
def crear_tipo(t: TipoDelitoIn, _rol=Depends(requiere("administrador"))):
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
def baja_tipo(tipo_id: int, _rol=Depends(requiere("administrador"))):
    with conexion() as con:
        fila = con.execute("UPDATE tipos_delito SET activo = false WHERE id = %s RETURNING id", (tipo_id,)).fetchone()
    if not fila:
        raise ErrorApi(404, "TIPO_NO_ENCONTRADO", "El tipo de delito no existe")


# ---------- Reportes (RF-01.2) ----------
def _publico(fila):
    dec = int(os.environ.get("OFUSCACION_DECIMALES", "3"))
    fila["latitud"], fila["longitud"] = ofuscar(fila["latitud"], dec), ofuscar(fila["longitud"], dec)
    return fila


SELECT_REPORTE = """SELECT r.folio, r.estado, r.descripcion, r.canal_origen, r.fecha_hecho, r.creado_en,
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
                        """INSERT INTO reportes (folio, tipo_delito_id, descripcion, canal_origen, fecha_hecho, ubicacion, colonia_id)
                           VALUES (%(f)s, %(t)s, %(d)s, %(canal)s, %(fh)s, ST_SetSRID(ST_MakePoint(%(lon)s, %(lat)s), 4326),
                                   (SELECT id FROM colonias WHERE ST_Covers(geom, ST_SetSRID(ST_MakePoint(%(lon)s, %(lat)s), 4326)) LIMIT 1))
                           RETURNING id, folio""",
                        {"f": folio, "t": r.tipo_delito_id, "d": r.descripcion, "canal": r.canal_origen, "fh": fecha, "lon": r.longitud, "lat": r.latitud},
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
def _consultar(extra_sql, params, pagina, tamano, orden="fecha_desc"):
    cond = ["r.estado = %(estado)s"] + extra_sql
    if orden == "distancia":
        if "lon" not in params:
            raise ErrorApi(422, "ORDEN_INVALIDO", "El orden por distancia requiere consulta por radio")
        orden_sql = "ST_Distance(r.ubicacion::geography, ST_SetSRID(ST_MakePoint(%(lon)s, %(lat)s), 4326)::geography), r.id"
    else:
        orden_sql = ORDENES[orden]
    sql = (SELECT_REPORTE + ", COUNT(*) OVER() AS total" + FROM_REPORTE + " WHERE " + " AND ".join(cond)
           + " ORDER BY " + orden_sql + " LIMIT %(limite)s OFFSET %(desplazamiento)s")
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
    orden: Orden = "fecha_desc",
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
    return _consultar(extra_sql, params, pagina, tamano, orden)


@app.post("/api/v1/reportes/buscar", tags=["Reportes"])
def buscar_por_poligono(b: BusquedaIn):
    if b.poligono.get("type") != "Polygon":
        raise ErrorApi(422, "POLIGONO_INVALIDO", "El polígono debe ser GeoJSON de tipo Polygon")
    extra_sql, params = [], {"estado": b.estado}
    extra_sql.append("ST_Covers(ST_SetSRID(ST_GeomFromGeoJSON(%(geojson)s), 4326), r.ubicacion)")
    params["geojson"] = json.dumps(b.poligono)
    _comunes(b.tipo_delito_id, b.desde, b.hasta, extra_sql, params)
    try:
        return _consultar(extra_sql, params, b.pagina, b.tamano, b.orden)
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


# ---------- Interfaz con E8: estados del reporte ----------
@app.patch("/api/v1/reportes/{folio}/estado", tags=["Moderación (E8)"])
def cambiar_estado(folio: str, c: CambioEstadoIn, _rol=Depends(requiere("moderador"))):
    with conexion() as con:
        fila = con.execute("SELECT id, estado FROM reportes WHERE folio = %s FOR UPDATE", (folio,)).fetchone()
        if not fila:
            raise ErrorApi(404, "REPORTE_NO_ENCONTRADO", "No existe un reporte con ese folio")
        if c.estado_nuevo not in TRANSICIONES[fila["estado"]]:
            raise ErrorApi(409, "TRANSICION_INVALIDA", "La transición de estado no está permitida", f"{fila['estado']} -> {c.estado_nuevo}")
        con.execute("UPDATE reportes SET estado = %s, actualizado_en = now() WHERE id = %s", (c.estado_nuevo, fila["id"]))
        con.execute("INSERT INTO historial_estado_reporte (reporte_id, estado_anterior, estado_nuevo, motivo) VALUES (%s,%s,%s,%s)",
                    (fila["id"], fila["estado"], c.estado_nuevo, c.motivo))
    return {"folio": folio, "estado_anterior": fila["estado"], "estado": c.estado_nuevo}


@app.get("/api/v1/reportes/{folio}/historial", tags=["Moderación (E8)"])
def historial_estado(folio: str, _rol=Depends(requiere("moderador"))):
    with conexion() as con:
        r = con.execute("SELECT id FROM reportes WHERE folio = %s", (folio,)).fetchone()
        if not r:
            raise ErrorApi(404, "REPORTE_NO_ENCONTRADO", "No existe un reporte con ese folio")
        filas = con.execute("SELECT estado_anterior, estado_nuevo, motivo, cambiado_en FROM historial_estado_reporte WHERE reporte_id = %s ORDER BY id", (r["id"],)).fetchall()
    return {"folio": folio, "datos": filas}


# ---------- Estadísticas agregadas (para E4) ----------
@app.get("/api/v1/estadisticas", tags=["Estadísticas"])
def estadisticas(agrupar_por: Literal["tipo", "colonia", "mes"] = "tipo", desde: Optional[datetime] = None, hasta: Optional[datetime] = None,
                 estado: Literal["PENDIENTE", "PUBLICADO", "RECHAZADO", "DUPLICADO"] = "PUBLICADO"):
    extra, params = [], {"estado": estado}
    _comunes(None, desde, hasta, extra, params)
    grupos = {"tipo": ("t.codigo", "t.subtipo"), "colonia": ("COALESCE(c.clave,'SIN_COLONIA')", "COALESCE(c.nombre,'Sin colonia')"),
              "mes": ("to_char(r.fecha_hecho,'YYYY-MM')", "to_char(r.fecha_hecho,'YYYY-MM')")}
    clave, etiqueta = grupos[agrupar_por]
    sql = (f"SELECT {clave} AS clave, {etiqueta} AS etiqueta, COUNT(*) AS total" + FROM_REPORTE
           + " WHERE r.estado = %(estado)s" + "".join(" AND " + e for e in extra) + " GROUP BY 1, 2 ORDER BY total DESC, 1")
    with conexion() as con:
        filas = con.execute(sql, params).fetchall()
    return {"agrupar_por": agrupar_por, "datos": filas, "aviso": "Cifras de reportes ciudadanos; no constituyen estadística oficial."}


# ---------- Interfaz con E5: ingesta de datos externos ----------
@app.post("/api/v1/ingesta/reportes", tags=["Ingesta (E5)"])
def ingestar(i: IngestaIn, _rol=Depends(requiere("ingesta"))):
    insertados, duplicados, rechazados = 0, 0, []
    with conexion() as con:
        tipos = {t["id"]: t for t in con.execute("SELECT id, activo FROM tipos_delito").fetchall()}
        for n, r in enumerate(i.registros):
            if not dentro_cobertura(r.latitud, r.longitud):
                rechazados.append({"indice": n, "code": "UBICACION_FUERA_DE_COBERTURA"})
                continue
            if r.tipo_delito_id not in tipos or not tipos[r.tipo_delito_id]["activo"]:
                rechazados.append({"indice": n, "code": "TIPO_INVALIDO"})
                continue
            fecha = r.fecha_hecho if r.fecha_hecho.tzinfo else r.fecha_hecho.replace(tzinfo=timezone.utc)
            fila = con.execute(
                """INSERT INTO reportes (folio, tipo_delito_id, descripcion, canal_origen, fuente, referencia_externa, fecha_hecho, ubicacion, estado, colonia_id)
                   VALUES (%(f)s, %(t)s, %(d)s, 'ingesta', %(fu)s, %(ref)s, %(fh)s, ST_SetSRID(ST_MakePoint(%(lon)s, %(lat)s), 4326), 'PUBLICADO',
                           (SELECT id FROM colonias WHERE ST_Covers(geom, ST_SetSRID(ST_MakePoint(%(lon)s, %(lat)s), 4326)) LIMIT 1))
                   ON CONFLICT (fuente, referencia_externa) WHERE referencia_externa IS NOT NULL DO NOTHING RETURNING id""",
                {"f": generar_folio(), "t": r.tipo_delito_id, "d": r.descripcion, "fu": i.fuente, "ref": r.referencia_externa, "fh": fecha, "lon": r.longitud, "lat": r.latitud},
            ).fetchone()
            if not fila:
                duplicados += 1
                continue
            con.execute("INSERT INTO historial_estado_reporte (reporte_id, estado_anterior, estado_nuevo, motivo) VALUES (%s, NULL, 'PUBLICADO', %s)", (fila["id"], f"Ingesta externa: {i.fuente}"))
            insertados += 1
    return {"fuente": i.fuente, "insertados": insertados, "duplicados": duplicados, "rechazados": rechazados}


# ---------- Interfaz con E7: suscripciones a zonas ----------
class SuscripcionIn(BaseModel):
    canal: Literal["telegram", "web"] = "telegram"
    identificador_externo: str = Field(min_length=3, max_length=120)
    latitud: float = Field(ge=-90, le=90)
    longitud: float = Field(ge=-180, le=180)
    radio_m: int = Field(ge=100, le=5000)


@app.post("/api/v1/suscripciones", status_code=201, tags=["Suscripciones (E7)"])
def crear_suscripcion(s: SuscripcionIn, _rol=Depends(requiere("bot", "ciudadano"))):
    if not dentro_cobertura(s.latitud, s.longitud):
        raise ErrorApi(422, "UBICACION_FUERA_DE_COBERTURA", "La ubicación está fuera de San Luis Potosí")
    with conexion() as con:
        fila = con.execute(
            """INSERT INTO suscripciones (canal, identificador_externo, centro, radio_m)
               VALUES (%s, %s, ST_SetSRID(ST_MakePoint(%s, %s), 4326), %s) RETURNING id""",
            (s.canal, s.identificador_externo, s.longitud, s.latitud, s.radio_m)).fetchone()
    return {"id": fila["id"], "radio_m": s.radio_m, "activa": True}


@app.get("/api/v1/suscripciones", tags=["Suscripciones (E7)"])
def listar_suscripciones(identificador_externo: str = Query(min_length=3), _rol=Depends(requiere("bot", "ciudadano"))):
    with conexion() as con:
        filas = con.execute(
            "SELECT id, canal, ST_Y(centro) AS latitud, ST_X(centro) AS longitud, radio_m, creada_en FROM suscripciones WHERE identificador_externo = %s AND activa ORDER BY id",
            (identificador_externo,)).fetchall()
    return {"datos": filas}


@app.delete("/api/v1/suscripciones/{suscripcion_id}", status_code=204, tags=["Suscripciones (E7)"])
def baja_suscripcion(suscripcion_id: int, _rol=Depends(requiere("bot", "ciudadano"))):
    with conexion() as con:
        fila = con.execute("UPDATE suscripciones SET activa = false WHERE id = %s AND activa RETURNING id", (suscripcion_id,)).fetchone()
    if not fila:
        raise ErrorApi(404, "SUSCRIPCION_NO_ENCONTRADA", "La suscripción no existe o ya fue cancelada")


@app.get("/api/v1/suscripciones/{suscripcion_id}/novedades", tags=["Suscripciones (E7)"])
def novedades_suscripcion(suscripcion_id: int, desde: datetime, _rol=Depends(requiere("bot"))):
    sql = (SELECT_REPORTE + FROM_REPORTE + " JOIN suscripciones s ON s.id = %(id)s AND s.activa"
           " WHERE r.estado = 'PUBLICADO' AND r.actualizado_en > %(desde)s"
           " AND ST_DWithin(r.ubicacion::geography, s.centro::geography, s.radio_m) ORDER BY r.actualizado_en DESC LIMIT 200")
    with conexion() as con:
        if not con.execute("SELECT 1 FROM suscripciones WHERE id = %s AND activa", (suscripcion_id,)).fetchone():
            raise ErrorApi(404, "SUSCRIPCION_NO_ENCONTRADA", "La suscripción no existe o ya fue cancelada")
        filas = con.execute(sql, {"id": suscripcion_id, "desde": desde}).fetchall()
    return {"datos": [_publico(f) for f in filas]}
