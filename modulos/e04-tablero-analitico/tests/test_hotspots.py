from backend.config import UMBRAL_MINIMO_REPORTES


def test_hotspots_responde_ok(client):
    resp = client.get("/api/v1/analitica/hotspots")
    assert resp.status_code == 200
    body = resp.json()
    assert "hotspots" in body
    assert "disclaimer" in body


def test_hotspots_umbral_minimo(client):
    resp = client.get("/api/v1/analitica/hotspots")
    body = resp.json()
    for h in body["hotspots"]:
        assert h["total_reportes"] >= UMBRAL_MINIMO_REPORTES


def test_hotspots_orden_descendente(client):
    resp = client.get("/api/v1/analitica/hotspots")
    body = resp.json()
    totales = [h["total_reportes"] for h in body["hotspots"]]
    assert totales == sorted(totales, reverse=True)


def test_hotspots_limite(client):
    resp = client.get("/api/v1/analitica/hotspots?limite=3")
    body = resp.json()
    assert len(body["hotspots"]) <= 3


def test_hotspots_contiene_coordenadas(client):
    resp = client.get("/api/v1/analitica/hotspots")
    body = resp.json()
    for h in body["hotspots"]:
        assert "lat" in h
        assert "lng" in h


def test_hotspots_filtro_tipo(client):
    resp = client.get("/api/v1/analitica/hotspots?tipo_delito=RTR")
    assert resp.status_code == 200
    body = resp.json()
    assert isinstance(body["hotspots"], list)
