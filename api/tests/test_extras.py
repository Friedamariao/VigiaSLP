"""Pruebas de orden (RF-01.6) y de las interfaces con E8 (estados), E5 (ingesta), E9 (roles) y estadísticas."""
import uuid
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient

from app.main import app

LAT, LON = 22.15, -100.975


@pytest.fixture(scope="module")
def cliente():
    c = TestClient(app)
    if c.get("/health").status_code != 200:
        pytest.skip("No hay base de datos disponible")
    return c


@pytest.fixture(scope="module")
def tipo(cliente):
    return next(t["id"] for t in cliente.get("/api/v1/tipos-delito").json()["datos"] if not t["es_vfs"])


def hace(dias):
    return (datetime.now(timezone.utc) - timedelta(days=dias)).isoformat()


def nuevo_reporte(cliente, tipo, dias=1, lat=LAT, lon=LON):
    r = cliente.post("/api/v1/reportes", json={"tipo_delito_id": tipo, "fecha_hecho": hace(dias), "latitud": lat, "longitud": lon})
    assert r.status_code == 201
    return r.json()["folio"]


def test_orden_por_fecha_y_distancia(cliente, tipo):
    for f in (nuevo_reporte(cliente, tipo, 3), nuevo_reporte(cliente, tipo, 2)):
        cliente.patch(f"/api/v1/reportes/{f}/estado", json={"estado_nuevo": "PUBLICADO"})
    base = {"latitud": LAT, "longitud": LON, "radio_m": 500, "tamano": 200}
    desc = cliente.get("/api/v1/reportes", params={**base, "orden": "fecha_desc"}).json()["datos"]
    asc = cliente.get("/api/v1/reportes", params={**base, "orden": "fecha_asc"}).json()["datos"]
    assert [d["folio"] for d in desc] == [d["folio"] for d in reversed(asc)]
    assert cliente.get("/api/v1/reportes", params={**base, "orden": "distancia"}).status_code == 200
    assert cliente.get("/api/v1/reportes", params={"orden": "distancia"}).json()["code"] == "ORDEN_INVALIDO"
    assert cliente.get("/api/v1/reportes", params={"orden": "azar"}).json()["code"] == "VALIDACION_FALLIDA"
    poligono = {"type": "Polygon", "coordinates": [[[-101.1, 22.0], [-100.9, 22.0], [-100.9, 22.3], [-101.1, 22.3], [-101.1, 22.0]]]}
    assert cliente.post("/api/v1/reportes/buscar", json={"poligono": poligono, "orden": "fecha_asc"}).status_code == 200


def test_cambio_de_estado_e_historial(cliente, tipo):
    f = nuevo_reporte(cliente, tipo)
    r = cliente.patch(f"/api/v1/reportes/{f}/estado", json={"estado_nuevo": "PUBLICADO", "motivo": "Verificado"})
    assert r.status_code == 200 and r.json()["estado_anterior"] == "PENDIENTE"
    assert cliente.patch(f"/api/v1/reportes/{f}/estado", json={"estado_nuevo": "DUPLICADO"}).json()["code"] == "TRANSICION_INVALIDA"
    assert cliente.patch("/api/v1/reportes/VIG-0000-XXXXXXXX/estado", json={"estado_nuevo": "PUBLICADO"}).status_code == 404
    h = cliente.get(f"/api/v1/reportes/{f}/historial").json()["datos"]
    assert [x["estado_nuevo"] for x in h] == ["PENDIENTE", "PUBLICADO"]
    assert cliente.get("/api/v1/reportes/VIG-0000-XXXXXXXX/historial").status_code == 404


def test_estadisticas(cliente):
    for g in ("tipo", "colonia", "mes"):
        r = cliente.get("/api/v1/estadisticas", params={"agrupar_por": g})
        assert r.status_code == 200 and "oficial" in r.json()["aviso"] and r.json()["datos"]
    assert cliente.get("/api/v1/estadisticas", params={"agrupar_por": "x"}).status_code == 422


def test_ingesta_idempotente(cliente, tipo):
    ref = "t-" + uuid.uuid4().hex[:8]
    cuerpo = {"fuente": "prueba", "registros": [
        {"tipo_delito_id": tipo, "fecha_hecho": hace(5), "latitud": LAT, "longitud": LON, "referencia_externa": ref},
        {"tipo_delito_id": tipo, "fecha_hecho": hace(5), "latitud": 10.0, "longitud": -80.0},
        {"tipo_delito_id": 999999, "fecha_hecho": hace(5), "latitud": LAT, "longitud": LON}]}
    r = cliente.post("/api/v1/ingesta/reportes", json=cuerpo).json()
    assert r["insertados"] == 1 and {x["code"] for x in r["rechazados"]} == {"UBICACION_FUERA_DE_COBERTURA", "TIPO_INVALIDO"}
    assert cliente.post("/api/v1/ingesta/reportes", json=cuerpo).json()["duplicados"] == 1
    assert cliente.post("/api/v1/ingesta/reportes", json={"fuente": "x", "registros": []}).status_code == 422


def test_roles_e9(cliente, tipo, monkeypatch):
    monkeypatch.setenv("AUTH_MODO", "cabecera")
    f = nuevo_reporte(cliente, tipo)
    ruta = f"/api/v1/reportes/{f}/estado"
    cuerpo = {"estado_nuevo": "RECHAZADO"}
    assert cliente.patch(ruta, json=cuerpo).json()["code"] == "NO_AUTENTICADO"
    assert cliente.patch(ruta, json=cuerpo, headers={"x-rol": "ciudadano"}).json()["code"] == "ROL_INSUFICIENTE"
    assert cliente.patch(ruta, json=cuerpo, headers={"x-rol": "moderador"}).status_code == 200
    assert cliente.delete("/api/v1/tipos-delito/1", headers={"x-rol": "moderador"}).status_code == 403
    assert cliente.post("/api/v1/ingesta/reportes", json={"fuente": "x", "registros": []}, headers={"x-rol": "ingesta"}).status_code == 422


def test_suscripciones(cliente, tipo):
    antes = hace(0.001)
    s = cliente.post("/api/v1/suscripciones", json={"identificador_externo": "chat-" + uuid.uuid4().hex[:6], "latitud": LAT, "longitud": LON, "radio_m": 1000})
    assert s.status_code == 201
    sid = s.json()["id"]
    f = nuevo_reporte(cliente, tipo)
    cliente.patch(f"/api/v1/reportes/{f}/estado", json={"estado_nuevo": "PUBLICADO"})
    nov = cliente.get(f"/api/v1/suscripciones/{sid}/novedades", params={"desde": antes}).json()["datos"]
    assert any(n["folio"] == f for n in nov)
    assert cliente.post("/api/v1/suscripciones", json={"identificador_externo": "abc", "latitud": 10, "longitud": -80, "radio_m": 500}).status_code == 422
    assert cliente.post("/api/v1/suscripciones", json={"identificador_externo": "abc", "latitud": LAT, "longitud": LON, "radio_m": 5}).json()["code"] == "VALIDACION_FALLIDA"
    assert cliente.delete(f"/api/v1/suscripciones/{sid}").status_code == 204
    assert cliente.delete(f"/api/v1/suscripciones/{sid}").status_code == 404
    assert cliente.get(f"/api/v1/suscripciones/{sid}/novedades", params={"desde": antes}).status_code == 404
