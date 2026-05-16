# Combinando DataFrames

Hay dos formas de juntar DataFrames y se confunden constantemente porque ambas "combinan datos". Son conceptualmente opuestas:

```
merge / join              concat
─────────────────         ──────────────────
Une por SIGNIFICADO       Une por POSICION
"¿Que comparten?"         "Ponlos uno encima/lado del otro"
Como SQL JOIN             Como pegar hojas de papel
Necesita keys comunes     Solo necesita que quepan
```

## Merge: union relacional

`pd.merge()` une dos DataFrames basandose en valores compartidos en columnas (o indices). Es el equivalente de `JOIN` en SQL.

El tipo de join determina **que filas sobreviven**:

```
LEFT         INNER        RIGHT        OUTER
┌──┐  ┌──┐  ┌──┐  ┌──┐  ┌──┐  ┌──┐  ┌──┐  ┌──┐
│A │  │B │  │A │  │B │  │A │  │B │  │A │  │B │
│1 │  │1 │  │1 │  │1 │  │1 │  │1 │  │1 │  │1 │
│2 │  │1 │  │2 │  │1 │  │2 │  │2 │  │2 │  │2 │
│3 │  │2 │  └──┘  └──┘  └──┘  └──┘  │3 │  │3 │
└──┘  └──┘                            └──┘  └──┘
Todas de A   Solo comunes  Todas de B  Todas de ambos
```

## Concat: apilado posicional

`pd.concat()` junta DataFrames por **posicion geometrica**, no por significado compartido. No busca claves comunes: simplemente coloca un DataFrame junto al otro, ya sea verticalmente o en horizontal.

El parametro `axis` indica **que dimension crece** como resultado de la operacion.

### Como pensar en `axis`

Un DataFrame tiene dos ejes:

```
          columna_a  columna_b  columna_c
              ↑          ↑          ↑
              └──────────┴──────────┘ ← eje de columnas (axis=1)

indice →  0 │    10         20         30
indice →  1 │    11         21         31       ← eje de filas (axis=0)
indice →  2 │    12         22         32
```

- **axis=0** es el eje de las filas (el indice). Concatenar a lo largo de `axis=0` significa que el indice crece: se anaden mas filas. Las columnas deben coincidir.
- **axis=1** es el eje de las columnas. Concatenar a lo largo de `axis=1` significa que las columnas crecen: se anaden mas columnas. Los indices deben coincidir.

### La trampa intuitiva

El nombre "axis" genera confusion porque parece decir "en que direccion se mueven los datos", cuando en realidad dice "que dimension del resultado se expande".

Una forma de recordarlo:

> `axis=0` → el resultado tiene **mas filas** que cualquiera de los inputs
> `axis=1` → el resultado tiene **mas columnas** que cualquiera de los inputs

### axis=0 — apilar filas (vertical)

Dos DataFrames con las mismas columnas, uno encima del otro:

```
df_enero            df_febrero          pd.concat([df_enero, df_febrero], axis=0)
──────────────       ──────────────       ────────────────────────────
   mes  ventas          mes  ventas           mes  ventas
0  ene      10       0  feb      30       0   ene      10
1  ene      20       1  feb      40       1   ene      20
                                         0   feb      30   ← indice se repite
                                         1   feb      40      (usar ignore_index=True
                                                               para 0,1,2,3)
```

Caso de uso tipico: tienes un archivo CSV por mes y quieres un unico DataFrame con todos los meses.

### axis=1 — apilar columnas (horizontal)

Dos DataFrames con el mismo indice, uno al lado del otro:

```
df_demograficos          df_financieros          pd.concat([...], axis=1)
──────────────────        ────────────────         ─────────────────────────────────
   nombre  edad              salario  ciudad           nombre  edad  salario  ciudad
0  Ana        25           0   35000  CDMX         0   Ana       25    35000  CDMX
1  Carlos     32           1   52000  MTY          1   Carlos    32    52000  MTY
2  Maria      28           2   41000  GDL          2   Maria     28    41000  GDL
```

Condicion: los indices deben coincidir. Si el indice de `df_demograficos` es `[0,1,2]` y el de `df_financieros` es `[0,1,3]`, la fila con indice `2` en demograficos y la fila con indice `3` en financieros no tendran pareja, y aparecen con `NaN` en las columnas del otro DataFrame.

Caso de uso tipico: tienes columnas de distintas fuentes sobre las mismas entidades (mismo indice) y quieres unirlas en un solo DataFrame.

### Por que no usar concat cuando necesitas merge

Concat no verifica que los datos correspondan — solo los pega por posicion. Si el orden de las filas en `df_demograficos` es distinto al orden en `df_financieros`, los datos de Ana quedaran en la misma fila que los datos de Carlos. No hay error, solo datos incorrectos.

Cuando necesitas unir datos por un identificador comun (nombre, id, fecha), usa `merge`. Concat es para cuando ya sabes que las filas o columnas corresponden posicionalmente.

## Los notebooks

[![Open in Colab — Merges](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/sonder-art/fdd_p26/blob/main/clase/13_pandas_io/code/02_merges_y_joins.ipynb)

[![Open in Colab — Concat](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/sonder-art/fdd_p26/blob/main/clase/13_pandas_io/code/03_concat.ipynb)
