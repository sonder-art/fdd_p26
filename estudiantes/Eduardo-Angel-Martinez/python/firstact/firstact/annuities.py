"""
firstact.annuities
==================
Anualidades contingentes discretas (variable K_x).

Tipos implementados:
  I.    Anticipada vitalicia:         ax
  Ibis. Vencida vitalicia:            ax_vencida
  II.   Anticipada temporal n años:   ax_temp
  IIbis.Vencida temporal n años:      ax_temp_vencida
  III.  Diferida vitalicia n años:    ax_diferida
  IV.   Diferida temporal n|m años:   ax_diferida_temp

Todas requieren x >= primera edad consecutiva de la tabla (x >= 20 en ILT).
"""

import numpy as np
from .mortality import MortalityTable
from .exceptions import EdadFueraDeRango, EdadNoDisponible, ParametroInvalido


class Annuity:
    """
    Calcula valores actuariales de anualidades contingentes discretas.

    Parámetros
    ----------
    table : MortalityTable
    i : float
        Tasa de interés anual efectiva por default.
        Puede sobreescribirse en cada función.
    """

    def __init__(self, table: MortalityTable, i: float = 0.06):
        self.table = table
        self.i = i

    def _vi(self, i_override):
        i = i_override if i_override is not None else self.i
        return 1.0 / (1.0 + i), i

    def _ages_from(self, x):
        return self.table.ages[self.table.ages >= x]

    def _ages_range(self, x, x_end):
        ages = self.table.ages
        return ages[(ages >= x) & (ages < x_end)]

    # ------------------------------------------------------------------
    # I. Anticipada vitalicia — ax
    # ------------------------------------------------------------------

    def ax(self, x: int, i: float = None) -> float:
        """
        Anualidad de vida entera anticipada (pagos al inicio del año).
        ä_x = sum_{k=0}^{omega-x} v^k * k_p_x

        Parámetros
        ----------
        x : int   Edad (debe ser >= primera edad consecutiva)
        i : float Tasa de interés (opcional)
        """
        try:
            self.table._check_consecutiva(x)
            v, _ = self._vi(i)
            total = 0.0
            for age in self._ages_from(x):
                k = int(age - x)
                kpx = self.table.npx(k, x)
                total += (v ** k) * kpx
            return total
        except (EdadFueraDeRango, EdadNoDisponible):
            raise

    # ------------------------------------------------------------------
    # Ibis. Vencida vitalicia — ax_vencida
    # ------------------------------------------------------------------

    def ax_vencida(self, x: int, i: float = None) -> float:
        """
        Anualidad de vida entera vencida (pagos al final del año).
        a_x = ä_x - 1

        Parámetros
        ----------
        x : int   Edad (debe ser >= primera edad consecutiva)
        i : float Tasa de interés (opcional)
        """
        try:
            return self.ax(x, i) - 1.0
        except (EdadFueraDeRango, EdadNoDisponible):
            raise

    # ------------------------------------------------------------------
    # II. Anticipada temporal — ax_temp
    # ------------------------------------------------------------------

    def ax_temp(self, x: int, n: int, i: float = None) -> float:
        """
        Anualidad temporal anticipada de n años.
        ä_{x:n|} = sum_{k=0}^{n-1} v^k * k_p_x

        Parámetros
        ----------
        x : int   Edad (debe ser >= primera edad consecutiva)
        n : int   Plazo en años
        i : float Tasa de interés (opcional)
        """
        try:
            self.table._check_consecutiva(x)
            if n <= 0:
                raise ParametroInvalido("n debe ser > 0.")
            v, _ = self._vi(i)
            total = 0.0
            for age in self._ages_range(x, x + n):
                k = int(age - x)
                kpx = self.table.npx(k, x)
                total += (v ** k) * kpx
            return total
        except (EdadFueraDeRango, EdadNoDisponible, ParametroInvalido):
            raise

    # ------------------------------------------------------------------
    # IIbis. Vencida temporal — ax_temp_vencida
    # ------------------------------------------------------------------

    def ax_temp_vencida(self, x: int, n: int, i: float = None) -> float:
        """
        Anualidad temporal vencida de n años.
        a_{x:n|} = ä_{x:n|} * v

        Parámetros
        ----------
        x : int   Edad (debe ser >= primera edad consecutiva)
        n : int   Plazo en años
        i : float Tasa de interés (opcional)
        """
        try:
            i_val = i if i is not None else self.i
            v = 1.0 / (1.0 + i_val)
            return self.ax_temp(x, n, i_val) * v
        except (EdadFueraDeRango, EdadNoDisponible, ParametroInvalido):
            raise

    # ------------------------------------------------------------------
    # III. Diferida vitalicia — ax_diferida
    # ------------------------------------------------------------------

    def ax_diferida(self, x: int, m: int, i: float = None) -> float:
        """
        Anualidad de vida entera anticipada diferida m años.
        m|ä_x = sum_{k=m}^{omega-x} v^k * k_p_x = m_E_x * ä_{x+m}

        Parámetros
        ----------
        x : int   Edad (debe ser >= primera edad consecutiva)
        m : int   Período de diferimiento
        i : float Tasa de interés (opcional)
        """
        try:
            self.table._check_consecutiva(x)
            if m <= 0:
                raise ParametroInvalido("m debe ser > 0.")
            v, _ = self._vi(i)
            ages = self.table.ages
            ages_in = ages[ages >= x + m]
            total = 0.0
            for age in ages_in:
                k = int(age - x)
                kpx = self.table.npx(k, x)
                total += (v ** k) * kpx
            return total
        except (EdadFueraDeRango, EdadNoDisponible, ParametroInvalido):
            raise

    # ------------------------------------------------------------------
    # IV. Diferida temporal — ax_diferida_temp
    # ------------------------------------------------------------------

    def ax_diferida_temp(self, x: int, m: int, n: int, i: float = None) -> float:
        """
        Anualidad temporal anticipada de n años diferida m años.
        m|n ä_x = sum_{k=m}^{m+n-1} v^k * k_p_x = m_E_x * ä_{x+m:n|}

        Parámetros
        ----------
        x : int   Edad (debe ser >= primera edad consecutiva)
        m : int   Período de diferimiento
        n : int   Plazo de la anualidad
        i : float Tasa de interés (opcional)
        """
        try:
            self.table._check_consecutiva(x)
            if m <= 0 or n <= 0:
                raise ParametroInvalido("m y n deben ser > 0.")
            v, _ = self._vi(i)
            ages = self.table.ages
            ages_in = ages[(ages >= x + m) & (ages < x + m + n)]
            total = 0.0
            for age in ages_in:
                k = int(age - x)
                kpx = self.table.npx(k, x)
                total += (v ** k) * kpx
            return total
        except (EdadFueraDeRango, EdadNoDisponible, ParametroInvalido):
            raise

    def __repr__(self):
        return f"Annuity(table={self.table}, i={self.i})"
