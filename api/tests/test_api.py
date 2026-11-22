"""Pruebas de la API contra una base PostGIS real (se omiten si no hay conexión)."""
import uuid
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient

from app.main import app

LAT, LON = 22.15, -100.975  # dentro de la cuadrícula provisional


@pytest.fixture(scope="module")
def cliente():
    c = TestClient(app)
    if c.get("/health").status_code != 200:
        pytest.skip("No hay base de datos disponible")
    return c


@pytest.fixture(scope="module")
def tipos(cliente):
    datos = cliente.get("/api/v1/tipos-delito").json()["datos"]
    normal = next(t for t in datos if not t["es_vfs"])
    vfs = next(t for t in datos if t["es_vfs"])
    return normal["id"], vfs["id"], datos


def hace(dias):
    return (datetime.now(timezone.utc) - timedelta(days=dias)).isoformat()


def reporte(tipo_id, **extra):
    base = {"tipo_delito_id": tipo_id, "descripcion": "Prueba sintética", "fecha_hecho": hace(1), "latitud": LAT, "longitud": LON}
    base.update(extra)
    return base


def test_salud_y_version(cliente):
    assert cliente.get("/health").json() == {"estado": "ok", "base_datos": "ok"}
    assert cliente.get("/version").json()["api"] == "v1"


def test_catalogo_tiene_tipos_y_marca_vfs(tipos):
    assert len(tipos[2]) >= 30
    assert all(not t["publicable_mapa"] for t in tipos[2] if t["es_vfs"])


def test_alta_duplicado_y_baja_logica_de_tipo(cliente):
    codigo = "TST-" + uuid.uuid4().hex[:6].upper()
    cuerpo = {"codigo": codigo, "categoria": "Pruebas", "tipo": "Prueba", "subtipo": "Tipo de prueba"}
    r = cliente.post("/api/v1/tipos-delito", json=cuerpo)
    assert r.status_code == 201
    assert cliente.post("/api/v1/tipos-delito", json=cuerpo).status_code == 409
    assert cliente.delete(f"/api/v1/tipos-delito/{r.json()['id']}").status_code == 204
    codigos = [t["codigo"] for t in cliente.get("/api/v1/tipos-delito").json()["datos"]]
    assert codigo not in codigos
    assert cliente.delete("/api/v1/tipos-delito/999999").status_code == 404


def test_alta_de_reporte_y_consulta_por_folio(cliente, tipos):
    r = cliente.post("/api/v1/reportes", json=reporte(tipos[0]))
    assert r.status_code == 201
    folio = r.json()["folio"]
    assert folio.startswith("VIG-") and r.json()["estado"] == "PENDIENTE"
    g = cliente.get(f"/api/v1/reportes/{folio}")
    assert g.status_code == 200
    assert g.json()["colonia"].startswith("Zona provisional")
    assert g.json()["latitud"] == round(LAT, 3)  # ubicación ofuscada
    assert cliente.get("/api/v1/reportes/VIG-0000-NOEXISTE").status_code == 404


def test_rechazos_del_alta(cliente, tipos):
    vfs = cliente.post("/api/v1/reportes", json=reporte(tipos[1]))
    assert vfs.status_code == 422 and vfs.json()["code"] == "TIPO_NO_PUBLICABLE"
    assert "089" in vfs.json()["detail"]
    assert vfs.headers["content-type"].startswith("application/problem+json")
    fuera = cliente.post("/api/v1/reportes", json=reporte(tipos[0], latitud=19.43, longitud=-99.13))
    assert fuera.json()["code"] == "UBICACION_FUERA_DE_COBERTURA"
    futura = cliente.post("/api/v1/reportes", json=reporte(tipos[0], fecha_hecho=(datetime.now(timezone.utc) + timedelta(days=2)).isoformat()))
    assert futura.json()["code"] == "FECHA_FUTURA"
    assert cliente.post("/api/v1/reportes", json=reporte(999999)).json()["code"] == "TIPO_INVALIDO"
    invalido = cliente.post("/api/v1/reportes", json={"tipo_delito_id": "x"})
    assert invalido.status_code == 422 and invalido.json()["code"] == "VALIDACION_FALLIDA"


def test_consulta_por_radio(cliente):
    r = cliente.get("/api/v1/reportes", params={"latitud": LAT, "longitud": LON, "radio_m": 3000, "tamano": 10})
    assert r.status_code == 200
    cuerpo = r.json()
    assert cuerpo["paginacion"]["total"] > 0 and len(cuerpo["datos"]) <= 10
    chico = cliente.get("/api/v1/reportes", params={"latitud": LAT, "longitud": LON, "radio_m": 50}).json()
    assert chico["paginacion"]["total"] <= cuerpo["paginacion"]["total"]
    assert cliente.get("/api/v1/reportes", params={"latitud": LAT}).json()["code"] == "RADIO_INCOMPLETO"


def test_consulta_por_colonia_bbox_y_filtros(cliente, tipos):
    col = cliente.get("/api/v1/geo/colonia", params={"latitud": LAT, "longitud": LON}).json()
    por_col = cliente.get("/api/v1/reportes", params={"colonia_id": col["id"]}).json()
    assert por_col["paginacion"]["total"] > 0
    assert all(d["colonia_id"] == col["id"] for d in por_col["datos"])
    bbox = cliente.get("/api/v1/reportes", params={"bbox": "-101.05,22.08,-100.90,22.20", "tamano": 5})
    assert bbox.status_code == 200 and bbox.json()["paginacion"]["total"] > 0
    assert cliente.get("/api/v1/reportes", params={"bbox": "1,2,3"}).json()["code"] == "BBOX_INVALIDO"
    reciente = cliente.get("/api/v1/reportes", params={"desde": hace(10), "tipo_delito_id": tipos[0]}).json()
    assert all(d["tipo_delito_id"] == tipos[0] for d in reciente["datos"])
    assert cliente.get("/api/v1/reportes", params={"desde": hace(1), "hasta": hace(5)}).json()["code"] == "RANGO_FECHAS_INVALIDO"


def test_consulta_por_poligono(cliente):
    poligono = {"type": "Polygon", "coordinates": [[[-101.05, 22.08], [-100.90, 22.08], [-100.90, 22.20], [-101.05, 22.20], [-101.05, 22.08]]]}
    r = cliente.post("/api/v1/reportes/buscar", json={"poligono": poligono, "tamano": 5})
    assert r.status_code == 200 and r.json()["paginacion"]["total"] > 0
    malo = cliente.post("/api/v1/reportes/buscar", json={"poligono": {"type": "Point", "coordinates": [0, 0]}})
    assert malo.json()["code"] == "POLIGONO_INVALIDO"


def test_geocodificacion_inversa(cliente):
    ok = cliente.get("/api/v1/geo/colonia", params={"latitud": LAT, "longitud": LON})
    assert ok.status_code == 200 and ok.json()["fuente"] == "provisional"
    assert cliente.get("/api/v1/geo/colonia", params={"latitud": 19.43, "longitud": -99.13}).status_code == 404
