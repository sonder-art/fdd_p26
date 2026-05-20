"""
Tests para firstact usando la ILT a i=0.06
Valores de referencia: Illustrative Life Table (SOA).
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np
from firstact import MortalityTable, Insurance, Annuity, Premium
from firstact.utils import to_cont, to_disc
from firstact.exceptions import (
    EdadFueraDeRango, EdadNoDisponible,
    ConversionNoAplicable, ParametroInvalido
)


def test_mortality_basico():
    t = MortalityTable.ilt()
    assert abs(t.qx(35) - 0.00201) < 1e-4
    assert abs(t.px(35) - (1 - 0.00201)) < 1e-4
    assert t.lx(0) == 10_000_000
    assert abs(t.npx(10, 35) - t.lx(45)/t.lx(35)) < 1e-10
    assert abs(t.npx(10, 35) + t.nqx(10, 35) - 1.0) < 1e-10
    print("✅ mortality básico OK")


def test_deferred_qx():
    t = MortalityTable.ilt()
    # m|n qx = mpx * nqx+m
    manual = t.npx(5, 35) * t.nqx(10, 40)
    assert abs(t.deferred_qx(5, 10, 35) - manual) < 1e-10
    print("✅ deferred_qx OK")


def test_Ax():
    t = MortalityTable.ilt()
    ins = Insurance(t, i=0.06)
    # Referencia ILT: 1000*A_35 = 128.72
    assert abs(ins.Ax(35) - 0.12872) < 0.001
    # Recursión: Ax = vqx + vpx*Ax+1
    v = 1/1.06
    rec = v*t.qx(35) + v*t.px(35)*ins.Ax(36)
    assert abs(ins.Ax(35) - rec) < 0.0001
    print(f"✅ Ax(35) = {ins.Ax(35):.5f}  (ref: 0.12872)")


def test_nEx():
    t = MortalityTable.ilt()
    ins = Insurance(t, i=0.06)
    # Referencia ILT: 1000*20E_35 = 286.00
    assert abs(ins.nEx(35, 20) - 0.28600) < 0.005
    # Formula: v^n * npx
    assert abs(ins.nEx(35, 20) - (1/1.06)**20 * t.npx(20, 35)) < 1e-10
    print(f"✅ nEx(35,20) = {ins.nEx(35,20):.5f}  (ref: 0.28600)")


def test_dotal_mixto():
    t = MortalityTable.ilt()
    ins = Insurance(t, i=0.06)
    # A_{x:n|} = A^1_{x:n|} + nEx
    A1 = ins.Ax_temporal(35, 20)
    nE = ins.nEx(35, 20)
    Axn = ins.Ax_dotal_mixto(35, 20)
    assert abs(Axn - (A1 + nE)) < 1e-10
    print(f"✅ Ax_dotal_mixto OK: {Axn:.5f} = {A1:.5f} + {nE:.5f}")


def test_ax():
    t = MortalityTable.ilt()
    ins = Insurance(t, i=0.06)
    ann = Annuity(t, i=0.06)
    d = 0.06/1.06
    # Referencia ILT: ä_35 = 15.3926
    assert abs(ann.ax(35) - 15.3926) < 0.05
    # Relación: ä_x = (1-Ax)/d
    assert abs(ann.ax(35) - (1-ins.Ax(35))/d) < 0.01
    # ä_x = ä_{x:n|} + n|ä_x
    axn = ann.ax_temp(35, 20)
    nax = ann.ax_diferida(35, 20)
    assert abs(ann.ax(35) - (axn + nax)) < 0.001
    print(f"✅ ax(35) = {ann.ax(35):.4f}  (ref: 15.3926)")


def test_ax_temp_vencida():
    t = MortalityTable.ilt()
    ann = Annuity(t, i=0.06)
    v = 1/1.06
    # a_{x:n|} = ä_{x:n|} * v
    due = ann.ax_temp(35, 20)
    imm = ann.ax_temp_vencida(35, 20)
    assert abs(imm - due * v) < 1e-10
    print(f"✅ ax_temp_vencida OK: {imm:.4f} = {due:.4f} * v")


def test_prima_vida_entera():
    t = MortalityTable.ilt()
    ins = Insurance(t, i=0.06)
    ann = Annuity(t, i=0.06)
    pre = Premium(t, i=0.06)
    P = pre.prima_vida_entera(35)
    # P = Ax / äx
    assert abs(P - ins.Ax(35)/ann.ax(35)) < 1e-10
    print(f"✅ prima_vida_entera(35) = {P:.6f}")


def test_reservas():
    t = MortalityTable.ilt()
    ins = Insurance(t, i=0.06)
    ann = Annuity(t, i=0.06)
    pre = Premium(t, i=0.06)
    # t=0 debe ser 0
    assert abs(pre.reserva_vida_entera(35, 0)) < 1e-8
    assert abs(pre.reserva_dotal_mixto(35, 20, 0)) < 1e-8
    # t=n debe ser 1 para dotal
    assert abs(pre.reserva_dotal_mixto(35, 20, 20) - 1.0) < 1e-6
    # Fórmula prospectiva: tV = A_{x+t} - P * ä_{x+t}
    P = pre.prima_vida_entera(35)
    tV = pre.reserva_vida_entera(35, 10)
    tV_form = ins.Ax(45) - P * ann.ax(45)
    assert abs(tV - tV_form) < 1e-10
    print(f"✅ reservas OK")


def test_i_sobreescribible():
    t = MortalityTable.ilt()
    ins = Insurance(t, i=0.06)
    Ax_06 = ins.Ax(35)
    Ax_05 = ins.Ax(35, i=0.05)
    Ax_08 = ins.Ax(35, i=0.08)
    # A mayor i, menor valor presente → menor Ax
    assert Ax_08 < Ax_06 < Ax_05
    print(f"✅ i sobreescribible OK: A_35(5%)={Ax_05:.4f} A_35(6%)={Ax_06:.4f} A_35(8%)={Ax_08:.4f}")


def test_to_cont_to_disc():
    import numpy as np
    t = MortalityTable.ilt()
    ins = Insurance(t, i=0.06)
    ann = Annuity(t, i=0.06)
    i = 0.06
    delta = np.log(1+i)
    Ax = ins.Ax(35)
    # Ā = A * i/delta
    Ax_bar = to_cont(Ax, i=i, kind='seguro')
    assert abs(Ax_bar - Ax*(i/delta)) < 1e-10
    # Vuelta: A = Ā * delta/i
    Ax_back = to_disc(Ax_bar, i=i, kind='seguro')
    assert abs(Ax_back - Ax) < 1e-8
    # Anualidad
    ax = ann.ax(35)
    ax_bar = to_cont(ax, i=i, kind='anualidad')
    ax_back = to_disc(ax_bar, i=i, kind='anualidad')
    assert abs(ax_back - ax) < 0.001
    print(f"✅ to_cont/to_disc OK: Ā_35={Ax_bar:.5f}, ā_35={ax_bar:.4f}")


def test_excepciones():
    t = MortalityTable.ilt()
    ins = Insurance(t, i=0.06)
    ann = Annuity(t, i=0.06)
    pre = Premium(t, i=0.06)

    # EdadNoDisponible
    try:
        t.qx(3)
        assert False, "Debería lanzar EdadNoDisponible"
    except EdadNoDisponible:
        pass

    # EdadFueraDeRango — seguros y anualidades con x < 20
    for x in [0, 5, 10, 15]:
        try:
            ins.Ax(x)
            assert False, f"Ax({x}) debería lanzar EdadFueraDeRango"
        except EdadFueraDeRango:
            pass
        try:
            ann.ax(x)
            assert False, f"ax({x}) debería lanzar EdadFueraDeRango"
        except EdadFueraDeRango:
            pass

    # npx con x<20 SÍ funciona si x y x+n están en tabla
    assert abs(t.npx(5, 0) - t.lx(5)/t.lx(0)) < 1e-10
    assert abs(t.npx(10, 5) - t.lx(15)/t.lx(5)) < 1e-10

    # ConversionNoAplicable
    try:
        to_cont(0.286, i=0.06, kind='dotal_puro')
        assert False
    except ConversionNoAplicable:
        pass
    try:
        to_cont(0.327, i=0.06, kind='dotal_mixto')
        assert False
    except ConversionNoAplicable:
        pass

    # ParametroInvalido
    try:
        t.npx(-1, 35)
        assert False
    except ParametroInvalido:
        pass
    try:
        pre.reserva_temporal(35, 20, 25)  # t > n
        assert False
    except ParametroInvalido:
        pass

    print("✅ excepciones OK")


if __name__ == "__main__":
    print("=" * 50)
    print("  firstact v0.2.0 — Tests")
    print("=" * 50)
    test_mortality_basico()
    test_deferred_qx()
    test_Ax()
    test_nEx()
    test_dotal_mixto()
    test_ax()
    test_ax_temp_vencida()
    test_prima_vida_entera()
    test_reservas()
    test_i_sobreescribible()
    test_to_cont_to_disc()
    test_excepciones()
    print("=" * 50)
    print("  Todos los tests pasaron ✅")
    print("=" * 50)
