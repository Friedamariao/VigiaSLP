"""Pruebas automatizadas de autenticacion JWT y control de acceso RBAC (E09)."""
import uuid
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

from app.db import conexion
from app.main import app, password_hasher

LAT, LON = 22.15, -100.975


@pytest.fixture
def entorno_auth(monkeypatch):
    """Prepara JWT y una cuenta administradora aislada para cada prueba."""
    sufijo = uuid.uuid4().hex[:10]
    admin = "e09admin" + sufijo
    bootstrap = "e09boot" + sufijo
    contrasena = "ClaveAdmin_E09_2026!"

    monkeypatch.setenv("AUTH_MODO", "jwt")
    monkeypatch.setenv("JWT_SECRET_KEY", "clave-de-prueba-e09-de-al-menos-32-bytes-2026")
    monkeypatch.setenv("JWT_ACCESS_TOKEN_MINUTES", "30")
    monkeypatch.setenv("E09_BOOTSTRAP_ADMIN_USERNAME", bootstrap)
    monkeypatch.setenv("E09_BOOTSTRAP_ADMIN_PASSWORD", "Bootstrap_E09_2026!")

    with TestClient(app) as cliente:
        with conexion() as con:
            con.execute(
                "INSERT INTO usuarios (usuario, password_hash, rol) VALUES (%s, %s, 'administrador')",
                (admin, password_hasher.hash(contrasena)),
            )
        try:
            yield cliente, admin, contrasena, bootstrap
        finally:
            with conexion() as con:
                con.execute(
                    "DELETE FROM usuarios WHERE usuario IN (%s, %s, %s)",
                    (admin, bootstrap, "e09mod" + sufijo),
                )


def iniciar(cliente, usuario, contrasena):
    return cliente.post(
        "/api/v1/auth/login",
        json={"usuario": usuario, "contrasena": contrasena},
    )


def test_login_valido_devuelve_token_jwt(entorno_auth):
    cliente, admin, contrasena, _ = entorno_auth
    respuesta = iniciar(cliente, admin, contrasena)

    assert respuesta.status_code == 200
    datos = respuesta.json()
    assert datos["token_type"] == "bearer"
    assert datos["rol"] == "administrador"
    assert datos["expires_in"] == 1800
    assert isinstance(datos["access_token"], str) and len(datos["access_token"]) > 20


def test_login_rechaza_credenciales_incorrectas(entorno_auth):
    cliente, admin, _, _ = entorno_auth
    respuesta = iniciar(cliente, admin, "ContrasenaIncorrecta_2026!")

    assert respuesta.status_code == 401
    assert respuesta.json()["code"] == "CREDENCIALES_INVALIDAS"


def test_rbac_admin_y_moderador(entorno_auth):
    cliente, admin, contrasena, _ = entorno_auth
    sufijo = admin.removeprefix("e09admin")
    moderador = "e09mod" + sufijo
    clave_moderador = "ClaveModerador_E09_2026!"

    # Sin token, las operaciones protegidas deben rechazarse.
    sin_token = cliente.get("/api/v1/reportes/VIG-0000-NOEXISTE/historial")
    assert sin_token.status_code == 401
    assert sin_token.json()["code"] == "NO_AUTENTICADO"

    # El administrador puede crear una cuenta de moderador.
    login_admin = iniciar(cliente, admin, contrasena)
    assert login_admin.status_code == 200
    token_admin = login_admin.json()["access_token"]
    creado = cliente.post(
        "/api/v1/auth/usuarios",
        headers={"Authorization": f"Bearer {token_admin}"},
        json={"usuario": moderador, "contrasena": clave_moderador, "rol": "moderador"},
    )
    assert creado.status_code == 201
    assert creado.json()["rol"] == "moderador"

    # El moderador puede consultar el historial, pero no crear usuarios.
    login_mod = iniciar(cliente, moderador, clave_moderador)
    assert login_mod.status_code == 200
    token_mod = login_mod.json()["access_token"]
    headers_mod = {"Authorization": f"Bearer {token_mod}"}

    tipos = cliente.get("/api/v1/tipos-delito").json()["datos"]
    tipo = next(t["id"] for t in tipos if not t["es_vfs"])
    reporte = cliente.post(
        "/api/v1/reportes",
        json={
            "tipo_delito_id": tipo,
            "descripcion": "Prueba automatizada E09",
            "fecha_hecho": datetime.now(timezone.utc).isoformat(),
            "latitud": LAT,
            "longitud": LON,
        },
    )
    assert reporte.status_code == 201

    historial = cliente.get(
        f"/api/v1/reportes/{reporte.json()['folio']}/historial",
        headers=headers_mod,
    )
    assert historial.status_code == 200
    assert historial.json()["datos"]

    prohibido = cliente.post(
        "/api/v1/auth/usuarios",
        headers=headers_mod,
        json={"usuario": "e09usuario" + sufijo, "contrasena": "ClaveUsuario_E09_2026!", "rol": "ciudadano"},
    )
    assert prohibido.status_code == 403
    assert prohibido.json()["code"] == "ROL_INSUFICIENTE"


def test_token_invalido_es_rechazado(entorno_auth):
    cliente, _, _, _ = entorno_auth
    respuesta = cliente.get(
        "/api/v1/reportes/VIG-0000-NOEXISTE/historial",
        headers={"Authorization": "Bearer token-falso"},
    )

    assert respuesta.status_code == 401
    assert respuesta.json()["code"] == "TOKEN_INVALIDO"
