# Modulo 13: Pandas — I/O y Combinacion de Datos

Antes de limpiar o analizar datos, primero tienes que **leerlos**. Y antes de analizarlos juntos, tienes que **combinarlos**. Este modulo cubre exactamente eso.

La mayor parte del trabajo esta en los notebooks — los markdowns son solo el mapa. Abre los notebooks directamente en Colab y sigue las explicaciones ahi.

## Contenido

| Seccion | Tema | Tiempo |
|---------|------|--------|
| [I/O y Encodings](./01_io_y_encodings.md) | Por que los encodings importan, CSV, JSON, Parquet, mojibake | ~5 min |
| [Combinando DataFrames](./02_combinando_datos.md) | Merges relacionales vs concat posicional | ~8 min |

## Notebooks

| Notebook | Tema | Tiempo |
|----------|------|--------|
| [I/O y Encodings](./code/01_io_y_encodings.ipynb) | CSV (sep, encoding), JSON nativo y anidado, Parquet, deteccion de encoding, mojibake | ~20 min |
| [Merges y Joins](./code/02_merges_y_joins.ipynb) | inner/left/right/outer, por columna e indice, keys distintas, validate | ~25 min |
| [Concat](./code/03_concat.ipynb) | axis 0/1, keys, ignore_index, columnas disparejas | ~12 min |

[![Open in Colab — I/O](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/sonder-art/fdd_p26/blob/main/clase/13_pandas_io/code/01_io_y_encodings.ipynb)
[![Open in Colab — Merges](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/sonder-art/fdd_p26/blob/main/clase/13_pandas_io/code/02_merges_y_joins.ipynb)
[![Open in Colab — Concat](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/sonder-art/fdd_p26/blob/main/clase/13_pandas_io/code/03_concat.ipynb)

## Prerequisitos

- Modulo 12: Pandas completado
- `pip install -r requirements.txt`
