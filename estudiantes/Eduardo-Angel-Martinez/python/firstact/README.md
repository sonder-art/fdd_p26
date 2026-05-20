# firstact

Librería de matemáticas actuariales básicas en Python.  
Basada en la **Illustrative Life Table (ILT)** de la SOA a $i = 6\%$.

---

## Instalación

```bash
pip install -r requirements.txt
pip install -e .
```

---

## Módulos

| Módulo | Descripción |
|---|---|
| `MortalityTable` | Tablas de mortalidad: lx, qx, px, dx, npx, nqx, ex |
| `Insurance` | Seguros de vida discretos (K_x, pago al final del año de muerte) |
| `Annuity` | Anualidades contingentes discretas |
| `Premium` | Primas netas niveladas y reservas prospectivas |
| `utils` | Conversiones discreto ↔ continuo bajo UDD |
| `exceptions` | Excepciones propias de la librería |

---

## Uso rápido

```python
from firstact import MortalityTable, Insurance, Annuity, Premium
from firstact.utils import to_cont, to_disc

t   = MortalityTable.ilt()   # ILT incluida (SOA)
ins = Insurance(t, i=0.06)
ann = Annuity(t, i=0.06)
pre = Premium(t, i=0.06)
```

También puedes cargar tu propia tabla desde un CSV con columnas `x`, `lx`, `qx`:

```python
t = MortalityTable("mi_tabla.csv")
```

---

## Tabla de Mortalidad

### Nota sobre edades en la ILT

La ILT tiene edades **0, 5, 10, 15** y luego **20–110 consecutivas**.  
Las funciones de consulta directa (`lx`, `qx`, `npx`, etc.) funcionan para cualquier edad disponible.  
Los cálculos de seguros y anualidades **requieren x >= 20** porque suman año por año.

### Funciones disponibles

```python
t.lx(35)                   # l_35 — número de vivos
t.qx(35)                   # q_35 — probabilidad de morir entre 35 y 36
t.px(35)                   # p_35 = 1 - q_35
t.dx(35)                   # d_35 — muertes entre 35 y 36

t.npx(10, 35)              # 10_p_35 = l_45 / l_35
t.nqx(10, 35)              # 10_q_35 = 1 - 10_p_35
t.deferred_qx(5, 10, 35)   # 5|10_q_35 = 5_p_35 * 10_q_40

t.ex(35)                   # e_35 curtate (años completos)
t.ex(35, curtate=False)    # ê_35 completa (≈ e_35 + 0.5)

t.summary(35)              # diccionario con todos los valores
t.ages                     # array de edades disponibles
t.omega                    # edad máxima
t.primera_consecutiva      # primera edad consecutiva (20 en ILT)
```

---

## Seguros de Vida

Todos los seguros son **discretos**: la variable aleatoria es $K_x$ (años completos) y el beneficio se paga al **final del año de muerte**.

Requieren **x >= 20** en la ILT.  
Puedes sobreescribir la tasa `i` en cada función.

### I. Seguro Ordinario de Vida

$$A_x = \sum_{k=0}^{\omega-x-1} v^{k+1} \cdot {_k}p_x \cdot q_{x+k}$$

```python
ins.Ax(35)           # A_35
ins.Ax(35, i=0.05)   # A_35 con i=5%
```

### II. Seguro Temporal n años

$$A^1_{x:\overline{n}|} = \sum_{k=0}^{n-1} v^{k+1} \cdot {_k}p_x \cdot q_{x+k}$$

```python
ins.Ax_temporal(35, 20)          # A^1_{35:20|}
ins.Ax_temporal(35, 20, i=0.05)  # con i=5%
```

### III. Dotal Puro n años

$$_nE_x = v^n \cdot {_n}p_x$$

Solo requiere que `x` y `x+n` estén en la tabla (no necesita x >= 20).

```python
ins.nEx(35, 20)          # 20_E_35
ins.nEx(0, 5)            # 5_E_0 — válido aunque x < 20
```

### IV. Dotal Mixto n años

$$A_{x:\overline{n}|} = A^1_{x:\overline{n}|} + {_n}E_x$$

```python
ins.Ax_dotal_mixto(35, 20)
```

### V. Seguro Diferido m años

$$_{m|}A_x = {_m}E_x \cdot A_{x+m}$$

```python
ins.Ax_diferido(35, 10)   # 10|A_35
```

### VI. Seguro Creciente

$$(IA)_x = \sum_{k=0}^{\omega-x-1} (k+1) \cdot v^{k+1} \cdot {_k}p_x \cdot q_{x+k}$$

```python
ins.IAx(35)
```

### VII. Seguro Decreciente Temporal

$$(DA)^1_{x:\overline{n}|} = \sum_{k=0}^{n-1} (n-k) \cdot v^{k+1} \cdot {_k}p_x \cdot q_{x+k}$$

```python
ins.DAx(35, 20)
```

---

## Anualidades Contingentes

Todas las anualidades son **discretas** (variable $K_x$).  
Requieren **x >= 20** en la ILT.

### I. Anticipada Vitalicia

$$\ddot{a}_x = \sum_{k=0}^{\omega-x} v^k \cdot {_k}p_x$$

```python
ann.ax(35)
```

### Ibis. Vencida Vitalicia

$$a_x = \ddot{a}_x - 1$$

```python
ann.ax_vencida(35)
```

### II. Anticipada Temporal n años

$$\ddot{a}_{x:\overline{n}|} = \sum_{k=0}^{n-1} v^k \cdot {_k}p_x$$

```python
ann.ax_temp(35, 20)
```

### IIbis. Vencida Temporal n años

