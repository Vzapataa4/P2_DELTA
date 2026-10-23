"""Casos de prueba automatizados de Sprint 2 (HU-02, 06, 08, 11, 15, 17, 21).

Cada HU tiene mínimo dos pruebas: happy path y flujo alterno, y cada una
crea sus propios datos (nombres únicos) para no depender del orden de
ejecución ni del estado compartido de la base de datos de pruebas.
"""
from datetime import date, timedelta


def h(token):
    return {"Authorization": f"Bearer {token}"}


def _crear_insumo(client, token, nombre, cantidad, minimo=0, costo=1.0, unidad="gr"):
    r = client.post(
        "/api/insumos",
        headers=h(token),
        json={
            "nombre": nombre,
            "unidad": unidad,
            "cantidad_disponible": cantidad,
            "nivel_minimo": minimo,
            "costo_unitario": costo,
        },
    )
    assert r.status_code == 201, r.text
    return r.json()


def _crear_receta(client, token, nombre, insumos, precio=None):
    body = {
        "nombre": nombre,
        "insumos": [{"insumo_nombre": n, "cantidad_requerida": c} for n, c in insumos],
    }
    if precio is not None:
        body["precio_venta"] = precio
    r = client.post("/api/recetas", headers=h(token), json=body)
    assert r.status_code == 201, r.text
    return r.json()


def _vender(client, token, distribuidor, receta, cantidad):
    r = client.post(
        "/api/ventas",
        headers=h(token),
        json={"distribuidor_nombre": distribuidor, "receta_nombre": receta, "cantidad": cantidad},
    )
    assert r.status_code == 201, r.text
    return r.json()


# ---------- HU-02 Crear cuenta de empleado ----------

def test_hu02_admin_crea_empleado_que_puede_iniciar_sesion_happy_path(client, admin_token):
    r = client.post(
        "/api/auth/empleados",
        headers=h(admin_token),
        json={"nombre": "Ana Pérez", "correo": "ana@laamassadera.com", "contrasena": "ClaveSegura1"},
    )
    assert r.status_code == 201
    assert r.json()["rol"] == "empleado"
    login = client.post(
        "/api/auth/login", json={"correo": "ana@laamassadera.com", "contrasena": "ClaveSegura1"}
    )
    assert login.status_code == 200
    assert login.json()["rol"] == "empleado"


def test_hu02_correo_duplicado_y_empleado_sin_permiso_alterno(client, admin_token, empleado_token):
    datos = {"nombre": "Luis", "correo": "luis@laamassadera.com", "contrasena": "ClaveSegura1"}
    assert client.post("/api/auth/empleados", headers=h(admin_token), json=datos).status_code == 201
    # Dado un correo ya registrado, la segunda creación se rechaza.
    assert client.post("/api/auth/empleados", headers=h(admin_token), json=datos).status_code == 409
    # Un empleado no puede crear cuentas.
    r = client.post("/api/auth/empleados", headers=h(empleado_token), json={**datos, "correo": "x@x.com"})
    assert r.status_code == 403
    # Contraseña demasiado corta -> validación.
    corta = client.post(
        "/api/auth/empleados", headers=h(admin_token), json={**datos, "correo": "c@x.com", "contrasena": "123"}
    )
    assert corta.status_code == 422


# ---------- HU-06 Actualizar cantidad de insumo ----------

def test_hu06_actualizar_cantidad_cambia_el_nivel_happy_path(client, admin_token):
    ins = _crear_insumo(client, admin_token, "Insumo HU06 A", cantidad=10, minimo=100)
    assert ins["nivel"] == "bajo"
    r = client.patch(
        f"/api/insumos/{ins['id']}/cantidad", headers=h(admin_token), json={"cantidad_disponible": 500}
    )
    assert r.status_code == 200
    assert r.json()["cantidad_disponible"] == 500
    assert r.json()["nivel"] == "ok"


