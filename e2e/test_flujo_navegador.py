"""Pruebas E2E en el navegador (planeadas desde el Sprint 2).

Prueban frontend y backend juntos, como lo usaría Mauricio. Necesitan las
dos partes corriendo (ver e2e/README.md):

    APP_URL=http://localhost:5173 python -m pytest e2e -v
"""
import os
import re
import uuid

import pytest
from playwright.sync_api import expect, sync_playwright

APP_URL = os.getenv("APP_URL", "http://localhost:5173")


@pytest.fixture(scope="module")
def navegador():
    with sync_playwright() as p:
        b = p.chromium.launch()
        yield b
        b.close()


@pytest.fixture
def pagina(navegador):
    contexto = navegador.new_context(viewport={"width": 1366, "height": 900})
    pg = contexto.new_page()
    yield pg
    contexto.close()


def entrar(pg, correo, clave):
    pg.goto(f"{APP_URL}/login")
    pg.fill("input[type=email]", correo)
    pg.fill("input[type=password]", clave)
    pg.click("button[type=submit]")


def test_e2e_admin_compra_vende_y_factura(pagina):
    entrar(pagina, "mauricio@laamassadera.com", "Amassadera2026")
    expect(pagina.get_by_role("heading", name="Panel principal")).to_be_visible()

    # Compra de harina: sube el inventario (HU-07)
    pagina.get_by_role("link", name="Compras a proveedores").click()
    pagina.locator("select").first.select_option("Harina")
    pagina.get_by_placeholder("Ej: 5000").fill("5000")
    pagina.get_by_placeholder("Ej: 12800").fill("12800")
    pagina.get_by_role("button", name="Guardar compra").click()
    expect(pagina.get_by_text("El inventario ya se actualizó")).to_be_visible()

    # Venta a un distribuidor nuevo y su factura (HU-09, HU-10, HU-12)
    distribuidor = f"Tienda E2E {uuid.uuid4().hex[:6]}"
    pagina.get_by_role("link", name="Registrar venta").click()
    pagina.get_by_placeholder("Ej: Mercados L. Pinedo").fill(distribuidor)
    pagina.get_by_placeholder("Cant.").fill("2")
    pagina.get_by_role("button", name="Registrar venta").click()
    expect(pagina.get_by_text("Venta registrada")).to_be_visible()
    pagina.get_by_role("button", name="Generar factura de este pedido").click()

    expect(pagina).to_have_url(re.compile(r"/facturas/\d+"))
    expect(pagina.get_by_text(distribuidor)).to_be_visible()
    expect(pagina.get_by_text(re.compile(r"FAC-\d{4}"))).to_be_visible()


def test_e2e_empleado_solo_ve_inventario(pagina):
    entrar(pagina, "empleado@laamassadera.com", "Produccion2026")
    expect(pagina.get_by_role("heading", name="Inventario de insumos")).to_be_visible()
    expect(pagina.get_by_role("link", name="Registrar venta")).to_have_count(0)

    # Si intenta entrar directo a una página de administrador, vuelve al inventario
    pagina.goto(f"{APP_URL}/historial")
    expect(pagina).to_have_url(re.compile(r"/inventario$"))


def test_e2e_contrasena_incorrecta_muestra_error(pagina):
    entrar(pagina, "mauricio@laamassadera.com", "clave-mala")
    expect(pagina).to_have_url(re.compile(r"/login$"))
    expect(pagina.get_by_text(re.compile("incorrect|inválid", re.IGNORECASE))).to_be_visible()
