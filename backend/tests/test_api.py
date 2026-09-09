"""Casos de prueba automatizados para las historias de Sprint 1.

Cada test está identificado con su historia de usuario (HU-XX) para
mantener la trazabilidad HU -> Criterio de aceptación -> Caso de prueba
que pide el documento maestro de Sprint 1 (ver también
Wiki_Casos_de_Prueba.md con la tabla completa Given-When-Then).
"""


def auth_header(token):
    return {"Authorization": f"Bearer {token}"}


# ---------- HU-01 Iniciar sesión ----------

def test_hu01_login_exitoso_happy_path(client):
    r = client.post(
        "/api/auth/login",
        json={"correo": "mauricio@laamassadera.com", "contrasena": "Amassadera2026"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["access_token"]
    assert body["rol"] == "administrador"


def test_hu01_login_credenciales_invalidas_alterno(client):
    r = client.post(
        "/api/auth/login",
        json={"correo": "mauricio@laamassadera.com", "contrasena": "clave-incorrecta"},
    )
    assert r.status_code == 401
    assert "incorrect" in r.json()["detail"].lower() or "incorrectos" in r.json()["detail"].lower()


# ---------- HU-04 / HU-05 Ver inventario y alerta de insumo bajo ----------

def test_hu04_ver_inventario_happy_path(client, admin_token):
    r = client.get("/api/insumos", headers=auth_header(admin_token))
    assert r.status_code == 200
    nombres = [i["nombre"] for i in r.json()]
    assert "Harina" in nombres


def test_hu04_inventario_sin_autenticacion_alterno(client):
    r = client.get("/api/insumos")
    assert r.status_code == 401


def test_hu05_alerta_insumo_bajo_happy_path(client, admin_token):
    r = client.get("/api/insumos", headers=auth_header(admin_token))
    mantequilla = next(i for i in r.json() if i["nombre"] == "Mantequilla")
    # Dado que la Mantequilla sembrada (1500 gr) está por debajo de su
    # nivel mínimo (2000 gr), cuando se consulta el inventario, debe
    # marcarse como "bajo".
    assert mantequilla["bajo"] is True


def test_hu05_insumo_con_stock_suficiente_no_genera_alerta_alterno(client, admin_token):
    r = client.get("/api/insumos", headers=auth_header(admin_token))
    harina = next(i for i in r.json() if i["nombre"] == "Harina")
    assert harina["bajo"] is False


# ---------- HU-03 Registrar insumos ----------

def test_hu03_registrar_insumo_happy_path(client, admin_token):
    r = client.post(
        "/api/insumos",
        headers=auth_header(admin_token),
        json={
            "nombre": "Esencia de Vainilla",
            "unidad": "gr",
            "cantidad_disponible": 500,
            "nivel_minimo": 100,
            "costo_unitario": 80,
            "proveedor_nombre": "Distribuidora local",
        },
    )
    assert r.status_code == 201
    assert r.json()["nombre"] == "Esencia de Vainilla"
    assert r.json()["bajo"] is False


def test_hu03_insumo_duplicado_alterno(client, admin_token):
    r = client.post(
        "/api/insumos",
        headers=auth_header(admin_token),
        json={"nombre": "Harina", "cantidad_disponible": 1000, "nivel_minimo": 500, "costo_unitario": 2.5},
    )
    assert r.status_code == 409


# ---------- HU-13 / HU-14 Registrar receta y calcular costo ----------

def test_hu13_registrar_receta_happy_path(client, admin_token):
    r = client.post(
        "/api/recetas",
        headers=auth_header(admin_token),
        json={
            "nombre": "Pan de Prueba",
            "insumos": [{"insumo_nombre": "Harina", "cantidad_requerida": 50}],
        },
    )
    assert r.status_code == 201
    assert r.json()["costo_total"] == 50 * 2.56


def test_hu13_receta_con_insumo_inexistente_alterno(client, admin_token):
    r = client.post(
        "/api/recetas",
        headers=auth_header(admin_token),
        json={
            "nombre": "Pan Inventado",
            "insumos": [{"insumo_nombre": "Ingrediente que no existe", "cantidad_requerida": 10}],
        },
    )
    assert r.status_code == 400


def test_hu14_costo_receta_coincide_con_suma_de_insumos_happy_path(client, admin_token):
    r = client.get("/api/recetas", headers=auth_header(admin_token))
    pan_queso = next(rc for rc in r.json() if rc["nombre"] == "Pan Queso")
    esperado = sum(
        ri["cantidad_requerida"] * {"Harina": 2.56, "Masa Madre": 2.56, "Azúcar": 4, "Sal": 2.6,
                                     "Mantequilla": 32, "Aceite": 10, "Levadura": 14, "Queso": 19,
                                     "Leche en polvo": 21}[ri["insumo_nombre"]]
        for ri in pan_queso["insumos"]
    )
    assert round(pan_queso["costo_total"], 2) == round(esperado, 2)


# ---------- HU-09 / HU-10 Registrar venta y descuento automático ----------

def test_hu09_hu10_registrar_venta_descuenta_insumo_happy_path(client, admin_token):
    antes = next(
        i for i in client.get("/api/insumos", headers=auth_header(admin_token)).json()
        if i["nombre"] == "Harina"
    )
    r = client.post(
        "/api/ventas",
        headers=auth_header(admin_token),
        json={"distribuidor_nombre": "Éxito Envigado", "receta_nombre": "Pan Integral", "cantidad": 5},
    )
    assert r.status_code == 201
    despues = next(
        i for i in client.get("/api/insumos", headers=auth_header(admin_token)).json()
        if i["nombre"] == "Harina"
    )
    # Pan Integral usa 70 gr de Harina por unidad -> 5 unidades = 350 gr
    assert antes["cantidad_disponible"] - despues["cantidad_disponible"] == 350


def test_hu10_venta_con_insumo_insuficiente_no_registra_alterno(client, admin_token):
    r = client.post(
        "/api/ventas",
        headers=auth_header(admin_token),
        json={
            "distribuidor_nombre": "Distribuidora del Sur",
            "receta_nombre": "Pan Mantequilla",
            "cantidad": 999999,  # cantidad imposible de cubrir con el inventario actual
        },
    )
    assert r.status_code == 400
    ventas = client.get("/api/ventas", headers=auth_header(admin_token)).json()
    assert not any(v["cantidad"] == 999999 for v in ventas)


def test_hu09_empleado_no_puede_registrar_venta_alterno(client, empleado_token):
    r = client.post(
        "/api/ventas",
        headers=auth_header(empleado_token),
        json={"distribuidor_nombre": "X", "receta_nombre": "Pan Mantequilla", "cantidad": 1},
    )
    assert r.status_code == 403


# ---------- HU-16 Ver panel principal ----------

def test_hu16_panel_principal_happy_path(client, admin_token):
    r = client.get("/api/dashboard", headers=auth_header(admin_token))
    assert r.status_code == 200
    body = r.json()
    assert "ventas_hoy" in body and "insumos_en_alerta" in body


def test_hu16_panel_principal_requiere_admin_alterno(client, empleado_token):
    r = client.get("/api/dashboard", headers=auth_header(empleado_token))
    assert r.status_code == 403


# ---------- HU-19 / HU-20 Recomendaciones de IA ----------

def test_hu19_hu20_recomendaciones_fallback_sin_api_key_happy_path(client, admin_token, monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    r = client.get("/api/ia/recomendaciones", headers=auth_header(admin_token))
    assert r.status_code == 200
    recomendaciones = r.json()
    assert all(rec["fuente"] == "regla" for rec in recomendaciones)
    assert any(rec["insumo"] == "Mantequilla" for rec in recomendaciones)


def test_hu20_sin_insumos_bajos_no_hay_recomendaciones_alterno(client, admin_token):
    from app import models
    from app.database import SessionLocal

    db = SessionLocal()
    try:
        for nombre in ["Mantequilla", "Levadura", "Queso"]:
            insumo = db.query(models.Insumo).filter_by(nombre=nombre).first()
            insumo.cantidad_disponible = insumo.nivel_minimo + 1000
        db.commit()
    finally:
        db.close()

    r = client.get("/api/ia/recomendaciones", headers=auth_header(admin_token))
    assert r.status_code == 200
    assert r.json() == []


# ---------- Nuevas mejoras: Acta de Compromiso 5/ago/2026 ----------

def test_hu05_alertas_tres_niveles_happy_path(client, admin_token):
    """Alertas de inventario por color (Acta de Compromiso): ok/medio/bajo.

    Se registran insumos nuevos con valores propios de este test (en vez de
    depender de la Mantequilla sembrada, que otro test de la suite modifica),
    para que el resultado no dependa del orden de ejecución."""
    def crear(nombre, disponible, minimo):
        r = client.post(
            "/api/insumos",
            headers=auth_header(admin_token),
            json={"nombre": nombre, "cantidad_disponible": disponible, "nivel_minimo": minimo, "costo_unitario": 1},
        )
        assert r.status_code == 201
        return r.json()

    bajo = crear("Insumo Nivel Bajo", 100, 500)      # 100 < 500 -> bajo
    medio = crear("Insumo Nivel Medio", 600, 500)    # 500 <= 600 < 750 -> medio
    ok = crear("Insumo Nivel Ok", 900, 500)          # 900 >= 750 -> ok

    assert bajo["nivel"] == "bajo"
    assert medio["nivel"] == "medio"
    assert ok["nivel"] == "ok"


def test_hu16_dashboard_vista_diaria_y_por_distribuidor_happy_path(client, admin_token):
    """El panel trae ventas por día, semana y mes, además del análisis por distribuidor."""
    r = client.get("/api/dashboard", headers=auth_header(admin_token))
    assert r.status_code == 200
    body = r.json()
    assert "ventas_por_dia" in body
    assert "ventas_por_semana" in body
    assert "ventas_por_mes" in body
    assert "analisis_distribuidores" in body
    if body["ventas_por_dia"]:
        assert "dia" in body["ventas_por_dia"][0]
    if body["ventas_por_semana"]:
        assert "semana" in body["ventas_por_semana"][0]
    if body["ventas_por_mes"]:
        assert "mes" in body["ventas_por_mes"][0]


def test_ventas_lote_registra_varias_lineas_happy_path(client, admin_token):
    """Registro de varias líneas de una misma factura bajo un distribuidor."""
    r = client.post(
        "/api/ventas/lote",
        headers=auth_header(admin_token),
        json={
            "distribuidor_nombre": "Carulla Poblado",
            "lineas": [
                {"receta_nombre": "Pan Suavecito", "cantidad": 2},
                {"receta_nombre": "Pan Integral", "cantidad": 3},
            ],
        },
    )
    assert r.status_code == 201
    body = r.json()
    assert len(body) == 2
    assert {v["receta_nombre"] for v in body} == {"Pan Suavecito", "Pan Integral"}


def test_importar_factura_sin_api_key_pide_llenado_manual_alterno(client, admin_token, monkeypatch):
    """Sin ANTHROPIC_API_KEY, la importación de factura no inventa datos:
    devuelve fuente 'manual' para que el usuario complete el formulario."""
    monkeypatch.setattr("app.importaciones.ANTHROPIC_API_KEY", None)
    archivo = ("factura.jpg", b"contenido-simulado-de-imagen", "image/jpeg")
    r = client.post(
        "/api/ventas/importar-factura",
        headers=auth_header(admin_token),
        files={"file": archivo},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["fuente"] == "manual"
    assert body["lineas"] == []


def test_importar_excel_receta_happy_path(client, admin_token):
    """Sube un Excel con insumos/cantidades y devuelve las líneas
    reconocidas para que el usuario las confirme (no guarda nada solo)."""
    from io import BytesIO

    from openpyxl import Workbook

    wb = Workbook()
    ws = wb.active
    ws.append(["Insumo", "Cantidad por unidad"])
    ws.append(["Harina", 60])
    ws.append(["Azúcar", 8])
    ws.append(["Insumo Que No Existe", 5])
    buf = BytesIO()
    wb.save(buf)
    buf.seek(0)

    archivo = (
        "Pan_Especial.xlsx",
        buf.read(),
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    r = client.post(
        "/api/recetas/importar-excel",
        headers=auth_header(admin_token),
        files={"file": archivo},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["receta_nombre"] == "Pan Especial"
    nombres = {linea["insumo_nombre"]: linea["existe"] for linea in body["lineas"]}
    assert nombres["Harina"] is True
    assert nombres["Azúcar"] is True
    assert nombres["Insumo Que No Existe"] is False


# ---------- Precio de venta y ganancia real (corrige bug: ganancia $0) ----------

def test_receta_sin_precio_venta_ganancia_cero_happy_path(client, admin_token):
    """Si no se define precio de venta, la ganancia debe ser 0 (no inventa un margen)."""
    r = client.post(
        "/api/recetas",
        headers=auth_header(admin_token),
        json={
            "nombre": "Pan Sin Precio",
            "insumos": [{"insumo_nombre": "Harina", "cantidad_requerida": 50}],
        },
    )
    assert r.status_code == 201
    body = r.json()
    assert body["precio_venta"] is None
    assert body["ganancia_unitaria"] == 0


def test_receta_con_precio_venta_y_venta_genera_ganancia_real_happy_path(client, admin_token):
    """Con un precio de venta definido, la venta debe cobrar ese precio (no el
    costo) y el panel debe mostrar una ganancia distinta de cero."""
    r = client.post(
        "/api/recetas",
        headers=auth_header(admin_token),
        json={
            "nombre": "Pan Con Precio",
            "insumos": [{"insumo_nombre": "Harina", "cantidad_requerida": 50}],
            "precio_venta": 500,
        },
    )
    assert r.status_code == 201
    body = r.json()
    assert body["precio_venta"] == 500
    costo_esperado = 50 * 2.56
    assert body["ganancia_unitaria"] == round(500 - costo_esperado, 2)

    venta = client.post(
        "/api/ventas",
        headers=auth_header(admin_token),
        json={"distribuidor_nombre": "Panadería Ganancia Test", "receta_nombre": "Pan Con Precio", "cantidad": 2},
    )
    assert venta.status_code == 201
    assert venta.json()["total"] == 500 * 2

    dash = client.get("/api/dashboard", headers=auth_header(admin_token))
    fila = next(
        d for d in dash.json()["analisis_distribuidores"] if d["distribuidor"] == "Panadería Ganancia Test"
    )
    assert fila["ganancia_total"] > 0
