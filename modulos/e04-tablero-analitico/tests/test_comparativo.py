def test_comparativo_responde_ok(client):
    resp = client.get("/api/v1/analitica/comparativo")
    assert resp.status_code == 200
    body = resp.json()
    assert "datos" in body
    assert "nota" in body
    assert "disclaimer" in body


def test_comparativo_nota_sesnsp(client):
    resp = client.get("/api/v1/analitica/comparativo")
    body = resp.json()
    assert "SESNSP" in body["nota"]
    assert "municipal" in body["nota"]


def test_comparativo_estructura_datos(client):
    resp = client.get("/api/v1/analitica/comparativo")
    body = resp.json()
    for punto in body["datos"]:
        assert "mes" in punto
        assert "ciudadano" in punto
        assert "oficial" in punto


def test_comparativo_filtro_tipo(client):
    resp = client.get("/api/v1/analitica/comparativo?tipo_delito=RTR")
    assert resp.status_code == 200
    body = resp.json()
    for punto in body["datos"]:
        assert punto["tipo_delito"] == "RTR"


def test_resumen_responde_ok(client):
    resp = client.get("/api/v1/analitica/resumen")
    assert resp.status_code == 200
    body = resp.json()
    assert "total_reportes" in body
    assert "reportes_semana" in body
    assert "tipo_mas_frecuente" in body
    assert "colonia_mas_reportes" in body
    assert "tendencia" in body
    assert "disclaimer" in body


def test_resumen_tipo_frecuente_no_vfs(client):
    resp = client.get("/api/v1/analitica/resumen")
    body = resp.json()
    assert body["tipo_mas_frecuente"]["clave"] != "VFS"


def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["modulo"] == "e04-analitica"
