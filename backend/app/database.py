"""Configuración de la base de datos.

Usa SQLite por defecto para desarrollo/pruebas locales (cero configuración
adicional para correr el proyecto). En producción se apunta a PostgreSQL
simplemente cambiando la variable de entorno DATABASE_URL, sin tocar el
resto del código, gracias a SQLAlchemy.
"""
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./amassadera.db")
# Algunos proveedores (Render, Heroku) entregan la URL como "postgres://",
# que SQLAlchemy 2 ya no acepta.
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
else:
    # pool_pre_ping: la base gratuita cierra conexiones inactivas; así se
    # revisa la conexión antes de usarla en vez de fallar con un error 500.
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
