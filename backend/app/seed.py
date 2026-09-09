"""Datos semilla: usuario administrador de prueba + insumos y recetas reales
tomados de las fichas técnicas de La Amassadera (ver formulas la AMASSADERA.xlsx)."""
from . import models
from .auth import hash_password
from .database import Base, SessionLocal, engine

# Margen de venta usado SOLO para tener un precio_venta de ejemplo en los
# datos semilla (para que el panel de "ganancia por distribuidor" no
# arranque en $0). Es un valor ilustrativo -- Mauricio debe definir el
# precio real de venta de cada receta desde la pantalla de Recetas.
MARGEN_DEMO = 1.45

INSUMOS = [
    {"nombre": "Harina", "unidad": "gr", "cantidad_disponible": 25000, "nivel_minimo": 15000, "costo_unitario": 2.56, "proveedor_nombre": "Rica Harina"},
    {"nombre": "Masa Madre", "unidad": "gr", "cantidad_disponible": 4000, "nivel_minimo": 3000, "costo_unitario": 2.56, "proveedor_nombre": "Producción propia"},
    {"nombre": "Azúcar", "unidad": "gr", "cantidad_disponible": 6000, "nivel_minimo": 5000, "costo_unitario": 4, "proveedor_nombre": "Distribuidora local"},
    {"nombre": "Sal", "unidad": "gr", "cantidad_disponible": 4000, "nivel_minimo": 3000, "costo_unitario": 2.6, "proveedor_nombre": "Distribuidora local"},
    {"nombre": "Mantequilla", "unidad": "gr", "cantidad_disponible": 1500, "nivel_minimo": 2000, "costo_unitario": 32, "proveedor_nombre": "Distribuidora local"},
    {"nombre": "Aceite", "unidad": "gr", "cantidad_disponible": 5000, "nivel_minimo": 3000, "costo_unitario": 10, "proveedor_nombre": "Distribuidora local"},
    {"nombre": "Levadura", "unidad": "gr", "cantidad_disponible": 800, "nivel_minimo": 1000, "costo_unitario": 14, "proveedor_nombre": "Distribuidora local"},
    {"nombre": "Leche en polvo", "unidad": "gr", "cantidad_disponible": 2000, "nivel_minimo": 1500, "costo_unitario": 21, "proveedor_nombre": "Distribuidora local"},
    {"nombre": "Harina Integral", "unidad": "gr", "cantidad_disponible": 3000, "nivel_minimo": 2000, "costo_unitario": 4, "proveedor_nombre": "Distribuidora local"},
    {"nombre": "Queso", "unidad": "gr", "cantidad_disponible": 1200, "nivel_minimo": 1500, "costo_unitario": 19, "proveedor_nombre": "Distribuidora local"},
]

# Cantidades por UNIDAD de producto (la ficha original es por tanda de 10
# porciones, así que se divide entre 10 para dejarlo por unidad vendida).
RECETAS = [
    {"nombre": "Pan Mantequilla", "insumos": [
        ("Harina", 90), ("Masa Madre", 20), ("Azúcar", 8), ("Sal", 2),
        ("Mantequilla", 10), ("Aceite", 6), ("Levadura", 2.5), ("Leche en polvo", 7),
    ]},
    {"nombre": "Pan Queso", "insumos": [
        ("Harina", 90), ("Masa Madre", 20), ("Azúcar", 10.5), ("Sal", 2),
        ("Mantequilla", 5), ("Aceite", 9.5), ("Levadura", 2), ("Queso", 18), ("Leche en polvo", 7),
    ]},
    {"nombre": "Pan Integral", "insumos": [
        ("Harina", 70), ("Masa Madre", 27), ("Harina Integral", 30),
        ("Azúcar", 10.5), ("Sal", 2.3),
    ]},
    {"nombre": "Pan Suavecito", "insumos": [
        ("Harina", 90), ("Masa Madre", 20), ("Azúcar", 8),
        ("Sal", 2.3), ("Aceite", 12), ("Levadura", 2),
    ]},
]

# Costos unitarios de cada insumo, capturados ANTES de que run() les quite
# "proveedor_nombre" (ver abajo), para poder calcular un precio_venta de
# ejemplo por receta.
_COSTOS_UNITARIOS = {i["nombre"]: i["costo_unitario"] for i in INSUMOS}


def _precio_venta_demo(insumos_receta):
    costo = sum(cantidad * _COSTOS_UNITARIOS[nombre] for nombre, cantidad in insumos_receta)
    return round(costo * MARGEN_DEMO / 10) * 10


def run():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        if not db.query(models.Usuario).first():
            db.add(models.Usuario(
                nombre="Mauricio Acosta Zapata",
                correo="mauricio@laamassadera.com",
                contrasena_hash=hash_password("Amassadera2026"),
                rol=models.RolUsuario.ADMIN,
            ))
            db.add(models.Usuario(
                nombre="Personal de Producción",
                correo="empleado@laamassadera.com",
                contrasena_hash=hash_password("Produccion2026"),
                rol=models.RolUsuario.EMPLEADO,
            ))

        if not db.query(models.Insumo).first():
            for data in INSUMOS:
                proveedor = None
                nombre_prov = data.pop("proveedor_nombre", None)
                if nombre_prov:
                    proveedor = db.query(models.Proveedor).filter_by(nombre=nombre_prov).first()
                    if not proveedor:
                        proveedor = models.Proveedor(nombre=nombre_prov)
                        db.add(proveedor)
                        db.flush()
                db.add(models.Insumo(**data, proveedor_id=proveedor.id if proveedor else None))
            db.commit()

        if not db.query(models.Receta).first():
            for r in RECETAS:
                receta = models.Receta(
                    nombre=r["nombre"], precio_venta=_precio_venta_demo(r["insumos"])
                )
                db.add(receta)
                db.flush()
                for nombre_insumo, cantidad in r["insumos"]:
                    insumo = db.query(models.Insumo).filter_by(nombre=nombre_insumo).first()
                    db.add(models.RecetaInsumo(
                        receta_id=receta.id, insumo_id=insumo.id, cantidad_requerida=cantidad
                    ))
            db.commit()

        db.commit()
    finally:
        db.close()


if __name__ == "__main__":
    run()
    print("Base de datos inicializada con datos de ejemplo.")
