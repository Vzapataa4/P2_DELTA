# La Amassadera Inteligente

Aplicación web para la panadería **La Amassadera**: inventario de insumos con alertas por color, compras a proveedores, registro de ventas que descuenta los insumos solo, facturas básicas, costeo y rentabilidad de recetas, comparación de periodos y recomendaciones con IA (qué comprar, qué producir y cómo vender más).

Proyecto Integrador 2, Universidad EAFIT, 2026-2. Equipo: Valentina Zapata (backend e IA) y Jerónimo Ramírez (frontend). Product Owner: Mauricio Acosta Zapata.

## App desplegada

| | Link |
|---|---|
| Aplicación (frontend en Vercel) | **https://la-amassadera.vercel.app** |
| API (backend en Render) | https://amassadera-api.onrender.com (documentación en `/docs`) |

> El backend está en el plan gratuito de Render: si nadie lo usa por 15 minutos se "duerme", y la primera entrada después de eso puede tardar alrededor de un minuto. Después funciona normal.

Usuarios de demostración: los mismos de la tabla de abajo, salvo que en el despliegue se hayan cambiado con `SEED_ADMIN_PASSWORD` / `SEED_EMPLEADO_PASSWORD`.

## Documentación

Todo está en la [Wiki del proyecto](https://github.com/Vzapataa4/P2_DELTA/wiki): definición del producto (Sprint 0), caso de negocio, backlog, casos de prueba, pruebas de usabilidad, **manual de usuario** y **proceso de despliegue** (Sprint 3).

El manual de usuario en PDF también se abre desde la app (menú lateral, "Manual de usuario").

## Estructura

```
backend/    API en FastAPI + SQLAlchemy (SQLite en local, PostgreSQL en producción)
frontend/   React + Vite + Tailwind
e2e/        Pruebas en navegador con Playwright
render.yaml Despliegue del backend y la base de datos en Render
```

## Correrlo en local

```bash
# Backend
cd backend
python3 -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env                                  # aquí va la ANTHROPIC_API_KEY si se quiere la IA real
python3 -c "from app.seed import run; run()"          # datos iniciales
python3 -m app.demo_data                              # opcional: ventas y compras de demostración
uvicorn app.main:app --reload                         # http://127.0.0.1:8000/docs

# Frontend (otra terminal)
cd frontend
npm install
npm run dev                                           # http://localhost:5173
```

| Correo | Contraseña | Rol |
|---|---|---|
| mauricio@laamassadera.com | Amassadera2026 | administrador |
| empleado@laamassadera.com | Produccion2026 | empleado |

## Pruebas

```bash
cd backend && python3 -m pytest tests/ -v --cov=app   # 53 pruebas automáticas
# E2E en navegador: ver e2e/README.md
```

El pipeline de GitHub Actions (`.github/workflows/ci.yml`) corre `ruff`, `pytest` con piso de cobertura del 85 %, `oxlint`, el build del frontend y las pruebas E2E en cada Pull Request a `main`.
