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

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
