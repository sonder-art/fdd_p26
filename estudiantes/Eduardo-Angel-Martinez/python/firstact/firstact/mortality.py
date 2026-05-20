"""
firstact.mortality
==================
Módulo para trabajar con tablas de mortalidad.
Permite cargar una tabla y consultar todas las funciones
biométricas clásicas: lx, qx, px, dx, nqx, npx, ex, etc.
"""

import numpy as np
import pandas as pd
from pathlib import Path
from .exceptions import EdadNoDisponible, EdadFueraDeRango, ParametroInvalido

_DATA_DIR = Path(__file__).parent / "data"
_ILT_PATH = _DATA_DIR / "ILT.csv"


class MortalityTable:
    """
    Representa una tabla de mortalidad y expone todas las
    funciones biométricas clásicas.

    Parámetros
    ----------
    source : str | Path | pd.DataFrame
        Ruta a un CSV con columnas [x, lx, qx] como mínimo,
        o un DataFrame ya cargado.

    Ejemplos
    --------
    >>> from firstact import MortalityTable
    >>> t = MortalityTable.ilt()
    >>> t.qx(35)
    0.00201
    >>> t.npx(10, 35)
    0.972761
    """

    def __init__(self, source):
        try:
            if isinstance(source, pd.DataFrame):
                df = source.copy()
            else:
                df = pd.read_csv(source)

            df.columns = [c.strip().lower() for c in df.columns]
            required = {"x", "lx", "qx"}
            missing = required - set(df.columns)
            if missing:
                raise ParametroInvalido(
                    f"La tabla debe contener las columnas: {required}. "
                    f"Faltan: {missing}"
                )
            df = df.sort_values("x").reset_index(drop=True)
            df = df.set_index("x")
            self._df = df
            self._ages = np.array(df.index)
            self._lx = df["lx"].values.astype(float)
            self._qx = df["qx"].values.astype(float)

            # Detectar primera edad desde la cual son consecutivas
            diffs = np.diff(self._ages)
            consec_idx = np.argmax(diffs == 1)
            self._primera_consecutiva = int(self._ages[consec_idx])
        except ParametroInvalido:
            raise

    @classmethod
    def ilt(cls):
        """Carga la Illustrative Life Table (SOA) incluida en el paquete."""
        return cls(_ILT_PATH)

    # ------------------------------------------------------------------
    # Validaciones internas
    # ------------------------------------------------------------------

    def _check_age(self, x: int) -> None:
        """Lanza EdadNoDisponible si x no está en la tabla."""
        if x not in self._df.index:
            raise EdadNoDisponible(
                f"La edad {x} no está en la tabla. "
                f"Rango disponible: {int(self._ages[0])}–{int(self._ages[-1])}."
            )

    def _check_consecutiva(self, x: int) -> None:
        """
        Lanza EdadFueraDeRango si x está en zona con saltos.
        Requerido por seguros y anualidades que suman año por año.
        """
        self._check_age(x)
        if x < self._primera_consecutiva:
            raise EdadFueraDeRango(
                f"x={x} está en la zona con saltos de la tabla "
                f"{list(self._ages[self._ages < self._primera_consecutiva])}. "
                f"Los cálculos de seguros y anualidades requieren "
                f"x >= {self._primera_consecutiva}."
            )

    # ------------------------------------------------------------------
    # Propiedades
    # ------------------------------------------------------------------

    @property
    def ages(self) -> np.ndarray:
        """Edades disponibles en la tabla."""
        return self._ages.copy()

    @property
    def omega(self) -> int:
        """Edad máxima de la tabla (última con lx > 0)."""
        return int(self._ages[self._lx > 0][-1])

    @property
    def primera_consecutiva(self) -> int:
        """Primera edad desde la cual las edades son consecutivas."""
        return self._primera_consecutiva

    # ------------------------------------------------------------------
    # Funciones de consulta directa
    # ------------------------------------------------------------------

    def lx(self, x: int) -> float:
        """Número de vivos a edad x."""
        try:
            self._check_age(x)
            return float(self._df.loc[x, "lx"])
        except EdadNoDisponible:
            raise

    def qx(self, x: int) -> float:
        """Probabilidad de morir entre x y x+1. q_x"""
        try:
            self._check_age(x)
            return float(self._df.loc[x, "qx"])
        except EdadNoDisponible:
            raise

    def px(self, x: int) -> float:
        """Probabilidad de sobrevivir de x a x+1. p_x = 1 - q_x"""
        try:
            return 1.0 - self.qx(x)
        except EdadNoDisponible:
            raise

    def dx(self, x: int) -> float:
        """Número esperado de muertes entre x y x+1. d_x"""
        try:
            self._check_age(x)
            idx = int(np.searchsorted(self._ages, x))
            if idx + 1 < len(self._lx):
                return self._lx[idx] - self._lx[idx + 1]
            return self._lx[idx]
        except EdadNoDisponible:
            raise

    # ------------------------------------------------------------------
    # Funciones de n períodos
    # ------------------------------------------------------------------

    def npx(self, n: int, x: int) -> float:
        """
        Probabilidad de que (x) sobreviva n años.
        n_p_x = l_{x+n} / l_x

        Solo requiere que x y x+n estén en la tabla.
        No requiere edades consecutivas.
        """
        try:
            if n < 0:
                raise ParametroInvalido("n debe ser >= 0.")
            if n == 0:
                return 1.0
            self._check_age(x)
            x_n = x + n
            if x_n > self.omega:
                return 0.0
            self._check_age(x_n)
            return self.lx(x_n) / self.lx(x)
        except (EdadNoDisponible, ParametroInvalido):
            raise

    def nqx(self, n: int, x: int) -> float:
        """
        Probabilidad de que (x) muera dentro de n años.
        n_q_x = 1 - n_p_x
        """
        try:
            return 1.0 - self.npx(n, x)
        except (EdadNoDisponible, ParametroInvalido):
            raise

    def deferred_qx(self, m: int, n: int, x: int) -> float:
        """
        Probabilidad de morir entre x+m y x+m+n.
        m|n q_x = m_p_x * n_q_{x+m}

        Solo requiere que x, x+m y x+m+n estén en la tabla.
        """
        try:
            if m < 0 or n < 0:
                raise ParametroInvalido("m y n deben ser >= 0.")
            return self.npx(m, x) * self.nqx(n, x + m)
        except (EdadNoDisponible, ParametroInvalido):
            raise

    # ------------------------------------------------------------------
    # Esperanza de vida
    # ------------------------------------------------------------------

    def ex(self, x: int, curtate: bool = True) -> float:
        """
        Esperanza de vida a edad x usando edades disponibles en la tabla.

        Parámetros
        ----------
        curtate : bool
            True  → e_x (discreta, años completos)
            False → ê_x (completa, aprox e_x + 0.5)
        """
        try:
            self._check_age(x)
            ages_from_x = self._ages[self._ages > x]
            result = 0.0
            for age in ages_from_x:
                n = int(age - x)
                result += self.npx(n, x)
            if not curtate:
                result += 0.5
            return result
        except (EdadNoDisponible, ParametroInvalido):
            raise

    # ------------------------------------------------------------------
    # Resumen
    # ------------------------------------------------------------------

    def summary(self, x: int) -> dict:
        """Resumen de funciones biométricas para la edad x."""
        try:
            self._check_age(x)
            result = {
                "x": x,
                "lx": self.lx(x),
                "dx": self.dx(x),
                "qx": self.qx(x),
                "px": self.px(x),
            }
            for n in [10, 20]:
                if (x + n) in self._df.index:
                    result[f"{n}px"] = round(self.npx(n, x), 6)
                    result[f"{n}qx"] = round(self.nqx(n, x), 6)
            result["ex (curtate)"]  = round(self.ex(x), 4)
            result["ex (completa)"] = round(self.ex(x, curtate=False), 4)
            return result
        except EdadNoDisponible:
            raise

    def __repr__(self):
        return (
            f"MortalityTable(edades={self._ages[0]}–{self._ages[-1]}, "
            f"omega={self.omega}, n={len(self._ages)}, "
            f"consecutivas_desde={self._primera_consecutiva})"
        )
