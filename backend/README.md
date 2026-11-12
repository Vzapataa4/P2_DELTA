# La Amassadera Inteligente — Backend

API REST en FastAPI con las historias de usuario de los Sprints 1, 2 y 3 (ver la Wiki del proyecto). Ver también el README de la raíz del repositorio.

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

Por defecto usa SQLite (`amassadera.db`), cero configuración. En producción (Render) usa PostgreSQL: solo cambia la variable `DATABASE_URL` (ej. `postgresql://usuario:clave@host:5432/amassadera`) — el resto del código no cambia, gracias a SQLAlchemy.

`python3 -m app.demo_data` agrega compras y ventas de demostración de los últimos 60 días (distribuidores ficticios), solo si la base no tiene ventas.

## Pruebas

```bash
python3 -m pytest tests/ -v
```

53 pruebas automáticas (Sprint 1: 25, Sprint 2: 14, Sprint 3: 14), cada historia con happy path y flujo alterno. La tabla HU → criterio de aceptación → caso de prueba está en la Wiki.

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
│   ├── demo_data.py       # ventas y compras de demostración
│   └── routers/           # endpoints por recurso
├── tests/                  # casos de prueba (pytest)
├── requirements.txt
└── pyproject.toml          # configuración de ruff
```
