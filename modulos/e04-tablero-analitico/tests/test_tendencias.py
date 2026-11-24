def test_tendencias_responde_ok(client):
    resp = client.get("/api/v1/analitica/tendencias")
    assert resp.status_code == 200
    body = resp.json()
    assert "datos" in body
    assert "disclaimer" in body
    assert body["periodo"] == "semana"


def test_tendencias_periodo_mes(client):
    resp = client.get("/api/v1/analitica/tendencias?periodo=mes")
    assert resp.status_code == 200
    body = resp.json()
    assert body["periodo"] == "mes"
    for punto in body["datos"]:
        assert len(punto["fecha"]) == 7


def test_tendencias_filtro_tipo(client):
    resp = client.get("/api/v1/analitica/tendencias?tipo_delito=RTR")
    assert resp.status_code == 200
    body = resp.json()
    for punto in body["datos"]:
        for tipo in punto["por_tipo"]:
            assert tipo == "RTR"


def test_tendencias_excluye_vfs(client):
    resp = client.get("/api/v1/analitica/tendencias?periodo=mes")
    body = resp.json()
    for punto in body["datos"]:
        assert "VFS" not in punto["por_tipo"]


def test_tendencias_incluye_disclaimer(client):
    resp = client.get("/api/v1/analitica/tendencias")
    body = resp.json()
    assert "no constituyen una cifra oficial" in body["disclaimer"]


def test_tipos_delito_responde_ok(client):
    resp = client.get("/api/v1/analitica/tipos-delito")
    assert resp.status_code == 200
    body = resp.json()
    assert "tipos" in body
    claves = [t["clave"] for t in body["tipos"]]
    assert "VFS" not in claves


def test_tipos_delito_orden_descendente(client):
    resp = client.get("/api/v1/analitica/tipos-delito")
    body = resp.json()
    totales = [t["total"] for t in body["tipos"]]
    assert totales == sorted(totales, reverse=True)
