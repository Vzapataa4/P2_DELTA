"""Casos de prueba automatizados de Sprint 3 (HU-07, HU-12, HU-18, HU-22).

Igual que en Sprint 2: cada HU tiene al menos una prueba de happy path y
una de flujo alterno, y cada prueba crea sus propios datos con nombres
únicos. Las ventas de HU-18 se mueven a fechas de 2020 para que no se
mezclen con las ventas que crean otras pruebas el día de hoy.
"""
import sys
import types
from datetime import datetime

from app import ia, models
from app.database import SessionLocal


def h(token):
    return {"Authorization": f"Bearer {token}"}


def _crear_insumo(client, token, nombre, cantidad, costo=1.0, proveedor=None):
    body = {
        "nombre": nombre,
        "unidad": "gr",
        "cantidad_disponible": cantidad,
        "nivel_minimo": 0,
        "costo_unitario": costo,
    }
    if proveedor:
        body["proveedor_nombre"] = proveedor
    r = client.post("/api/insumos", headers=h(token), json=body)
    assert r.status_code == 201, r.text
    return r.json()


def _crear_receta(client, token, nombre, insumo, cantidad, precio):
    r = client.post(
        "/api/recetas",
        headers=h(token),
        json={
            "nombre": nombre,
            "insumos": [{"insumo_nombre": insumo, "cantidad_requerida": cantidad}],
            "precio_venta": precio,
        },
    )
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


def _mover_venta(venta_id, fecha):
    db = SessionLocal()
    try:
        db.get(models.Venta, venta_id).fecha = fecha
        db.commit()
    finally:
        db.close()


def _cantidad_insumo(client, token, nombre):
    insumos = client.get("/api/insumos", headers=h(token)).json()
    return next(i["cantidad_disponible"] for i in insumos if i["nombre"] == nombre)


# ---------- HU-07 Ver compras por proveedor ----------

def test_hu07_compra_suma_inventario_y_agrupa_por_proveedor_happy_path(client, admin_token):
    _crear_insumo(client, admin_token, "Harina S3-07", 1000, proveedor="Molinos S3")

    r = client.post(
        "/api/compras",
        headers=h(admin_token),
        json={"insumo_nombre": "Harina S3-07", "cantidad": 5000, "costo_total": 12500},
    )
    assert r.status_code == 201
    assert r.json()["proveedor"] == "Molinos S3"
    assert _cantidad_insumo(client, admin_token, "Harina S3-07") == 6000

    # Segunda compra del mismo insumo a otro proveedor (se crea solo)
    r = client.post(
        "/api/compras",
        headers=h(admin_token),
        json={
            "insumo_nombre": "Harina S3-07",
            "cantidad": 1000,
            "costo_total": 3000,
            "proveedor_nombre": "Granos del Norte S3",
        },
    )
    assert r.status_code == 201

    resumen = client.get("/api/compras/por-proveedor", headers=h(admin_token)).json()
    molinos = next(p for p in resumen if p["proveedor"] == "Molinos S3")
    granos = next(p for p in resumen if p["proveedor"] == "Granos del Norte S3")
    assert molinos["numero_compras"] == 1 and molinos["total_gastado"] == 12500
    assert granos["insumos"] == ["Harina S3-07"]
    # Ordenado de mayor a menor gasto
    assert resumen.index(molinos) < resumen.index(granos)


def test_hu07_compra_invalida_no_modifica_inventario_alterno(client, admin_token, empleado_token):
    _crear_insumo(client, admin_token, "Sal S3-07", 200)  # sin proveedor
    compra = {"insumo_nombre": "Sal S3-07", "cantidad": 100, "costo_total": 500}

    # Sin proveedor asignado y sin decir a quién se le compró
    assert client.post("/api/compras", headers=h(admin_token), json=compra).status_code == 400
    # Insumo que no existe
    r = client.post("/api/compras", headers=h(admin_token), json={**compra, "insumo_nombre": "Nada S3"})
    assert r.status_code == 404
    # Cantidad cero
    r = client.post("/api/compras", headers=h(admin_token), json={**compra, "cantidad": 0, "proveedor_nombre": "X"})
    assert r.status_code == 422
    # El empleado no puede registrar compras ni verlas
    assert client.post("/api/compras", headers=h(empleado_token), json=compra).status_code == 403
    assert client.get("/api/compras/por-proveedor", headers=h(empleado_token)).status_code == 403
    # Rango de fechas invertido
    r = client.get("/api/compras/por-proveedor?desde=2026-02-01&hasta=2026-01-01", headers=h(admin_token))
    assert r.status_code == 400

    assert _cantidad_insumo(client, admin_token, "Sal S3-07") == 200