$$a_{x:\overline{n}|} = \ddot{a}_{x:\overline{n}|} \cdot v$$

```python
ann.ax_temp_vencida(35, 20)
```

### III. Diferida Vitalicia m años

$$_{m|}\ddot{a}_x = {_m}E_x \cdot \ddot{a}_{x+m}$$

```python
ann.ax_diferida(35, 10)
```

### IV. Diferida Temporal m|n años

$$_{m|n}\ddot{a}_x = {_m}E_x \cdot \ddot{a}_{x+m:\overline{n}|}$$

```python
ann.ax_diferida_temp(35, 10, 20)
```

---

## Primas Netas

Todas bajo el **principio de equivalencia**: $E[Z] = P \cdot E[Y]$

### Primas Únicas Netas (PUN)

```python
pre.prima_unica_vida_entera(35)
pre.prima_unica_temporal(35, 20)
pre.prima_unica_dotal_mixto(35, 20)
```

### Primas Anuales Niveladas

```python
pre.prima_vida_entera(35)              # P = A_x / ä_x
pre.prima_temporal(35, 20)             # P = A^1_{x:n|} / ä_{x:n|}
pre.prima_dotal_mixto(35, 20)          # P = A_{x:n|} / ä_{x:n|}
pre.prima_vida_entera_limitada(35, 10) # h_P = A_x / ä_{x:h|}
```

### Primas Fraccionadas (aproximación UDD)

$$P^{(m)} = P \cdot \frac{i}{i^{(m)}} \cdot \frac{1}{m}$$

```python
P = pre.prima_vida_entera(35)
pre.prima_fraccionada(P, m=12)   # prima mensual
pre.prima_fraccionada(P, m=4)    # prima trimestral
pre.prima_fraccionada(P, m=2)    # prima semestral
```

---

## Reservas Prospectivas

$$_tV = \text{VP(beneficios futuros)} - P \cdot \text{VP(primas futuras)}$$

```python
pre.reserva_vida_entera(35, t=10)        # 10_V(A_35)
pre.reserva_temporal(35, 20, t=10)       # 10_V temporal
pre.reserva_dotal_mixto(35, 20, t=10)    # 10_V dotal mixto

# Tabla completa t = 0, 1, ..., n
pre.tabla_reservas(35, 20, kind='dotal_mixto')
pre.tabla_reservas(35, 20, kind='temporal')
pre.tabla_reservas(35, 20, kind='vida_entera')
```

---

## Conversiones Discreto ↔ Continuo

Bajo el supuesto **UDD** (Distribución Uniforme de Muertes):

$$\bar{A}_x = A_x \cdot \frac{i}{\delta} \qquad \bar{a}_x = \frac{1 - \bar{A}_x}{\delta}$$

donde $\delta = \ln(1+i)$.

```python
from firstact.utils import to_cont, to_disc

# Discreto → Continuo
Ax_bar = to_cont(ins.Ax(35), i=0.06, kind='seguro')     # Ā_35
ax_bar = to_cont(ann.ax(35), i=0.06, kind='anualidad')  # ā_35

# Continuo → Discreto
Ax = to_disc(Ax_bar, i=0.06, kind='seguro')
ax = to_disc(ax_bar, i=0.06, kind='anualidad')
```

### ⚠️ No aplica para dotal puro ni dotal mixto

```python
to_cont(ins.nEx(35,20), i=0.06, kind='dotal_puro')      # ConversionNoAplicable
to_cont(ins.Ax_dotal_mixto(35,20), i=0.06, kind='dotal_mixto')  # ConversionNoAplicable
```

El dotal puro $_nE_x = v^n \cdot {_n}p_x$ es un pago de **sobrevivencia**, no de muerte, y no tiene versión continua bajo UDD.

---

## Excepciones

| Excepción | Cuándo ocurre |
|---|---|
| `EdadNoDisponible` | La edad no existe en la tabla |
| `EdadFueraDeRango` | x < 20 en la ILT (zona con saltos) para seguros/anualidades |
| `ConversionNoAplicable` | `to_cont`/`to_disc` con dotal puro o dotal mixto |
| `ParametroInvalido` | n negativo, t > n, m <= 0, etc. |

```python
from firstact.exceptions import EdadFueraDeRango, EdadNoDisponible
from firstact.exceptions import ConversionNoAplicable, ParametroInvalido

try:
    ins.Ax(5)
except EdadFueraDeRango as e:
    print(e)

try:
    t.qx(3)
except EdadNoDisponible as e:
    print(e)
```

---

## Ejemplo completo

```python
from firstact import MortalityTable, Insurance, Annuity, Premium
from firstact.utils import to_cont

t   = MortalityTable.ilt()
ins = Insurance(t, i=0.06)
ann = Annuity(t, i=0.06)
pre = Premium(t, i=0.06)

# Persona de 30 años, seguro dotal mixto 25 años, SA = $1,000,000
SA, x, n = 1_000_000, 30, 25

P      = pre.prima_dotal_mixto(x, n) * SA
P_mens = pre.prima_fraccionada(P, m=12)
R10    = pre.reserva_dotal_mixto(x, n, t=10) * SA

print(f"Prima anual:       ${P:>12,.2f}")
print(f"Prima mensual:     ${P_mens:>12,.2f}")
print(f"Reserva año 10:    ${R10:>12,.2f}")

# Versión continua
Ax_bar = to_cont(ins.Ax(x), i=0.06, kind='seguro')
print(f"Ā_{x} (continuo):  {Ax_bar:.5f}")
```

---

## Tests

```bash
python tests/test_firstact.py
```
