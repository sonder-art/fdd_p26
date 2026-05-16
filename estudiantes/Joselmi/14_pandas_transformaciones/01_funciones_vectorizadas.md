# Funciones vectorizadas: apply, map y transform

La pregunta central es siempre la misma: **¿sobre que objeto corre mi funcion?**

Esa pregunta parece pequena, pero en pandas decide casi todo: si tu funcion recibira un escalar o una Serie, si el resultado tendra la misma longitud que la entrada y si estas escribiendo una transformacion natural o un workaround costoso.

Cuando alguien dice "use `apply` y funciono", muchas veces lo que en realidad paso es que pandas tolero una operacion que podia haberse expresado de forma mas clara con metodos vectorizados nativos. Por eso conviene pensar en `map`, `apply` y `transform` como herramientas con contratos distintos, no como variantes intercambiables.

```
¿Que recibe f()?
─────────────────────────────────────────────────────────
Series.map(f)              → 1 valor escalar por llamada
Series.apply(f)            → 1 valor escalar por llamada

DataFrame.apply(f, axis=0) → 1 columna completa (Series)
DataFrame.apply(f, axis=1) → 1 fila completa (Series)

DataFrame.map(f)           → 1 valor escalar (celda a celda)

DataFrame.pipe(f)          → el DataFrame entero
```

La confusion mas comun: `DataFrame.apply(axis=0)` no aplica `f` a cada celda — aplica `f` a cada **columna**. Si tu funcion espera un escalar y recibes una Serie, falla de maneras inesperadas.

Una regla practica:

- si quieres transformar **cada valor** de una Serie, piensa primero en `Series.map()`
- si quieres transformar **cada fila o columna** de un DataFrame, piensa en `DataFrame.apply()`
- si quieres un resultado **del mismo tamano** que la entrada, piensa en `transform()`
- si quieres operar sobre **todo el DataFrame encadenado**, piensa en `pipe()`

Antes de usar cualquiera de estos metodos, preguntate tambien si ya existe una operacion vectorizada de pandas o NumPy. Por ejemplo, `s * 2`, `s.str.lower()`, `s.dt.year` o `df["a"] + df["b"]` suelen ser mas expresivos y mas rapidos que envolver esa logica dentro de `apply`.

## El contrato de output importa

Lo que `f` devuelve determina la forma del resultado:

| `f` devuelve | `Series.apply` devuelve | `DataFrame.apply` devuelve |
|---|---|---|
| escalar | Serie | Serie |
| Serie (mismo indice) | DataFrame | DataFrame |
| Serie (indice diferente) | DataFrame con NaN | DataFrame con NaN |
| dict | DataFrame | DataFrame |

Esto no es solo un detalle tecnico: es la razon por la que a veces `apply` "explota" una columna en varias, a veces devuelve una Serie y a veces produce alineaciones con `NaN`. pandas intenta construir una estructura coherente a partir de lo que tu funcion devuelve en cada llamada.

Dos implicaciones importantes:

- Si tu funcion devuelve estructuras inconsistentes entre llamadas, el resultado sera dificil de leer y de depurar.
- Si dependes de que el output tenga forma estable, conviene definir esa forma explicitamente y no dejar que pandas la infiera.

En otras palabras, con `apply` no solo importan los argumentos de entrada; tambien importa mucho la disciplina con la que diseñas el valor de retorno.

## `map` y `apply` en Series: parecidos, pero no identicos

En una `Series`, tanto `map` como `apply` trabajan valor por valor, pero su uso tipico no es exactamente el mismo:

- `map` comunica una transformacion elemento a elemento.
- `apply` es mas general, pero justamente por eso a veces oculta la intencion.

`map` suele ser la mejor opcion cuando:

- aplicas una funcion simple a cada valor
- haces recodificacion con diccionarios
- quieres expresar claramente que el nivel de operacion es escalar

Ejemplos tipicos:

```python
s.map(str.upper)
s.map({"CDMX": "Ciudad de Mexico", "MTY": "Monterrey"})
```

