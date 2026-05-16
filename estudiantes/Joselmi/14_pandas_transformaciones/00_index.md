# Modulo 14: Pandas — Transformaciones y Tiempo

En los modulos anteriores el foco estuvo en **leer**, **limpiar** y **combinar** datos. El siguiente paso natural es transformarlos para contestar preguntas reales: crear nuevas variables, resumir informacion por grupos, normalizar columnas y trabajar con fechas de forma consistente.

Este modulo se concentra en tres ideas que suelen confundirse cuando apenas empiezas con pandas:

1. `apply`, `map` y `transform` no hacen lo mismo, aunque sus nombres se parezcan.
2. Las fechas parecen simples hasta que aparecen formatos mezclados, zonas horarias y operaciones calendario.
3. `groupby` no solo sirve para "sacar promedios"; tambien permite transformar y filtrar sin perder el contexto fila por fila.

La meta no es memorizar metodos aislados, sino construir un **mapa mental**: que objeto recibe tu funcion, que forma tendra el resultado y cuando una operacion conserva o cambia el numero de filas.

## Contenido

| Seccion | Tema | Tiempo |
|---------|------|--------|
| [Funciones vectorizadas](./01_funciones_vectorizadas.md) | El mapa mental de apply/map/transform | ~8 min |
| [Tiempo y groupby](./02_tiempo_y_groupby.md) | Timestamps, UTC, groupby avanzado | ~5 min |
| [Pandas 3.0](./03_pandas3.md) | CoW obligatorio, strings Arrow, applymap eliminado, groupby observed, migracion | ~10 min |

## Que deberias poder hacer al terminar

- Distinguir entre operaciones elemento a elemento, por fila/columna y por grupo.
- Decidir cuando `transform` es mejor opcion que `apply`.
- Parsear fechas sin introducir ambiguedades de timezone.
- Diseñar agregaciones y features por grupo sin romper la forma del DataFrame.
- Reconocer cambios de pandas 3.0 que afectan notebooks y pipelines escritos para versiones anteriores.

## Notebooks

| Notebook | Tema | Tiempo |
|----------|------|--------|
| [Apply, Map y Transform](./code/01_apply_map_transform.ipynb) | map/apply en Series, apply con axis en DataFrame, applymap, transform, edge cases, argumentos extra | ~35 min |
| [Timestamps y Timezones](./code/02_timestamps.ipynb) | to_datetime, formatos, UTC, tz_localize/convert, .dt accessor, features temporales | ~15 min |
| [Groupby](./code/03_groupby.ipynb) | agg, transform, filter, named agg, multicolumna | ~10 min |
| [Pandas 3.0](./code/04_pandas3.ipynb) | Cambios de comportamiento, codigo legacy vs moderno, checklist de migracion | ~20 min |

[![Open in Colab — Apply/Map](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/sonder-art/fdd_p26/blob/main/clase/14_pandas_transformaciones/code/01_apply_map_transform.ipynb)
[![Open in Colab — Timestamps](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/sonder-art/fdd_p26/blob/main/clase/14_pandas_transformaciones/code/02_timestamps.ipynb)
[![Open in Colab — Groupby](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/sonder-art/fdd_p26/blob/main/clase/14_pandas_transformaciones/code/03_groupby.ipynb)
[![Open in Colab — Pandas 3.0](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/sonder-art/fdd_p26/blob/main/clase/14_pandas_transformaciones/code/04_pandas3.ipynb)

## Prerequisitos

- Modulo 12 y 13: Pandas completados
- `pip install -r requirements.txt`

## Idea central del modulo

Muchos errores en pandas no vienen de "no saber la sintaxis", sino de no tener claro el **nivel de operacion**:

- celda individual
- Serie completa
- fila o columna
- grupo
- DataFrame completo

Si identificas ese nivel antes de escribir codigo, eliges mejor entre `map`, `apply`, `transform`, `agg`, `filter` o `pipe`, y tu codigo se vuelve mas predecible, mas facil de depurar y normalmente tambien mas rapido.
