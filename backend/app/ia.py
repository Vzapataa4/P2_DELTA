"""Módulo de IA: análisis de consumo histórico y recomendaciones de
reabastecimiento (HU-19, HU-20).

Se conecta con la API de Claude (Anthropic) enviando únicamente datos
agregados y operativos (nunca datos personales) — ver Wiki_RNF_Ampliados.md,
sección de Privacidad de los datos usados por la IA.

Manejo de fallos: si la API no está configurada o no responde a tiempo,
se cae a una recomendación basada en una regla simple (fallback), en vez de
romper la funcionalidad para el resto del sistema.
"""
import json
import logging
import os
import re
from typing import List

from . import models
from .schemas import IdeaMarketingOut, RecomendacionOut

logger = logging.getLogger(__name__)

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-sonnet-5-5")
IA_TIMEOUT_SECONDS = 8


def _regla_fallback(insumo: models.Insumo) -> str:
    faltante = max(insumo.nivel_minimo - insumo.cantidad_disponible, 0)
    sugerido = max(faltante * 2, insumo.nivel_minimo * 0.5)
    return (
        f"{insumo.nombre} está en {insumo.cantidad_disponible:.0f} {insumo.unidad}, "
        f"por debajo del mínimo de {insumo.nivel_minimo:.0f} {insumo.unidad}. "
        f"Se recomienda comprar al menos {sugerido:.0f} {insumo.unidad} adicionales."
    )


def _prompt_para_insumo(insumo: models.Insumo) -> str:
    return (
        "Eres un asistente de una panadería. Con estos datos de un insumo, "
        "da una recomendación de reabastecimiento en una frase, en español, "
        "concreta y accionable (sin rodeos):\n"
        f"- Insumo: {insumo.nombre}\n"
        f"- Cantidad disponible: {insumo.cantidad_disponible} {insumo.unidad}\n"
        f"- Nivel mínimo: {insumo.nivel_minimo} {insumo.unidad}\n"
    )


def generar_recomendaciones(insumos_bajos: List[models.Insumo]) -> List[RecomendacionOut]:
    if not insumos_bajos:
        return []

    if not ANTHROPIC_API_KEY:
        logger.info("ANTHROPIC_API_KEY no configurada; usando recomendaciones por regla.")
        return [
            RecomendacionOut(insumo=i.nombre, mensaje=_regla_fallback(i), fuente="regla")
            for i in insumos_bajos
        ]

    try:
        import anthropic  # import perezoso: solo si la key está configurada

        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY, timeout=IA_TIMEOUT_SECONDS)
        recomendaciones = []
        for insumo in insumos_bajos:
            try:
                resp = client.messages.create(
                    model=CLAUDE_MODEL,
                    max_tokens=120,
                    messages=[{"role": "user", "content": _prompt_para_insumo(insumo)}],
                )
                texto = resp.content[0].text.strip()
                recomendaciones.append(
                    RecomendacionOut(insumo=insumo.nombre, mensaje=texto, fuente="ia")
                )
            except Exception as exc:  # fallo puntual de un insumo: no tumba el resto
                logger.warning("Fallo IA para insumo %s: %s", insumo.nombre, exc)
                recomendaciones.append(
                    RecomendacionOut(
                        insumo=insumo.nombre, mensaje=_regla_fallback(insumo), fuente="regla"
                    )
                )
        return recomendaciones
    except Exception as exc:  # fallo general (sin conexión, librería no disponible, etc.)
        logger.error("Fallo general del Módulo de IA, usando fallback completo: %s", exc)
        return [
            RecomendacionOut(insumo=i.nombre, mensaje=_regla_fallback(i), fuente="regla")
            for i in insumos_bajos
        ]


# ---------- HU-22 Sugerir ideas de marketing ----------
# Entrada: un resumen ya agregado que arma el router (ver routers/ia.py):
#   productos: [{"nombre", "ganancia_unitaria", "unidades_30d"}]
#   distribuidores: [{"nombre", "unidades_30d", "unidades_30d_previos", "ganancia_30d"}]

def _pesos(valor: float) -> str:
    return f"{valor:,.0f}".replace(",", ".")


