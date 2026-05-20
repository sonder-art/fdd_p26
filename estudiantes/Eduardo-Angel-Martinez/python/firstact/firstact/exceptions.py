"""
firstact.exceptions
===================
Excepciones propias de la librería firstact.
"""


class FirstActError(Exception):
    """Error base de firstact."""
    pass


class EdadNoDisponible(FirstActError):
    """
    La edad solicitada no existe en la tabla de mortalidad.
    
    Ejemplo:
        t.qx(3)  # 3 no está en la ILT
    """
    pass


class EdadFueraDeRango(FirstActError):
    """
    La edad x está en la zona con saltos de la tabla.
    Los cálculos de seguros y anualidades requieren edades consecutivas
    para sumar año por año correctamente.
    
    En la ILT esto ocurre para x < 20 (edades 0, 5, 10, 15).
    Las funciones de consulta directa (lx, qx, px, npx, nEx) sí funcionan
    para estas edades siempre que x y x+n estén en la tabla.
    
    Ejemplo:
        ins.Ax(5)   # Error — zona con saltos
        ann.ax(10)  # Error — zona con saltos
    """
    pass


class ConversionNoAplicable(FirstActError):
    """
    La conversión discreto↔continuo no aplica para este tipo de seguro
    o anualidad bajo el supuesto UDD.
    
    Aplica SOLO a pagos contingentes por muerte:
        - Seguro ordinario de vida (Ax)
        - Seguro temporal (Ax_temporal)
        - Seguro diferido (Ax_diferido)
        - Seguro creciente (IAx)
        - Seguro decreciente (DAx)
    
    NO aplica a:
        - Dotal puro (nEx): es pago por sobrevivencia, no por muerte
        - Dotal mixto (Ax_dotal_mixto): contiene nEx
    
    Ejemplo:
        to_cont(nEx_val, i=0.06, kind='dotal_puro')   # Error
        to_cont(Axn_val, i=0.06, kind='dotal_mixto')  # Error
    """
    pass


class ParametroInvalido(FirstActError):
    """
    Un parámetro tiene un valor inválido.
    
    Ejemplos:
        t.npx(-1, 35)           # n negativo
        pre.reserva_temporal(35, 20, 25)  # t > n
    """
    pass
