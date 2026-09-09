"""Módulo de IA: análisis de consumo histórico y recomendaciones de
reabastecimiento (HU-19, HU-20).

Se conecta con la API de Claude (Anthropic) enviando únicamente datos
agregados y operativos (nunca datos personales) — ver Wiki_RNF_Ampliados.md,
sección de Privacidad de los datos usados por la IA.

Manejo de fallos: si la API no está configurada o no responde a tiempo,
se cae a una recomendación basada en una regla simple (fallback), en vez de
romper la funcionalidad para el resto del sistema.
"""
import logging
import os
from typing import List

from . import models
from .schemas import RecomendacionOut

logger = logging.getLogger(__name__)

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-sonnet-5")
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