def _ideas_por_regla(productos, distribuidores) -> List[IdeaMarketingOut]:
    ideas = []
    con_precio = [p for p in productos if p["ganancia_unitaria"] > 0]
    mas_vendido = max(productos, key=lambda p: p["unidades_30d"], default=None)

    if con_precio:
        mas_rentable = max(con_precio, key=lambda p: p["ganancia_unitaria"])
        if mas_vendido and mas_rentable["nombre"] != mas_vendido["nombre"]:
            ideas.append(IdeaMarketingOut(
                titulo=f"Impulsa el {mas_rentable['nombre']}",
                idea=(
                    f"Es el producto que más te deja (${_pesos(mas_rentable['ganancia_unitaria'])} por unidad), "
                    f"pero el más pedido es {mas_vendido['nombre']}. Ofrécelo a tus distribuidores "
                    "con una degustación o un precio de lanzamiento por tiempo limitado."
                ),
                fuente="regla",
            ))

    en_caida = []
    for d in distribuidores:
        antes, ahora = d["unidades_30d_previos"], d["unidades_30d"]
        if antes > 0 and ahora <= antes * 0.8:
            en_caida.append((round((antes - ahora) / antes * 100), d))
    # Solo los dos que más cayeron, para no llenar la pantalla de llamadas.
    for caida, d in sorted(en_caida, key=lambda x: -x[0])[:2]:
        ideas.append(IdeaMarketingOut(
            titulo=f"Recupera a {d['nombre']}",
            idea=(
                f"En los últimos 30 días te pidió {d['unidades_30d']} unidades, {caida}% menos que el "
                f"mes anterior ({d['unidades_30d_previos']}). Llámalo para saber qué pasó y ofrécele "
                "un descuento en su próximo pedido."
            ),
            fuente="regla",
        ))

    # A quien se está yendo no se le propone fidelizar: primero hay que recuperarlo.
    nombres_en_caida = {d["nombre"] for _, d in en_caida}
    activos = [d for d in distribuidores if d["unidades_30d"] > 0 and d["nombre"] not in nombres_en_caida]
    if activos:
        mejor = max(activos, key=lambda d: d["ganancia_30d"])
        ideas.append(IdeaMarketingOut(
            titulo=f"Fideliza a {mejor['nombre']}",
            idea=(
                f"Es el distribuidor que más ganancia te dejó en los últimos 30 días "
                f"(${_pesos(mejor['ganancia_30d'])}). Proponle un pedido fijo semanal a cambio de un "
                "pequeño descuento: te asegura ventas y te ayuda a planear la producción."
            ),
            fuente="regla",
        ))

    for p in productos:
        if p["unidades_30d"] == 0:
            ideas.append(IdeaMarketingOut(
                titulo=f"Reactiva el {p['nombre']}",
                idea=(
                    "No ha tenido ventas en los últimos 30 días. Inclúyelo como muestra gratis en los "
                    "pedidos de tus mejores distribuidores para que lo vuelvan a pedir."
                ),
                fuente="regla",
            ))
    return ideas


def generar_ideas_marketing(productos, distribuidores) -> List[IdeaMarketingOut]:
    """Sin ventas en el último mes no hay de dónde sacar ideas, así que se
    devuelve vacío (no se inventan sugerencias genéricas)."""
    if not any(p["unidades_30d"] for p in productos):
        return []
    if not ANTHROPIC_API_KEY:
        return _ideas_por_regla(productos, distribuidores)

    # Privacidad (RNF de la Wiki): a la IA no le llegan los nombres de los
    # distribuidores, solo alias. Después se cambian de vuelta.
    alias = {d["nombre"]: f"Distribuidor {i}" for i, d in enumerate(distribuidores, start=1)}
    resumen = {
        "productos": productos,
        "distribuidores": [{**d, "nombre": alias[d["nombre"]]} for d in distribuidores],
    }
    prompt = (
        "Eres asesor de una panadería pequeña que le vende a distribuidores (tiendas y supermercados), "
        "no al público. Con este resumen de los últimos 30 días (y los 30 anteriores) propón 3 ideas de "
        "marketing concretas, baratas y fáciles de hacer esta semana, en español sencillo.\n"
        f"{json.dumps(resumen, ensure_ascii=False)}\n"
        'Responde SOLO con JSON: [{"titulo": "...", "idea": "..."}]'
    )
    try:
        import anthropic

        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY, timeout=IA_TIMEOUT_SECONDS * 2)
        resp = client.messages.create(
            model=CLAUDE_MODEL, max_tokens=600, messages=[{"role": "user", "content": prompt}]
        )
        texto = resp.content[0].text.strip()
        texto = re.sub(r"^```(json)?|```$", "", texto, flags=re.MULTILINE).strip()
        ideas = []
        for item in json.loads(texto)[:5]:
            titulo, idea = str(item["titulo"]), str(item["idea"])
            # Los alias más largos primero, para que "Distribuidor 1" no dañe "Distribuidor 10".
            for real, falso in sorted(alias.items(), key=lambda kv: -len(kv[1])):
                titulo, idea = titulo.replace(falso, real), idea.replace(falso, real)
            ideas.append(IdeaMarketingOut(titulo=titulo, idea=idea, fuente="ia"))
        return ideas or _ideas_por_regla(productos, distribuidores)
    except Exception as exc:
        logger.warning("Fallo IA en ideas de marketing, se usan reglas: %s", exc)
        return _ideas_por_regla(productos, distribuidores)
