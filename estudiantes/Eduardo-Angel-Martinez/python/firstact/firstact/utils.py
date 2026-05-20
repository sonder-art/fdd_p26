"""
firstact.utils
==============
Conversiones entre seguros/anualidades discretos y continuos.

Bajo el supuesto UDD (Distribución Uniforme de Muertes):
    Ā_x = A_x * (i / delta)     donde delta = ln(1+i)
    ā_x = (1 - Ā_x) / delta

APLICA (pagos contingentes por muerte):
    - Seguro ordinario de vida:  Ax  → Āx
    - Seguro temporal:           Ax_temporal → Ā^1_{x:n|}
    - Seguro diferido:           Ax_diferido → m|Āx
    - Seguro creciente:          IAx → (IĀ)x
    - Seguro decreciente:        DAx → (DĀ)^1_{x:n|}
    - Anualidades derivadas de los anteriores

NO APLICA (pagos por sobrevivencia):
    - Dotal puro:   nEx   → ConversionNoAplicable
    - Dotal mixto:  Ax_dotal_mixto → ConversionNoAplicable
"""

import numpy as np
from .exceptions import ConversionNoAplicable, ParametroInvalido

# Tipos válidos para conversión
_TIPOS_VALIDOS = {
    "seguro",
    "anualidad",
}

_TIPOS_NO_VALIDOS = {
    "dotal_puro",
    "dotal_mixto",
}


def to_cont(valor: float, i: float, kind: str) -> float:
    """
    Convierte un valor actuarial discreto a su equivalente continuo
    bajo el supuesto UDD.

    Parámetros
    ----------
    valor : float
        Valor actuarial discreto (A_x, ä_x, etc.)
    i : float
        Tasa de interés anual efectiva (obligatorio).
    kind : str
        Tipo de valor a convertir:
        - 'seguro'      → Ā = A * (i/delta)
        - 'anualidad'   → ā = (1 - Ā) / delta
                          donde Ā = 1 - delta * ä  (se obtiene del discreto)
        - 'dotal_puro'  → ConversionNoAplicable
        - 'dotal_mixto' → ConversionNoAplicable

    Retorna
    -------
    float : Valor actuarial continuo equivalente

    Ejemplos
    --------
    >>> from firstact.utils import to_cont
    >>> to_cont(0.12876, i=0.06, kind='seguro')    # Ā_35
    >>> to_cont(15.3926, i=0.06, kind='anualidad') # ā_35

    Lanza
    -----
    ConversionNoAplicable : si kind es 'dotal_puro' o 'dotal_mixto'
    ParametroInvalido     : si i <= 0 o kind no reconocido
    """
    try:
        _validar_params(valor, i, kind)

        delta = np.log(1 + i)
        d = i / (1 + i)

        if kind == "seguro":
            # Ā = A * (i / delta)
            return valor * (i / delta)

        elif kind == "anualidad":
            # Del discreto: A = 1 - d * ä
            # Continuo: Ā = A * (i/delta) = (1 - d*ä) * (i/delta)
            # ā = (1 - Ā) / delta
            A_disc = 1 - d * valor
            A_cont = A_disc * (i / delta)
            return (1 - A_cont) / delta

    except (ConversionNoAplicable, ParametroInvalido):
        raise


def to_disc(valor: float, i: float, kind: str) -> float:
    """
    Convierte un valor actuarial continuo a su equivalente discreto
    bajo el supuesto UDD.

    Parámetros
    ----------
    valor : float
        Valor actuarial continuo (Ā_x, ā_x, etc.)
    i : float
        Tasa de interés anual efectiva (obligatorio).
    kind : str
        Tipo de valor a convertir:
        - 'seguro'      → A = Ā * (delta/i)
        - 'anualidad'   → ä = (1 - A) / d
        - 'dotal_puro'  → ConversionNoAplicable
        - 'dotal_mixto' → ConversionNoAplicable

    Retorna
    -------
    float : Valor actuarial discreto equivalente

    Ejemplos
    --------
    >>> from firstact.utils import to_disc
    >>> to_disc(0.13259, i=0.06, kind='seguro')    # A_35
    >>> to_disc(14.886,  i=0.06, kind='anualidad') # ä_35

    Lanza
    -----
    ConversionNoAplicable : si kind es 'dotal_puro' o 'dotal_mixto'
    ParametroInvalido     : si i <= 0 o kind no reconocido
    """
    try:
        _validar_params(valor, i, kind)

        delta = np.log(1 + i)
        d = i / (1 + i)

        if kind == "seguro":
            # A = Ā * (delta / i)
            return valor * (delta / i)

        elif kind == "anualidad":
            # Del continuo: Ā = 1 - delta * ā
            # Discreto: A = Ā * (delta/i)
            # ä = (1 - A) / d
            A_cont = 1 - delta * valor
            A_disc = A_cont * (delta / i)
            return (1 - A_disc) / d

    except (ConversionNoAplicable, ParametroInvalido):
        raise


def _validar_params(valor: float, i: float, kind: str) -> None:
    """Valida parámetros comunes de to_cont y to_disc."""
    if i <= 0:
        raise ParametroInvalido(
            f"i debe ser > 0. Se recibió i={i}."
        )

    if kind in _TIPOS_NO_VALIDOS:
        raise ConversionNoAplicable(
            f"La conversión discreto↔continuo NO aplica para '{kind}' "
            f"bajo UDD porque contiene pagos por sobrevivencia (nEx), "
            f"no por muerte.\n"
            f"  - 'dotal_puro'  (nEx): es v^n * npx, no depende de muerte\n"
            f"  - 'dotal_mixto' (Ax_dotal_mixto = A^1 + nEx): contiene nEx\n"
            f"Solo aplica para: {sorted(_TIPOS_VALIDOS)}"
        )

    if kind not in _TIPOS_VALIDOS:
        raise ParametroInvalido(
            f"kind='{kind}' no reconocido. "
            f"Valores válidos: {sorted(_TIPOS_VALIDOS)}. "
            f"Valores que lanzan ConversionNoAplicable: {sorted(_TIPOS_NO_VALIDOS)}."
        )
