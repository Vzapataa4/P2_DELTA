"""Datos de DEMOSTRACIÓN: compras y ventas de los últimos 60 días con
distribuidores ficticios, para que el panel, el análisis de periodos y las
ideas de marketing tengan algo que mostrar en la sustentación y en el
manual de usuario.

No se usa en producción con datos reales de Mauricio. Se corre a mano:

    python -m app.demo_data

Solo agrega datos si todavía no hay ventas registradas.
"""
import random
from datetime import datetime, timedelta, timezone

from . import models
from .database import SessionLocal
from .seed import run as seed_run

DISTRIBUIDORES = {
    # nombre: (pedidos por semana, cambio del último mes respecto al anterior)
    "Supermercado La Esquina": (3, 1.15),
    "Tienda Don Pacho": (2, 0.55),  # viene pidiendo menos -> idea de marketing
    "Minimercado El Ahorro": (2, 1.0),
}

COMPRAS = [
    # insumo, cantidad, costo_total, días atrás
    ("Harina Integral", 9000, 36000, 57),
    ("Queso", 9000, 171000, 57),
    ("Harina", 180000, 460800, 58),
    ("Masa Madre", 45000, 115200, 58),
    ("Mantequilla", 18000, 576000, 50),
    ("Levadura", 7500, 105000, 45),
    ("Azúcar", 24000, 96000, 40),
    ("Harina", 180000, 468000, 30),
    ("Masa Madre", 45000, 115200, 30),
    ("Queso", 12000, 228000, 28),
    ("Aceite", 12000, 120000, 25),
    ("Sal", 6000, 15600, 22),
    ("Leche en polvo", 9000, 189000, 18),
    ("Mantequilla", 15000, 480000, 15),
    ("Harina", 150000, 390000, 8),
    ("Masa Madre", 36000, 92160, 8),
]

CONTEO_FINAL = {
    "Harina": 38000,
    "Masa Madre": 9000,
    "Mantequilla": 1400,  # bajo (mínimo 2000)
    "Levadura": 1200,  # medio (mínimo 1000)
    "Queso": 900,  # bajo (mínimo 1500)
    "Leche en polvo": 2000,  # medio (mínimo 1500)
    "Azúcar": 9000,
    "Aceite": 4000,
    "Harina Integral": 2600,  # medio (mínimo 2000)
    "Sal": 5000,
}


def run():
    seed_run()
    db = SessionLocal()
    rnd = random.Random(2026)
    try:
        if db.query(models.Venta).first():
            print("Ya hay ventas registradas; no se agregan datos de demostración.")
            return

        ahora = datetime.now(timezone.utc).replace(tzinfo=None)
        for nombre, cantidad, costo, dias in COMPRAS:
            insumo = db.query(models.Insumo).filter_by(nombre=nombre).first()
            insumo.cantidad_disponible += cantidad
            db.add(models.Compra(
                fecha=ahora - timedelta(days=dias, hours=rnd.randint(1, 8)),
                proveedor_id=insumo.proveedor_id,
                insumo_id=insumo.id,
                cantidad=cantidad,
                costo_total=costo,
            ))
        db.commit()

        recetas = db.query(models.Receta).all()
        pesos = {"Pan Mantequilla": 4, "Pan Queso": 3, "Pan Integral": 1, "Pan Suavecito": 2}
        for distribuidor, (por_semana, cambio) in DISTRIBUIDORES.items():
            for dias in range(58, 0, -1):
                if rnd.random() > por_semana / 7:
                    continue
                factor = cambio if dias <= 30 else 1.0
                receta = rnd.choices(recetas, weights=[pesos.get(r.nombre, 1) for r in recetas])[0]
                unidades = max(5, int(rnd.randint(15, 40) * factor))
                if any(ri.insumo.cantidad_disponible < ri.cantidad_requerida * unidades for ri in receta.insumos):
                    continue
                for ri in receta.insumos:
                    ri.insumo.cantidad_disponible -= ri.cantidad_requerida * unidades
                db.add(models.Venta(
                    fecha=ahora - timedelta(days=dias, hours=rnd.randint(1, 6)),
                    distribuidor_nombre=distribuidor,
                    receta_id=receta.id,
                    cantidad=unidades,
                    total=receta.precio_venta_efectivo * unidades,
                ))
        # Conteo físico simulado al final: deja algunos insumos en rojo y
        # naranja para que se vean las alertas y las recomendaciones.
        for nombre, cantidad in CONTEO_FINAL.items():
            db.query(models.Insumo).filter_by(nombre=nombre).first().cantidad_disponible = cantidad
        db.commit()
        print("Datos de demostración creados.")
    finally:
        db.close()


if __name__ == "__main__":
    run()