def test_hu06_cantidad_negativa_inexistente_y_rol_alterno(client, admin_token, empleado_token):
    ins = _crear_insumo(client, admin_token, "Insumo HU06 B", cantidad=50)
    url = f"/api/insumos/{ins['id']}/cantidad"
    assert client.patch(url, headers=h(admin_token), json={"cantidad_disponible": -5}).status_code == 422
    assert client.patch("/api/insumos/999999/cantidad", headers=h(admin_token), json={"cantidad_disponible": 5}).status_code == 404
    assert client.patch(url, headers=h(empleado_token), json={"cantidad_disponible": 5}).status_code == 403
    # Nada de lo anterior debió modificar la cantidad.
    actual = next(i for i in client.get("/api/insumos", headers=h(admin_token)).json() if i["id"] == ins["id"])
    assert actual["cantidad_disponible"] == 50


# ---------- HU-08 Consultar inventario (empleado) ----------

def test_hu08_empleado_consulta_inventario_happy_path(client, empleado_token):
    r = client.get("/api/insumos", headers=h(empleado_token))
    assert r.status_code == 200
    assert any(i["nombre"] == "Harina" for i in r.json())


def test_hu08_empleado_no_ve_informacion_financiera_ni_modifica_alterno(client, empleado_token):
    assert client.get("/api/dashboard", headers=h(empleado_token)).status_code == 403
    assert client.get("/api/ventas", headers=h(empleado_token)).status_code == 403
    assert client.get("/api/recetas/rentabilidad", headers=h(empleado_token)).status_code == 403
    r = client.post(
        "/api/insumos", headers=h(empleado_token), json={"nombre": "Colado", "cantidad_disponible": 1}
    )
    assert r.status_code == 403


# ---------- HU-11 Ver historial de ventas ----------

def test_hu11_historial_filtra_por_distribuidor_happy_path(client, admin_token):
    _crear_insumo(client, admin_token, "Insumo HU11", cantidad=10000)
    _crear_receta(client, admin_token, "Pan HU11", [("Insumo HU11", 10)], precio=100)
    _vender(client, admin_token, "Distribuidor HU11 Uno", "Pan HU11", 2)
    _vender(client, admin_token, "Distribuidor HU11 Dos", "Pan HU11", 3)
    r = client.get("/api/ventas", params={"distribuidor": "Distribuidor HU11 Uno"}, headers=h(admin_token))
    assert r.status_code == 200
    assert len(r.json()) == 1
    assert r.json()[0]["cantidad"] == 2


def test_hu11_rango_de_fechas_y_rango_invalido_alterno(client, admin_token):
    hoy = date.today()
    manana = hoy + timedelta(days=2)
    ayer = hoy - timedelta(days=2)
    # Rango en el futuro: no hay ventas, lista vacía (no error).
    futuro = client.get("/api/ventas", params={"desde": manana.isoformat()}, headers=h(admin_token))
    assert futuro.status_code == 200 and futuro.json() == []
    # Rango que incluye hoy: trae las ventas registradas hoy.
    incluye = client.get(
        "/api/ventas", params={"desde": ayer.isoformat(), "hasta": manana.isoformat()}, headers=h(admin_token)
    )
    assert incluye.status_code == 200
    # Rango invertido: error claro.
    malo = client.get(
        "/api/ventas", params={"desde": manana.isoformat(), "hasta": ayer.isoformat()}, headers=h(admin_token)
    )
    assert malo.status_code == 400


# ---------- HU-15 Ver rentabilidad por producto ----------

def test_hu15_rentabilidad_calcula_margen_y_ganancia_total_happy_path(client, admin_token):
    _crear_insumo(client, admin_token, "Insumo HU15", cantidad=10000, costo=2.0)
    _crear_receta(client, admin_token, "Pan HU15", [("Insumo HU15", 50)], precio=150)  # costo 100
    _vender(client, admin_token, "Distribuidor HU15", "Pan HU15", 4)
    r = client.get("/api/recetas/rentabilidad", headers=h(admin_token))
    assert r.status_code == 200
    fila = next(f for f in r.json() if f["receta"] == "Pan HU15")
    assert fila["costo_unitario"] == 100
    assert fila["ganancia_unitaria"] == 50
    assert fila["margen_pct"] == 33.3
    assert fila["unidades_vendidas"] == 4
    assert fila["ganancia_total"] == 200


