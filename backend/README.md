# La Amassadera Inteligente — Backend (Sprint 1 MVP)

API REST en FastAPI que implementa las 11 historias de usuario del Sprint 1 (ver Wiki_Backlog_Completo.md).

## Cómo correrlo localmente

```bash
python3 -m venv .venv
source .venv/bin/activate        # en Windows: .venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env             # y completa las variables si quieres usar la IA real

python3 -c "from app.seed import run; run()"   # crea la base de datos con datos de ejemplo
uvicorn app.main:app --reload
```

La API queda en `http://127.0.0.1:8000`. Documentación interactiva (Swagger) en `http://127.0.0.1:8000/docs`.

### Usuarios de prueba (creados por el seed)

| Correo | Contraseña | Rol |
|---|---|---|
| mauricio@laamassadera.com | Amassadera2026 | administrador |
| empleado@laamassadera.com | Produccion2026 | empleado |

## Base de datos

Por defecto usa SQLite (`amassadera.db`), cero configuración. Para usar PostgreSQL en producción, solo se cambia la variable `DATABASE_URL` en `.env` (ej. `postgresql://usuario:clave@host:5432/amassadera`) — el resto del código no cambia, gracias a SQLAlchemy.

## Pruebas

```bash
python3 -m pytest tests/ -v
```

16 casos de prueba automatizados cubriendo las 11 historias de Sprint 1 (happy path + flujo alterno). Ver `Wiki_Casos_de_Prueba.md` para la tabla completa de criterios de aceptación y su relación con cada caso de prueba.

## Calidad de código

- Estándar de nombramiento: PEP 8 (snake_case para funciones/variables, PascalCase para clases).
- Análisis estático: [ruff](https://docs.astral.sh/ruff/) (`pyproject.toml`). Correr con `ruff check .`.
- Ver `Wiki_Calidad_Software.md` para la justificación completa.

## Estructura

```
backend/
├── app/
│   ├── main.py          # entrypoint FastAPI
│   ├── database.py      # configuración SQLAlchemy
│   ├── models.py        # entidades del dominio
│   ├── schemas.py        # validación Pydantic
│   ├── auth.py           # login, hash de contraseñas, JWT, roles
│   ├── ia.py              # Módulo de IA (API de Claude + fallback)
│   ├── seed.py            # datos de ejemplo
│   └── routers/           # endpoints por recurso
├── tests/                  # casos de prueba (pytest)
├── requirements.txt
└── pyproject.toml          # configuración de ruff
```
