import os
import sys
import tempfile

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Se fija ANTES de importar cualquier módulo de la app, para que toda la
# suite de pruebas use una única base de datos SQLite temporal y aislada
# de la base de datos de desarrollo (amassadera.db).
_db_fd, _db_path = tempfile.mkstemp(suffix=".db")
os.environ["DATABASE_URL"] = f"sqlite:///{_db_path}"

from fastapi.testclient import TestClient  # noqa: E402

from app import seed  # noqa: E402
from app.main import app  # noqa: E402

seed.run()


@pytest.fixture(scope="session")
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="session")
def admin_token(client):
    r = client.post(
        "/api/auth/login",
        json={"correo": "mauricio@laamassadera.com", "contrasena": "Amassadera2026"},
    )
    return r.json()["access_token"]


@pytest.fixture(scope="session")
def empleado_token(client):
    r = client.post(
        "/api/auth/login",
        json={"correo": "empleado@laamassadera.com", "contrasena": "Produccion2026"},
    )
    return r.json()["access_token"]
