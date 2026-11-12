# Se carga el archivo .env (si existe) antes de que cualquier módulo lea
# variables como ANTHROPIC_API_KEY o DATABASE_URL. Hasta el Sprint 2 el .env
# no se leía nunca, por eso la lectura de facturas con IA no se activaba
# aunque la key estuviera puesta. override=False: lo que ya venga del
# entorno (Render, CI, pruebas) tiene prioridad sobre el archivo.
from dotenv import load_dotenv

load_dotenv(override=False)