# ---------- HU-12 Generar factura básica ----------

def test_hu12_factura_agrupa_ventas_del_pedido_happy_path(client, admin_token):
    _crear_insumo(client, admin_token, "Insumo S3-12", 10000)
    _crear_receta(client, admin_token, "Pan S3-12A", "Insumo S3-12", 10, 1500)
    _crear_receta(client, admin_token, "Pan S3-12B", "Insumo S3-12", 10, 2000)
    v1 = _vender(client, admin_token, "Tienda Factura S3", "Pan S3-12A", 4)
    v2 = _vender(client, admin_token, "Tienda Factura S3", "Pan S3-12B", 3)

    r = client.post("/api/facturas", headers=h(admin_token), json={"venta_ids": [v1["id"], v2["id"]]})
    assert r.status_code == 201
    factura = r.json()
    assert factura["numero"].startswith("FAC-")
    assert factura["distribuidor_nombre"] == "Tienda Factura S3"
    assert factura["total"] == 4 * 1500 + 3 * 2000
    assert [(lin["producto"], lin["precio_unitario"]) for lin in factura["lineas"]] == [
        ("Pan S3-12A", 1500),
        ("Pan S3-12B", 2000),
    ]

    misma = client.get(f"/api/facturas/{factura['id']}", headers=h(admin_token)).json()
    assert misma["numero"] == factura["numero"]
    facturadas = client.get("/api/facturas/ventas-facturadas", headers=h(admin_token)).json()
    assert v1["id"] in facturadas and v2["id"] in facturadas


def test_hu12_reglas_de_factura_alterno(client, admin_token, empleado_token):
    _crear_insumo(client, admin_token, "Insumo S3-12x", 10000)
    _crear_receta(client, admin_token, "Pan S3-12x", "Insumo S3-12x", 10, 1000)
    a = _vender(client, admin_token, "Tienda Uno S3", "Pan S3-12x", 1)
    b = _vender(client, admin_token, "Tienda Dos S3", "Pan S3-12x", 1)

    # Ventas de distribuidores distintos
    r = client.post("/api/facturas", headers=h(admin_token), json={"venta_ids": [a["id"], b["id"]]})
    assert r.status_code == 400
    # Venta inexistente
    r = client.post("/api/facturas", headers=h(admin_token), json={"venta_ids": [a["id"], 999999]})
    assert r.status_code == 404
    # El empleado no puede facturar
    r = client.post("/api/facturas", headers=h(empleado_token), json={"venta_ids": [a["id"]]})
    assert r.status_code == 403
    # Una venta no se factura dos veces
    assert client.post("/api/facturas", headers=h(admin_token), json={"venta_ids": [a["id"]]}).status_code == 201
    assert client.post("/api/facturas", headers=h(admin_token), json={"venta_ids": [a["id"]]}).status_code == 409
    # Lista vacía y factura que no existe
    assert client.post("/api/facturas", headers=h(admin_token), json={"venta_ids": []}).status_code == 422
    assert client.get("/api/facturas/999999", headers=h(admin_token)).status_code == 404


# ---------- HU-18 Comparar periodos de venta ----------

def test_hu18_compara_dos_periodos_happy_path(client, admin_token):
    _crear_insumo(client, admin_token, "Insumo S3-18", 10000, costo=10)
    _crear_receta(client, admin_token, "Pan S3-18", "Insumo S3-18", 10, 1000)  # costo 100

    # Periodo B (marzo 2020): 10 unidades. Periodo A (abril 2020): 15 unidades.
    _mover_venta(_vender(client, admin_token, "T18", "Pan S3-18", 10)["id"], datetime(2020, 3, 10, 9))
    _mover_venta(_vender(client, admin_token, "T18", "Pan S3-18", 5)["id"], datetime(2020, 4, 2, 9))
    _mover_venta(_vender(client, admin_token, "T18", "Pan S3-18", 10)["id"], datetime(2020, 4, 30, 18))

    r = client.get(
        "/api/dashboard/comparar?a_desde=2020-04-01&a_hasta=2020-04-30&b_desde=2020-03-01&b_hasta=2020-03-31",
        headers=h(admin_token),
    )
    assert r.status_code == 200
    data = r.json()
    assert data["periodo_a"]["unidades"] == 15 and data["periodo_a"]["numero_ventas"] == 2
    assert data["periodo_a"]["ingresos"] == 15000 and data["periodo_a"]["ganancia"] == 13500
    assert data["periodo_b"]["ingresos"] == 10000
    assert data["variacion_ingresos_pct"] == 50.0
    assert data["productos"] == [
        {"producto": "Pan S3-18", "unidades_a": 15, "unidades_b": 10, "variacion_pct": 50.0}
    ]