def test_hu15_sin_precio_de_venta_el_margen_es_cero_alterno(client, admin_token):
    _crear_insumo(client, admin_token, "Insumo HU15 B", cantidad=1000, costo=1.0)
    _crear_receta(client, admin_token, "Pan HU15 B", [("Insumo HU15 B", 10)])  # sin precio_venta
    fila = next(
        f for f in client.get("/api/recetas/rentabilidad", headers=h(admin_token)).json()
        if f["receta"] == "Pan HU15 B"
    )
    assert fila["ganancia_unitaria"] == 0
    assert fila["margen_pct"] == 0


# ---------- HU-17 Ranking de productos ----------

def test_hu17_ranking_ordena_por_unidades_happy_path(client, admin_token):
    _crear_insumo(client, admin_token, "Insumo HU17", cantidad=100000)
    _crear_receta(client, admin_token, "Pan HU17 Poco", [("Insumo HU17", 1)], precio=10)
    _crear_receta(client, admin_token, "Pan HU17 Mucho", [("Insumo HU17", 1)], precio=10)
    _vender(client, admin_token, "Distribuidor HU17", "Pan HU17 Poco", 1)
    _vender(client, admin_token, "Distribuidor HU17", "Pan HU17 Mucho", 9999)
    r = client.get("/api/ventas/ranking", params={"limite": 50}, headers=h(admin_token))
    assert r.status_code == 200
    ranking = r.json()
    assert ranking[0]["producto"] == "Pan HU17 Mucho"
    assert ranking[0]["posicion"] == 1
    posiciones = [x["producto"] for x in ranking]
    assert posiciones.index("Pan HU17 Mucho") < posiciones.index("Pan HU17 Poco")


def test_hu17_limite_invalido_y_rol_alterno(client, admin_token, empleado_token):
    assert client.get("/api/ventas/ranking", params={"limite": 0}, headers=h(admin_token)).status_code == 400
    assert client.get("/api/ventas/ranking", params={"limite": 999}, headers=h(admin_token)).status_code == 400
    assert client.get("/api/ventas/ranking", headers=h(empleado_token)).status_code == 403
    assert len(client.get("/api/ventas/ranking", params={"limite": 1}, headers=h(admin_token)).json()) <= 1


# ---------- HU-21 Sugerir recetas a producir ----------

def test_hu21_sugiere_recetas_producibles_priorizando_demanda_happy_path(client, admin_token):
    _crear_insumo(client, admin_token, "Insumo HU21", cantidad=1000)
    _crear_receta(client, admin_token, "Pan HU21", [("Insumo HU21", 100)], precio=500)
    _vender(client, admin_token, "Distribuidor HU21", "Pan HU21", 3)  # consume 300 -> quedan 700
    r = client.get("/api/ia/recetas-sugeridas", headers=h(admin_token))
    assert r.status_code == 200
    s = next(x for x in r.json() if x["receta"] == "Pan HU21")
    assert s["unidades_producibles"] == 7
    assert s["insumo_limitante"] == "Insumo HU21"
    assert s["unidades_vendidas_30d"] == 3
    assert s["fuente"] == "regla"


def test_hu21_no_sugiere_recetas_sin_insumo_suficiente_alterno(client, admin_token):
    _crear_insumo(client, admin_token, "Insumo HU21 B", cantidad=5)
    _crear_receta(client, admin_token, "Pan HU21 B", [("Insumo HU21 B", 100)], precio=500)
    r = client.get("/api/ia/recetas-sugeridas", headers=h(admin_token))
    assert r.status_code == 200
    assert all(x["receta"] != "Pan HU21 B" for x in r.json())
