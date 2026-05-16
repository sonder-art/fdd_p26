# Pandas 3.0 — Que cambio y por que importa

pandas 3.0 salio en enero de 2025. No es una actualizacion menor: consolida anos de cambios que venian siendo opcionales o experimentales en pandas 2.x y elimina APIs que llevaban tiempo deprecadas. Si tu codigo fue escrito para pandas 1.x o 2.x, probablemente tiene cosas que ya no funcionan igual.

Este capitulo documenta los cambios que mas afectan el trabajo cotidiano en ciencia de datos.

La idea central es esta: pandas 3.0 empuja a usar un estilo de codigo mas **explicito**, mas **predecible** y menos dependiente de comportamientos historicos ambiguos. Varios cambios pueden sentirse incomodos al principio, pero casi todos apuntan a lo mismo:

- menos magia implicita
- menos APIs redundantes
- menos ambiguedad entre vista y copia
- mejor integracion con tipos modernos como Arrow y `pd.NA`

## Copy-on-Write es ahora obligatorio

El cambio mas importante. En pandas 2.x, Copy-on-Write (CoW) era opt-in:

```python
# pandas 2.x: habia que activarlo manualmente
pd.options.mode.copy_on_write = True
```

En pandas 3.0, CoW **es el comportamiento default e inamovible**. Ya no existe la opcion de desactivarlo.

### Que significa esto en la practica

El problema que CoW resuelve: en pandas 1.x/2.x (sin CoW), modificar un subconjunto de un DataFrame a veces modificaba el original y a veces no, dependiendo de si pandas habia creado una vista o una copia interna. El resultado era impredecible y generaba el infame `SettingWithCopyWarning`.

```python
# pandas < 3.0: comportamiento AMBIGUO
subset = df[df["edad"] > 30]
subset["score"] = 100  # ¿Modifica df? Depende. SettingWithCopyWarning.

# pandas 3.0: comportamiento PREDECIBLE
# subset es siempre una copia logica. Modificarla nunca afecta df.
subset = df[df["edad"] > 30]
subset["score"] = 100  # Modifica subset, df no cambia. Sin warning.

# Para modificar df, usa .loc explicitamente:
df.loc[df["edad"] > 30, "score"] = 100  # Esto si modifica df.
```

Si tu codigo dependia del comportamiento de modificar vistas, necesita ser revisado.

Lo importante no es solo "evitar warnings". CoW cambia la forma de razonar sobre mutacion:

- seleccionar produce un objeto separado desde el punto de vista logico
- asignar sobre ese objeto ya no tiene efectos colaterales sorpresa
- si quieres modificar el original, debes decirlo explicitamente con `.loc`, `.iloc` o una reasignacion clara

Este cambio hace que los pipelines sean mas faciles de leer y de depurar, porque la mutacion deja de depender de detalles internos del motor.

### Que patrones conviene migrar

- `df[cond]["col"] = valor` -> usar `df.loc[cond, "col"] = valor`
- modificar un subset esperando efectos sobre `df` -> reasignar o usar `.loc`
- confiar en `inplace=True` para "ahorrar memoria" -> preferir reasignacion explicita

La intuicion correcta en pandas 3.0 es: **seleccionar no equivale a abrir una ventana mutable al objeto original**.

## Strings con Arrow por default

pandas 3.0 cambia el tipo por default de columnas de texto. En pandas 2.x, leer un CSV con texto daba columnas de tipo `object` (arrays de punteros a objetos Python — lento y pesado). En pandas 3.0, el default es `pd.StringDtype()` respaldado por Apache Arrow.

```python
# pandas 2.x
df = pd.read_csv("datos.csv")
df["nombre"].dtype  # object

# pandas 3.0
df = pd.read_csv("datos.csv")
df["nombre"].dtype  # string[python] o string[pyarrow]
```

Ventajas: mas rapido, menos memoria, mejor soporte para `pd.NA`. El comportamiento con valores faltantes cambia: antes una columna `object` podia mezclar strings y `NaN`; ahora usa `pd.NA` consistentemente.

Si necesitas el comportamiento legacy:
```python
df = pd.read_csv("datos.csv", dtype_backend="numpy_nullable")
```

Este cambio importa porque `object` era una especie de "cajon de sastre": ahi cabian strings, enteros Python, listas, `NaN` y casi cualquier cosa. Eso daba flexibilidad, pero tambien hacia mas dificil optimizar y razonar sobre tipos.

Con strings tipados, pandas puede:

- representar faltantes de forma mas consistente
- delegar operaciones a Arrow cuando existe soporte
- reducir memoria en muchas cargas de datos textuales

La consecuencia practica es que conviene revisar codigo que asumia `object` en columnas de texto o que mezclaba tipos arbitrariamente en la misma columna.

## `applymap` eliminado — usar `map`

`DataFrame.applymap()` fue renombrado a `DataFrame.map()` en pandas 2.1 (dejando `applymap` como alias deprecado). En pandas 3.0 el alias fue **eliminado**. Codigo que use `applymap` lanzara `AttributeError`.

```python
# pandas < 3.0 (funciona pero lanza DeprecationWarning en 2.1+)
df.applymap(lambda x: round(x, 2))

# pandas 3.0 (correcto)
df.map(lambda x: round(x, 2))
```