def test_hu18_periodo_sin_ventas_y_rangos_invalidos_alterno(client, admin_token, empleado_token):
    # B sin ventas: no se puede calcular variación (no se divide por cero)
    r = client.get(
        "/api/dashboard/comparar?a_desde=2020-04-01&a_hasta=2020-04-30&b_desde=2019-01-01&b_hasta=2019-01-31",
        headers=h(admin_token),
    )
    assert r.status_code == 200
    assert r.json()["periodo_b"]["numero_ventas"] == 0
    assert r.json()["variacion_ingresos_pct"] is None

    url_invertida = "/api/dashboard/comparar?a_desde=2020-05-01&a_hasta=2020-04-01&b_desde=2020-03-01&b_hasta=2020-03-31"
    assert client.get(url_invertida, headers=h(admin_token)).status_code == 400
    url_ok = "/api/dashboard/comparar?a_desde=2020-04-01&a_hasta=2020-04-30&b_desde=2020-03-01&b_hasta=2020-03-31"
    assert client.get(url_ok, headers=h(empleado_token)).status_code == 403
    # Falta un parámetro
    assert client.get("/api/dashboard/comparar?a_desde=2020-04-01", headers=h(admin_token)).status_code == 422


# ---------- HU-22 Sugerir ideas de marketing ----------

PRODUCTOS = [
    {"nombre": "Pan Popular", "ganancia_unitaria": 300, "unidades_30d": 120},
    {"nombre": "Pan Premium", "ganancia_unitaria": 900, "unidades_30d": 15},
    {"nombre": "Pan Olvidado", "ganancia_unitaria": 200, "unidades_30d": 0},
]
DISTRIBUIDORES = [
    {"nombre": "Súper Estable", "unidades_30d": 100, "unidades_30d_previos": 90, "ganancia_30d": 40000},
    {"nombre": "Tienda en Caída", "unidades_30d": 35, "unidades_30d_previos": 80, "ganancia_30d": 15000},
]


def test_hu22_ideas_salen_de_los_datos_del_negocio_happy_path(client, admin_token):
    ideas = ia.generar_ideas_marketing(PRODUCTOS, DISTRIBUIDORES)
    titulos = [i.titulo for i in ideas]
    assert "Impulsa el Pan Premium" in titulos  # el que más deja no es el más vendido
    assert "Recupera a Tienda en Caída" in titulos  # bajó 56% frente al mes anterior
    assert "Fideliza a Súper Estable" in titulos  # el de más ganancia
    assert "Reactiva el Pan Olvidado" in titulos  # 0 ventas en 30 días
    assert "Recupera a Súper Estable" not in titulos  # subió, no hay que recuperarlo
    assert all(i.fuente == "regla" for i in ideas)

    # El endpoint responde con las ventas reales de la base de pruebas
    r = client.get("/api/ia/marketing", headers=h(admin_token))
    assert r.status_code == 200
    assert len(r.json()) > 0


def test_hu22_sin_ventas_no_inventa_ideas_y_rol_alterno(client, empleado_token):
    sin_ventas = [{**p, "unidades_30d": 0} for p in PRODUCTOS]
    assert ia.generar_ideas_marketing(sin_ventas, []) == []
    assert client.get("/api/ia/marketing", headers=h(empleado_token)).status_code == 403


def test_hu22_a_la_ia_no_le_llegan_nombres_de_distribuidores(monkeypatch):
    """RNF de privacidad: los distribuidores viajan como alias y la
    respuesta se traduce de vuelta a los nombres reales."""
    prompts = []

    class _Mensajes:
        def create(self, **kwargs):
            prompts.append(kwargs["messages"][0]["content"])
            texto = '[{"titulo": "Llama a Distribuidor 2", "idea": "Distribuidor 2 bajó sus pedidos."}]'
            return types.SimpleNamespace(content=[types.SimpleNamespace(text=texto)])

    class _Cliente:
        def __init__(self, **kwargs):
            self.messages = _Mensajes()

    monkeypatch.setitem(sys.modules, "anthropic", types.SimpleNamespace(Anthropic=_Cliente))
    monkeypatch.setattr(ia, "ANTHROPIC_API_KEY", "clave-de-prueba")

    ideas = ia.generar_ideas_marketing(PRODUCTOS, DISTRIBUIDORES)
    assert "Tienda en Caída" not in prompts[0] and "Súper Estable" not in prompts[0]
    assert ideas[0].titulo == "Llama a Tienda en Caída"
    assert ideas[0].fuente == "ia"