`Series.apply()` sigue siendo util, pero en practica muchas veces `map()` comunica mejor la idea. Si la operacion ya existe como accessor especializado, mejor aun:

```python
s.str.upper()
s.astype("string")
s.dt.day_name()
```

La jerarquia mental recomendada es:

1. Metodo vectorizado especializado (`.str`, `.dt`, operaciones aritmeticas, comparaciones, etc.)
2. `map()` para transformacion escalar simple
3. `apply()` cuando realmente necesitas una funcion mas flexible

## `transform` vs `apply`

Misma firma, contrato diferente:

- `apply`: puede cambiar la forma del resultado — devuelve lo que devuelva `f`
- `transform`: **debe** devolver un objeto del mismo tamano que la entrada — util con `groupby`

El caso clasico de `transform`: agregar una columna con el promedio del grupo sin perder filas.

```python
# apply: colapsa a un valor por grupo
df.groupby("ciudad")["salario"].apply(np.mean)    # → Serie con un valor por ciudad

# transform: mantiene la forma original, repite el valor por grupo
df["salario_medio_ciudad"] = df.groupby("ciudad")["salario"].transform(np.mean)  # → Serie misma longitud
```

La diferencia conceptual es profunda:

- `apply` pregunta: "¿que quieres producir a partir de este grupo?"
- `transform` pregunta: "¿como quieres reexpresar este grupo sin cambiar cuantas filas tiene?"

Por eso `transform` aparece mucho en feature engineering. Te permite construir variables como:

- z-score dentro de cada grupo
- promedio del grupo repetido en cada fila
- ranking interno
- imputacion por grupo

Ejemplos:

```python
# centrar cada salario respecto al promedio de su ciudad
df["salario_centrado"] = (
    df["salario"] - df.groupby("ciudad")["salario"].transform("mean")
)

# normalizar por grupo
df["z_salario_ciudad"] = df.groupby("ciudad")["salario"].transform(
    lambda s: (s - s.mean()) / s.std()
)
```

Si intentas hacer esto con `agg`, pierdes filas. Si lo haces con `apply`, muchas veces obtienes un resultado menos alineado o mas dificil de reasignar.

## `DataFrame.apply(axis=1)`: util, pero con cuidado

`axis=1` significa que tu funcion recibe una **fila completa** como `Series`. Eso es util cuando la logica depende de varias columnas al mismo tiempo:

```python
df["categoria"] = df.apply(
    lambda row: "alto" if row["ingreso"] > 50000 and row["deuda"] < 10000 else "medio",
    axis=1,
)
```

Pero tambien es una de las rutas mas lentas y menos idiomaticas de pandas, porque rompe parte del beneficio de la vectorizacion. Antes de usarla, revisa si puedes escribir la logica con operaciones booleanas:

```python
df["categoria"] = np.where(
    (df["ingreso"] > 50000) & (df["deuda"] < 10000),
    "alto",
    "medio",
)
```

No se trata de prohibir `axis=1`, sino de usarlo cuando la alternativa vectorizada seria artificial o mucho menos legible.

## Errores comunes

- Usar `apply` para operaciones que ya tienen metodo vectorizado.
- Confundir `DataFrame.apply(axis=0)` con transformacion celda por celda.
- Esperar que `transform` reduzca el numero de filas.
- Devolver outputs con formas inconsistentes dentro de `apply`.
- Usar `axis=1` por costumbre, no por necesidad.

Si recuerdas solo una cosa, que sea esta: en pandas la pregunta correcta no es "¿que metodo me deja meter una lambda?", sino "¿cual es el nivel correcto de operacion para este problema?".

## El notebook

El notebook aterriza estas ideas con ejemplos ejecutables, casos borde y comparaciones entre soluciones idiomaticas y soluciones que "funcionan" pero son menos claras o menos robustas.

[![Open in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/sonder-art/fdd_p26/blob/main/clase/14_pandas_transformaciones/code/01_apply_map_transform.ipynb)
