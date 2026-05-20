"""
firstact.premiums
=================
Primas netas niveladas y reservas prospectivas.

Principio de equivalencia: E[Z] = P * E[Y]
    donde Z = v.a. del beneficio, Y = v.a. de las primas

Primas implementadas:
  - Primas únicas netas (PUN)
  - Primas anuales niveladas
  - Primas fraccionadas m veces al año (aproximación UDD)

Reservas implementadas (método prospectivo):
  t_V = VP(beneficios futuros) - P * VP(primas futuras)
"""

import numpy as np
from .mortality import MortalityTable
from .insurance import Insurance
from .annuities import Annuity
from .exceptions import EdadFueraDeRango, EdadNoDisponible, ParametroInvalido


class Premium:
    """
    Calcula primas netas y reservas bajo el principio de equivalencia.

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
        self._ins = Insurance(table, i)
        self._ann = Annuity(table, i)

    def _get_i(self, i_override):
        return i_override if i_override is not None else self.i

    # ------------------------------------------------------------------
    # Primas únicas netas (PUN)
    # ------------------------------------------------------------------

    def prima_unica_vida_entera(self, x: int, i: float = None) -> float:
        """
        Prima única neta del seguro ordinario de vida.
        PUN = A_x

        Parámetros
        ----------
        x : int   Edad de entrada
        i : float Tasa de interés (opcional)
        """
        try:
            return self._ins.Ax(x, self._get_i(i))
        except (EdadFueraDeRango, EdadNoDisponible):
            raise

    def prima_unica_temporal(self, x: int, n: int, i: float = None) -> float:
        """
        Prima única neta del seguro temporal n años.
        PUN = A^1_{x:n|}
        """
        try:
            return self._ins.Ax_temporal(x, n, self._get_i(i))
        except (EdadFueraDeRango, EdadNoDisponible, ParametroInvalido):
            raise

    def prima_unica_dotal_mixto(self, x: int, n: int, i: float = None) -> float:
        """
        Prima única neta del seguro dotal mixto n años.
        PUN = A_{x:n|}
        """
        try:
            return self._ins.Ax_dotal_mixto(x, n, self._get_i(i))
        except (EdadFueraDeRango, EdadNoDisponible, ParametroInvalido):
            raise

    # ------------------------------------------------------------------
    # Primas anuales niveladas
    # ------------------------------------------------------------------

    def prima_vida_entera(self, x: int, i: float = None) -> float:
        """
        Prima anual nivelada del seguro ordinario de vida.
        Pagos durante toda la vida.

        P(A_x) = A_x / ä_x

        Parámetros
        ----------
        x : int   Edad de entrada
        i : float Tasa de interés (opcional)
        """
        try:
            i_val = self._get_i(i)
            Ax = self._ins.Ax(x, i_val)
            ax = self._ann.ax(x, i_val)
            return Ax / ax
        except (EdadFueraDeRango, EdadNoDisponible):
            raise

    def prima_temporal(self, x: int, n: int, i: float = None) -> float:
        """
        Prima anual nivelada del seguro temporal de n años.
        Pagos durante n años o hasta la muerte.

        P(A^1_{x:n|}) = A^1_{x:n|} / ä_{x:n|}
        """
        try:
            i_val = self._get_i(i)
            A = self._ins.Ax_temporal(x, n, i_val)
            ax_n = self._ann.ax_temp(x, n, i_val)
            if ax_n == 0:
                return 0.0
            return A / ax_n
        except (EdadFueraDeRango, EdadNoDisponible, ParametroInvalido):
            raise

    def prima_dotal_mixto(self, x: int, n: int, i: float = None) -> float:
        """
        Prima anual nivelada del seguro dotal mixto de n años.

        P(A_{x:n|}) = A_{x:n|} / ä_{x:n|}
        """
        try:
            i_val = self._get_i(i)
            A = self._ins.Ax_dotal_mixto(x, n, i_val)
            ax_n = self._ann.ax_temp(x, n, i_val)
            if ax_n == 0:
                return 0.0
            return A / ax_n
        except (EdadFueraDeRango, EdadNoDisponible, ParametroInvalido):
            raise

    def prima_vida_entera_limitada(self, x: int, h: int, i: float = None) -> float:
        """
        Prima anual nivelada del seguro de vida entera con pagos
        limitados a h años.

        h_P(A_x) = A_x / ä_{x:h|}
        """
        try:
            i_val = self._get_i(i)
            Ax = self._ins.Ax(x, i_val)
            ax_h = self._ann.ax_temp(x, h, i_val)
            if ax_h == 0:
                return 0.0
            return Ax / ax_h
        except (EdadFueraDeRango, EdadNoDisponible, ParametroInvalido):
            raise

    # ------------------------------------------------------------------
    # Primas fraccionadas (m pagos al año) — aproximación UDD
    # ------------------------------------------------------------------

    def prima_fraccionada(self, prima_anual: float, m: int, i: float = None) -> float:
        """
        Convierte una prima anual en prima fraccionada de m pagos al año.
        Aproximación UDD: P^(m) = P * i / i^(m)

        donde i^(m) = m * [(1+i)^(1/m) - 1]

        Parámetros
        ----------
        prima_anual : float  Prima anual nivelada
        m : int              Pagos al año (2=semestral, 4=trimestral, 12=mensual)
        i : float            Tasa de interés (opcional)

        Retorna
        -------
        float : Prima por pago (no anual)
        """
        try:
            if m <= 0:
                raise ParametroInvalido("m debe ser > 0.")
            i_val = self._get_i(i)
            i_m = m * ((1 + i_val) ** (1 / m) - 1)
            return prima_anual * i_val / i_m / m
        except ParametroInvalido:
            raise

    # ------------------------------------------------------------------
    # Reservas prospectivas
    # ------------------------------------------------------------------

    def reserva_vida_entera(self, x: int, t: int, i: float = None) -> float:
        """
        Reserva prospectiva al tiempo t del seguro ordinario de vida.

        t_V(A_x) = A_{x+t} - P(A_x) * ä_{x+t}

        Parámetros
        ----------
        x : int   Edad de entrada
        t : int   Tiempo transcurrido
        i : float Tasa de interés (opcional)
        """
        try:
            if t < 0:
                raise ParametroInvalido("t debe ser >= 0.")
            i_val = self._get_i(i)
            P = self.prima_vida_entera(x, i_val)
            A_xt = self._ins.Ax(x + t, i_val)
            ax_xt = self._ann.ax(x + t, i_val)
            return A_xt - P * ax_xt
        except (EdadFueraDeRango, EdadNoDisponible, ParametroInvalido):
            raise

    def reserva_temporal(self, x: int, n: int, t: int, i: float = None) -> float:
        """
        Reserva prospectiva al tiempo t del seguro temporal.

        t_V = A^1_{x+t:n-t|} - P * ä_{x+t:n-t|}

        Parámetros
        ----------
        x : int   Edad de entrada
        n : int   Plazo del seguro
        t : int   Tiempo transcurrido (0 <= t <= n)
        i : float Tasa de interés (opcional)
        """
        try:
            if t < 0:
                raise ParametroInvalido("t debe ser >= 0.")
            if t > n:
                raise ParametroInvalido("t no puede ser mayor que n.")
            if t == n:
                return 0.0
            i_val = self._get_i(i)
            P = self.prima_temporal(x, n, i_val)
            rem = n - t
            A_rem = self._ins.Ax_temporal(x + t, rem, i_val)
            ax_rem = self._ann.ax_temp(x + t, rem, i_val)
            return A_rem - P * ax_rem
        except (EdadFueraDeRango, EdadNoDisponible, ParametroInvalido):
            raise

    def reserva_dotal_mixto(self, x: int, n: int, t: int, i: float = None) -> float:
        """
        Reserva prospectiva al tiempo t del seguro dotal mixto.

        t_V = A_{x+t:n-t|} - P * ä_{x+t:n-t|}

        Parámetros
        ----------
        x : int   Edad de entrada
        n : int   Plazo del seguro
        t : int   Tiempo transcurrido (0 <= t <= n)
        i : float Tasa de interés (opcional)
        """
        try:
            if t < 0:
                raise ParametroInvalido("t debe ser >= 0.")
            if t > n:
                raise ParametroInvalido("t no puede ser mayor que n.")
            if t == n:
                return 1.0
            i_val = self._get_i(i)
            P = self.prima_dotal_mixto(x, n, i_val)
            rem = n - t
            A_rem = self._ins.Ax_dotal_mixto(x + t, rem, i_val)
            ax_rem = self._ann.ax_temp(x + t, rem, i_val)
            return A_rem - P * ax_rem
        except (EdadFueraDeRango, EdadNoDisponible, ParametroInvalido):
            raise

    def tabla_reservas(self, x: int, n: int, kind: str = "dotal_mixto",
                       i: float = None) -> list:
        """
        Tabla de reservas prospectivas para t = 0, 1, ..., n.

        Parámetros
        ----------
        x    : int   Edad de entrada
        n    : int   Plazo del seguro
        kind : str   'vida_entera', 'temporal' o 'dotal_mixto'
        i    : float Tasa de interés (opcional)
        """
        try:
            if kind not in ("vida_entera", "temporal", "dotal_mixto"):
                raise ParametroInvalido(
                    "kind debe ser 'vida_entera', 'temporal' o 'dotal_mixto'."
                )
            results = []
            for t in range(n + 1):
                if kind == "vida_entera":
                    v = self.reserva_vida_entera(x, t, i)
                elif kind == "temporal":
                    v = self.reserva_temporal(x, n, t, i)
                else:
                    v = self.reserva_dotal_mixto(x, n, t, i)
                results.append({"t": t, "reserva": round(v, 6)})
            return results
        except (EdadFueraDeRango, EdadNoDisponible, ParametroInvalido):
            raise

    def __repr__(self):
        return f"Premium(table={self.table}, i={self.i})"