def test_hu22_si_la_ia_falla_se_usan_reglas_alterno(monkeypatch):
    class _ClienteRoto:
        def __init__(self, **kwargs):
            raise RuntimeError("sin conexión")

    monkeypatch.setitem(sys.modules, "anthropic", types.SimpleNamespace(Anthropic=_ClienteRoto))
    monkeypatch.setattr(ia, "ANTHROPIC_API_KEY", "clave-de-prueba")
    ideas = ia.generar_ideas_marketing(PRODUCTOS, DISTRIBUIDORES)
    assert ideas and all(i.fuente == "regla" for i in ideas)


# ---------- Compromiso de la Review: lectura de facturas con la API de IA ----------

def test_factura_con_ia_activada_devuelve_lineas_para_confirmar(monkeypatch):
    """Con la key configurada, la foto se manda a Claude y lo que responde
    se devuelve como sugerencia (nunca se registra la venta sola)."""
    from app import importaciones

    respuesta = '```json\n{"distribuidor_nombre": "Mercados L. Pinedo", "lineas": [{"receta_nombre": "Pan Queso", "cantidad": 12}, {"receta_nombre": "Pan Integral", "cantidad": 0}]}\n```'

    class _Cliente:
        def __init__(self, **kwargs):
            self.messages = types.SimpleNamespace(
                create=lambda **kw: types.SimpleNamespace(content=[types.SimpleNamespace(text=respuesta)])
            )

    monkeypatch.setitem(sys.modules, "anthropic", types.SimpleNamespace(Anthropic=_Cliente))
    monkeypatch.setattr(importaciones, "ANTHROPIC_API_KEY", "clave-de-prueba")

    r = importaciones.extraer_factura_desde_imagen(b"foto", "image/png", ["Pan Queso", "Pan Integral"])
    assert r.fuente == "ia"
    assert r.distribuidor_nombre == "Mercados L. Pinedo"
    assert [(lin.receta_nombre, lin.cantidad) for lin in r.lineas] == [("Pan Queso", 12)]  # la línea en 0 se descarta


def test_factura_con_respuesta_ilegible_pide_llenado_manual_alterno(monkeypatch):
    from app import importaciones

    class _Cliente:
        def __init__(self, **kwargs):
            self.messages = types.SimpleNamespace(
                create=lambda **kw: types.SimpleNamespace(content=[types.SimpleNamespace(text="no sé leer esto")])
            )

    monkeypatch.setitem(sys.modules, "anthropic", types.SimpleNamespace(Anthropic=_Cliente))
    monkeypatch.setattr(importaciones, "ANTHROPIC_API_KEY", "clave-de-prueba")

    r = importaciones.extraer_factura_desde_imagen(b"foto", "image/png", ["Pan Queso"])
    assert r.fuente == "manual" and r.lineas == []


# ---------- Editar precio de venta (mejora detectada en el manual) ----------

def test_editar_precio_actualiza_ganancia_sin_tocar_ventas_pasadas(client, admin_token):
    _crear_insumo(client, admin_token, "Insumo S3-precio", 5000, costo=10)
    r = client.post(
        "/api/recetas",
        headers=h(admin_token),
        json={"nombre": "Pan S3-precio", "insumos": [{"insumo_nombre": "Insumo S3-precio", "cantidad_requerida": 10}]},
    )
    receta = r.json()
    assert receta["ganancia_unitaria"] == 0  # sin precio: no se inventa margen
    venta = _vender(client, admin_token, "T-precio", "Pan S3-precio", 2)

    r = client.patch(f"/api/recetas/{receta['id']}/precio", headers=h(admin_token), json={"precio_venta": 250})
    assert r.status_code == 200
    assert r.json()["precio_venta"] == 250 and r.json()["ganancia_unitaria"] == 150
    ventas = client.get("/api/ventas?distribuidor=T-precio", headers=h(admin_token)).json()
    assert ventas[0]["id"] == venta["id"] and ventas[0]["total"] == venta["total"]


def test_editar_precio_invalido_alterno(client, admin_token, empleado_token):
    receta = client.get("/api/recetas", headers=h(admin_token)).json()[0]
    url = f"/api/recetas/{receta['id']}/precio"
    assert client.patch(url, headers=h(admin_token), json={"precio_venta": -1}).status_code == 422
    assert client.patch(url, headers=h(empleado_token), json={"precio_venta": 100}).status_code == 403
    assert client.patch("/api/recetas/999999/precio", headers=h(admin_token), json={"precio_venta": 100}).status_code == 404
