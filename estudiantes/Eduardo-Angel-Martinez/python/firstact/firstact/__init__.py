"""
firstact
========
Librería de matemáticas actuariales básicas en Python.

Módulos
-------
MortalityTable : Tablas de mortalidad y funciones biométricas
Insurance      : Seguros de vida discretos (K_x)
Annuity        : Anualidades contingentes discretas
Premium        : Primas netas niveladas y reservas prospectivas
utils          : Conversiones discreto ↔ continuo (UDD)
exceptions     : Excepciones propias de la librería

Uso rápido
----------
>>> from firstact import MortalityTable, Insurance, Annuity, Premium
>>> from firstact.utils import to_cont, to_disc
>>>
>>> t   = MortalityTable.ilt()          # ILT (SOA), i=6% por default
>>> ins = Insurance(t, i=0.06)
>>> ann = Annuity(t, i=0.06)
>>> pre = Premium(t, i=0.06)
>>>
>>> # Tabla de mortalidad
>>> t.qx(35)                            # q_35
>>> t.npx(10, 35)                       # 10_p_35
>>> t.nqx(10, 35)                       # 10_q_35
>>> t.deferred_qx(5, 10, 35)           # 5|10_q_35
>>> t.ex(35)                            # e_35 (curtate)
>>>
>>> # Seguros (discretos, pago al final del año de muerte)
>>> ins.Ax(35)                          # A_35 ordinario
>>> ins.Ax_temporal(35, 20)             # A^1_{35:20|}
>>> ins.nEx(35, 20)                     # 20_E_35 dotal puro
>>> ins.Ax_dotal_mixto(35, 20)          # A_{35:20|} dotal mixto
>>> ins.Ax_diferido(35, 10)             # 10|A_35
>>> ins.IAx(35)                         # (IA)_35 creciente
>>> ins.DAx(35, 20)                     # (DA)^1_{35:20|} decreciente
>>>
>>> # Anualidades (discretas, K_x)
>>> ann.ax(35)                          # ä_35 anticipada vitalicia
>>> ann.ax_vencida(35)                  # a_35 vencida vitalicia
>>> ann.ax_temp(35, 20)                 # ä_{35:20|} temporal anticipada
>>> ann.ax_temp_vencida(35, 20)         # a_{35:20|} temporal vencida
>>> ann.ax_diferida(35, 10)             # 10|ä_35
>>> ann.ax_diferida_temp(35, 10, 20)    # 10|20 ä_35
>>>
>>> # Primas netas (principio de equivalencia)
>>> pre.prima_vida_entera(35)           # P(A_35)
>>> pre.prima_temporal(35, 20)          # P(A^1_{35:20|})
>>> pre.prima_dotal_mixto(35, 20)       # P(A_{35:20|})
>>> pre.prima_vida_entera_limitada(35, 10)  # 10_P(A_35)
>>> pre.prima_fraccionada(P, m=12)      # prima mensual (UDD)
>>>
>>> # Reservas prospectivas
>>> pre.reserva_vida_entera(35, t=10)   # 10_V(A_35)
>>> pre.reserva_temporal(35, 20, t=10)  # 10_V temporal
>>> pre.reserva_dotal_mixto(35, 20, t=10) # 10_V dotal mixto
>>> pre.tabla_reservas(35, 20)          # t=0..n
>>>
>>> # Conversiones discreto ↔ continuo (UDD)
>>> to_cont(ins.Ax(35), i=0.06, kind='seguro')     # Ā_35
>>> to_cont(ann.ax(35), i=0.06, kind='anualidad')  # ā_35
>>> to_disc(0.1326,     i=0.06, kind='seguro')     # A_35
"""

from .mortality import MortalityTable
from .insurance import Insurance
from .annuities import Annuity
from .premiums import Premium
from . import utils
from . import exceptions

__all__ = [
    "MortalityTable",
    "Insurance",
    "Annuity",
    "Premium",
    "utils",
    "exceptions",
]

__version__ = "0.2.0"
__author__ = "firstact"
