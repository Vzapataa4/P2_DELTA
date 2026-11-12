# Pruebas E2E (navegador)

Prueban la app completa (frontend + backend) en un Chromium real, con Playwright.

```bash
# 1. Backend con datos semilla (en una terminal)
cd backend && python3 -c "from app.seed import run; run()" && uvicorn app.main:app

# 2. Frontend (en otra terminal)
cd frontend && npm run dev

# 3. Pruebas (en otra terminal, desde la raíz del repo)
pip install -r e2e/requirements.txt && python -m playwright install chromium
APP_URL=http://localhost:5173 python -m pytest e2e -v
```

En GitHub Actions corren solas en el job `e2e` del pipeline, después de `backend` y `frontend`.