Este cambio conecta directamente con lo que viste en el notebook de `apply/map/transform` de este modulo.

La motivacion no es solo "cambiar el nombre". `map` unifica mejor la idea semantica de una transformacion elemento a elemento:

- `Series.map()` -> sobre una Serie
- `DataFrame.map()` -> sobre cada celda del DataFrame

Eso hace el API mas coherente y reduce una palabra historica (`applymap`) que ya no aportaba demasiado.

## `groupby` con `observed=True` por default

Cambio que afecta a cualquiera que use `groupby` con columnas categoricas. En pandas 2.x, el default era `observed=False`, que incluia en el resultado todas las combinaciones de categorias aunque no hubiera datos para esa combinacion. En pandas 3.0 el default es `observed=True`.

```python
cat = pd.Categorical(["a", "a", "b"], categories=["a", "b", "c"])
df = pd.DataFrame({"grupo": cat, "valor": [1, 2, 3]})

# pandas 2.x (observed=False por default)
df.groupby("grupo")["valor"].sum()
# grupo
# a    3
# b    3
# c    0  ← categoria "c" sin datos aparece con 0

# pandas 3.0 (observed=True por default)
df.groupby("grupo")["valor"].sum()
# grupo
# a    3
# b    3   ← "c" no aparece porque no hay datos
```

Si tu pipeline depende de que aparezcan todas las categorias (por ejemplo, para reportes, tablas comparativas o dashboards con categorias fijas), especifica `observed=False` explicitamente.

Este cambio refleja una tension comun entre dos objetivos:

- analisis exploratorio: normalmente quieres ver solo lo observado
- reporteo estructurado: a veces quieres ver tambien categorias vacias

pandas 3.0 escoge como default el caso mas comun en analisis practico, pero deja abierta la opcion de recuperar el comportamiento anterior cuando sea necesario.

## APIs eliminadas

pandas 3.0 elimina varios metodos y parametros que llevaban versiones con `DeprecationWarning`. Los mas comunes:

| Eliminado en 3.0 | Reemplazo |
|---|---|
| `DataFrame.applymap()` | `DataFrame.map()` |
| `DataFrame.swapaxes()` | Transponer manualmente |
| `Series.swapaxes()` | Igual |
| `DataFrame.append()` | `pd.concat([df1, df2])` |
| Parametro `inplace=` en muchos metodos | Reasignar: `df = df.metodo()` |

`DataFrame.append()` era el mas usado. Fue eliminado desde pandas 2.0 pero aun aparece en codigo legacy y tutoriales viejos. La alternativa correcta es `pd.concat()`.

La leccion de fondo aqui es que pandas esta intentando reducir caminos redundantes para hacer lo mismo. Menos aliases implica menos carga cognitiva y menos tutoriales contradictorios.

Sobre `inplace=`, la recomendacion moderna es no pensar en pandas como si fuera una API "mutable por defecto". En muchos casos `inplace` no daba las ventajas de performance que los usuarios suponian y hacia mas dificil encadenar operaciones o razonar sobre estados intermedios.

## Mejoras de performance

pandas 3.0 aprovecha Arrow mas agresivamente internamente:

- Operaciones sobre strings hasta 3-5x mas rapidas con Arrow backend
- Menor uso de memoria para columnas de texto
- Mejoras en `read_csv`, `read_parquet`, y operaciones de `groupby`
- Copy-on-Write elimina copias innecesarias en pipelines encadenados

Conviene leer estas mejoras con cautela: no significan que cualquier notebook sera automaticamente mucho mas rapido. El beneficio depende del tipo de datos y del patron de uso. Donde mas suele notarse es en:

- tablas grandes con muchas columnas de texto
- cargas y escrituras frecuentes
- pipelines con slicing y reasignaciones
- operaciones que ya aprovechan Arrow internamente

La mejora importante no es solo velocidad bruta, sino tener un modelo mas consistente entre tipos, memoria y mutacion.

## Checklist mental de migracion

Si vas a correr codigo viejo en pandas 3.0, revisa primero esto:

1. Busca `applymap` y cambialo por `map`.
2. Busca chained indexing del tipo `df[cond]["col"] = ...`.
3. Revisa supuestos sobre `object` en columnas de texto.
4. Verifica `groupby` sobre categoricas si esperabas categorias no observadas.
5. Reemplaza APIs viejas como `.append()` por `pd.concat()`.

No todos los notebooks se romperan, pero estos cinco puntos concentran una gran parte de los cambios que si alteran comportamiento o estilo recomendado.

## El notebook

El notebook recorre estos cambios con codigo ejecutable: comparaciones de comportamiento, casos donde codigo de pandas 2.x falla en 3.0, y formas concretas de migrar a un estilo mas moderno y mas estable.

[![Open in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/sonder-art/fdd_p26/blob/main/clase/14_pandas_transformaciones/code/04_pandas3.ipynb)

:::exercise{title="Auditoria de compatibilidad" difficulty="2"}
Toma cualquier notebook de pandas que hayas escrito (de los modulos 12, 13 o 14). Busca: (1) uso de `applymap`, (2) patrones de chained indexing como `df[cond]["col"] = val`, (3) uso de `.append()`, (4) `groupby` sobre columnas categoricas. Documenta que cambiaria al correr ese codigo en pandas 3.0.
:::
