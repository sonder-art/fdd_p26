"""
firstact.insurance
==================
Seguros de vida discretos (pago al final del año de muerte, variable K_x).

Tipos implementados:
  I.   Seguro ordinario de vida:   Ax
  II.  Seguro temporal n años:     Ax_temporal
  III. Dotal puro n años:          nEx
  IV.  Dotal mixto n años:         Ax_dotal_mixto
  V.   Diferido n años:            Ax_diferido
  VI.  Creciente:                  IAx
  VII. Decreciente temporal:       DAx

Nota: Ax, Ax_temporal, Ax_diferido, IAx, DAx requieren x >= primera
edad consecutiva de la tabla (x >= 20 en la ILT).
nEx y Ax_dotal_mixto solo requieren que x y x+n estén en la tabla.
"""

import numpy as np
from .mortality import MortalityTable
from .exceptions import EdadFueraDeRango, EdadNoDisponible, ParametroInvalido


def _get_v(i: float) -> float:
    return 1.0 / (1.0 + i)


class Insurance:
    """
    Calcula valores actuariales netos de seguros de vida discretos.
    Todos los beneficios se pagan al final del año de muerte (K_x).

    Parámetros
    ----------
    table : MortalityTable
    i : float
        Tasa de interés anual efectiva por default (ej. 0.06).
        Puede sobreescribirse en cada función.
    """

    def __init__(self, table: MortalityTable, i: float = 0.06):
        self.table = table
        self.i = i

    def _vi(self, i_override):
        """Retorna v con i sobreescrito si se proporciona."""
        i = i_override if i_override is not None else self.i
        return _get_v(i), i

    def _ages_from(self, x):
        return self.table.ages[self.table.ages >= x]

    def _ages_range(self, x, n):
        ages = self.table.ages
        return ages[(ages >= x) & (ages < x + n)]

    # ------------------------------------------------------------------
    # I. Seguro ordinario de vida — Ax
    # ------------------------------------------------------------------

    def Ax(self, x: int, i: float = None) -> float:
        """
        Valor actuarial del seguro ordinario de vida.
        Paga 1 al final del año de muerte.

        A_x = sum_{k=0}^{omega-x-1} v^{k+1} * k_p_x * q_{x+k}

        Parámetros
        ----------
        x : int   Edad de entrada (debe ser >= primera edad consecutiva)
        i : float Tasa de interés (opcional, sobreescribe el default)
        """
        try:
            self.table._check_consecutiva(x)
            v, _ = self._vi(i)
            total = 0.0
            for age in self._ages_from(x):
                k = int(age - x)
                kpx = self.table.npx(k, x)
                qxk = self.table.qx(age)
                total += (v ** (k + 1)) * kpx * qxk
            return total
        except (EdadFueraDeRango, EdadNoDisponible):
            raise

    # ------------------------------------------------------------------
    # II. Seguro temporal n años — Ax_temporal
    # ------------------------------------------------------------------

    def Ax_temporal(self, x: int, n: int, i: float = None) -> float:
        """
        Valor actuarial del seguro temporal de n años.
        Paga 1 si (x) muere dentro de n años.

        A^1_{x:n|} = sum_{k=0}^{n-1} v^{k+1} * k_p_x * q_{x+k}

        Parámetros
        ----------
        x : int   Edad de entrada (debe ser >= primera edad consecutiva)
        n : int   Plazo en años
        i : float Tasa de interés (opcional)
        """
        try:
            self.table._check_consecutiva(x)
            if n <= 0:
                raise ParametroInvalido("n debe ser > 0.")
            v, _ = self._vi(i)
            total = 0.0
            for age in self._ages_range(x, n):
                k = int(age - x)
                kpx = self.table.npx(k, x)
                qxk = self.table.qx(age)
                total += (v ** (k + 1)) * kpx * qxk
            return total
        except (EdadFueraDeRango, EdadNoDisponible, ParametroInvalido):
            raise

    # ------------------------------------------------------------------
    # III. Dotal puro — nEx
    # ------------------------------------------------------------------

    def nEx(self, x: int, n: int, i: float = None) -> float:
        """
        Dotal puro: pago de 1 si (x) sobrevive n años.
        n_E_x = v^n * n_p_x

        Solo requiere que x y x+n estén en la tabla.

        Parámetros
        ----------
        x : int   Edad de entrada
        n : int   Plazo en años
        i : float Tasa de interés (opcional)
        """
        try:
            if n <= 0:
                raise ParametroInvalido("n debe ser > 0.")
            v, _ = self._vi(i)
            return (v ** n) * self.table.npx(n, x)
        except (EdadNoDisponible, ParametroInvalido):
            raise

    # ------------------------------------------------------------------
    # IV. Dotal mixto — Ax_dotal_mixto
    # ------------------------------------------------------------------

    def Ax_dotal_mixto(self, x: int, n: int, i: float = None) -> float:
        """
        Dotal mixto: paga 1 al morir (dentro de n años) o al sobrevivir n años.
        A_{x:n|} = A^1_{x:n|} + n_E_x

        Requiere x >= primera edad consecutiva (por el término temporal).

        Parámetros
        ----------
        x : int   Edad de entrada
        n : int   Plazo en años
        i : float Tasa de interés (opcional)
        """
        try:
            i_val = i if i is not None else self.i
            return self.Ax_temporal(x, n, i_val) + self.nEx(x, n, i_val)
        except (EdadFueraDeRango, EdadNoDisponible, ParametroInvalido):
            raise

    # ------------------------------------------------------------------
    # V. Diferido — Ax_diferido
    # ------------------------------------------------------------------

    def Ax_diferido(self, x: int, m: int, i: float = None) -> float:
        """
        Seguro ordinario de vida diferido m años.
        Paga 1 si (x) muere después de m años.

        m|A_x = m_E_x * A_{x+m}

        Parámetros
        ----------
        x : int   Edad de entrada (debe ser >= primera edad consecutiva)
        m : int   Período de diferimiento
        i : float Tasa de interés (opcional)
        """
        try:
            self.table._check_consecutiva(x)
            if m <= 0:
                raise ParametroInvalido("m debe ser > 0.")
            i_val = i if i is not None else self.i
            xm = x + m
            self.table._check_age(xm)
            return self.nEx(x, m, i_val) * self.Ax(xm, i_val)
        except (EdadFueraDeRango, EdadNoDisponible, ParametroInvalido):
            raise

    # ------------------------------------------------------------------
    # VI. Creciente — IAx
    # ------------------------------------------------------------------

    def IAx(self, x: int, i: float = None) -> float:
        """
        Seguro de vida entera creciente.
        Paga k+1 si (x) muere en el año k+1.

        (IA)_x = sum_{k=0}^{omega-x-1} (k+1) * v^{k+1} * k_p_x * q_{x+k}

        Parámetros
        ----------
        x : int   Edad de entrada (debe ser >= primera edad consecutiva)
        i : float Tasa de interés (opcional)
        """
        try:
            self.table._check_consecutiva(x)
            v, _ = self._vi(i)
            total = 0.0
            for age in self._ages_from(x):
                k = int(age - x)
                kpx = self.table.npx(k, x)
                qxk = self.table.qx(age)
                total += (k + 1) * (v ** (k + 1)) * kpx * qxk
            return total
        except (EdadFueraDeRango, EdadNoDisponible):
            raise

    # ------------------------------------------------------------------
    # VII. Decreciente temporal — DAx
    # ------------------------------------------------------------------

    def DAx(self, x: int, n: int, i: float = None) -> float:
        """
        Seguro temporal decreciente de n años.
        Paga n-k si (x) muere en el año k+1 (dentro de n años).

        (DA)^1_{x:n|} = sum_{k=0}^{n-1} (n-k) * v^{k+1} * k_p_x * q_{x+k}

        Parámetros
        ----------
        x : int   Edad de entrada (debe ser >= primera edad consecutiva)
        n : int   Plazo en años
        i : float Tasa de interés (opcional)
        """
        try:
            self.table._check_consecutiva(x)
            if n <= 0:
                raise ParametroInvalido("n debe ser > 0.")
            v, _ = self._vi(i)
            total = 0.0
            for age in self._ages_range(x, n):
                k = int(age - x)
                kpx = self.table.npx(k, x)
                qxk = self.table.qx(age)
                total += (n - k) * (v ** (k + 1)) * kpx * qxk
            return total
        except (EdadFueraDeRango, EdadNoDisponible, ParametroInvalido):
            raise

    def __repr__(self):
        return f"Insurance(table={self.table}, i={self.i})"
