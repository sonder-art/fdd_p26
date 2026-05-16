# Timestamps, Timezones y Groupby

## Timestamps: el problema de las fechas en datos reales

Las fechas en datos reales vienen en decenas de formatos: `"2024-01-15"`, `"15/01/2024"`, `"Jan 15, 2024"`, `1705276800` (Unix timestamp). pandas puede parsear muchos de ellos, pero eso no significa que siempre adivine bien.

Hay dos problemas distintos que suelen mezclarse:

- **parsing**: convertir texto o enteros a fechas
- **semantica temporal**: decidir que instante del tiempo representa realmente ese dato

El problema mas sutil es el de **timezones**. Un timestamp sin timezone es ambiguo: no sabes si `"2024-01-15 10:00"` es hora de Ciudad de Mexico, UTC, o Nueva York. Cuando combinas datos de fuentes distintas sin normalizar a UTC primero, puedes introducir diferencias de horas silenciosas que despues contaminan merges, resamples, ventanas de tiempo o calculos de duracion.

La regla:
```
Siempre almacena en UTC internamente.
Convierte a timezone local solo para mostrar.
```

Esa regla existe porque separa dos preguntas que no deberian confundirse:

- "¿cual es el instante real?" -> UTC
- "¿como quiero mostrarselo a una persona?" -> timezone local

Otra distincion clave:

- `tz_localize()` asigna timezone a un timestamp que era naive
- `tz_convert()` cambia de una timezone a otra manteniendo el mismo instante real

Confundirlas produce errores muy comunes. Si localizas cuando debias convertir, estas reinterpretando la hora; si conviertes cuando el dato aun no tenia timezone, pandas te dira que falta contexto.

## Que conviene decidir al parsear fechas

Antes de llamar `pd.to_datetime()`, conviene fijarte en cuatro cosas:

1. Si todas las filas usan el mismo formato o vienen mezcladas.
2. Si el origen ya esta en UTC o en una hora local.
3. Si existen valores invalidos que deberian convertirse a `NaT`.
4. Si vas a usar la fecha como columna ordinaria o como indice temporal.

Un buen parseo no solo "evita errores"; tambien prepara el terreno para operaciones posteriores como:

- extraer anio, mes, dia de semana o trimestre con `.dt`
- ordenar cronologicamente
- calcular diferencias de tiempo
- reagrupar por periodos
- hacer joins temporales

Cuando una fecha queda como `object`, pierdes todas esas capacidades y ademas es mas facil cometer errores silenciosos.

## Groupby: lo que probablemente ya sabes y lo que no

Ya usaste `groupby` en el curso anterior. Aqui el foco es en entender que `groupby` no es una sola operacion, sino un patron de tres etapas:

1. **split**: dividir las filas por llave(s)
2. **apply**: ejecutar una operacion dentro de cada grupo
3. **combine**: recombinar resultados

Lo importante es que la etapa del medio puede tener objetivos distintos. Por eso vale la pena separar los tres modos mas comunes y cuando usar cada uno:

| Modo | Metodo | Forma del output | Uso tipico |
|------|--------|-----------------|------------|
| **Agregar** | `.agg()` | Menos filas (una por grupo) | Calcular estadisticas por grupo |
| **Transformar** | `.transform()` | Mismas filas que el original | Agregar columna con estadistica del grupo |
| **Filtrar** | `.filter()` | Subset de filas originales | Quitar grupos que no cumplen condicion |

La mayoria solo conoce el modo agregar. `transform` es el que mas se necesita en ciencia de datos y machine learning porque te deja incorporar contexto del grupo sin colapsar el dataset.

Ejemplos mentales:

- `agg`: "quiero una tabla resumen"
- `transform`: "quiero nuevas columnas, pero conservar cada observacion"
- `filter`: "quiero quedarme solo con grupos suficientemente grandes o interesantes"

## Cuando `groupby` se vuelve especialmente poderoso

`groupby` se vuelve mucho mas util cuando deja de ser solo "promedio por categoria" y pasa a responder preguntas analiticas como:

- ¿que tan lejos esta cada observacion del promedio de su grupo?
- ¿que porcentaje del total del grupo representa cada fila?
- ¿que grupos tienen suficiente muestra para analizar?
- ¿como cambia una variable dentro de cada cliente, ciudad o periodo?

Ejemplos conceptuales:

```python
# porcentaje del total del grupo
df["share"] = df["ventas"] / df.groupby("region")["ventas"].transform("sum")

# quedarse con grupos de tamano suficiente
df_filtrado = df.groupby("cliente").filter(lambda g: len(g) >= 5)
```

Estas operaciones son muy comunes en datos reales porque mezclan dos niveles de analisis al mismo tiempo:

- el nivel fila
- el nivel grupo

Justamente ahi es donde `transform` y `filter` brillan.

## Relacion entre tiempo y groupby

Estos dos temas aparecen juntos por una razon: en analisis real es muy comun agrupar **por tiempo** o construir grupos despues de extraer componentes temporales.

Por ejemplo:

- ventas por mes
- usuarios por dia de la semana
- promedio de transacciones por hora
- comportamiento por trimestre y por region

Una vez que la columna de fecha esta bien parseada, puedes derivar variables temporales y usarlas como llaves de agrupacion. Si esa columna estaba mal interpretada o con timezone inconsistente, todo el analisis por grupo queda sesgado desde el inicio.

## Los notebooks

[![Open in Colab — Timestamps](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/sonder-art/fdd_p26/blob/main/clase/14_pandas_transformaciones/code/02_timestamps.ipynb)

[![Open in Colab — Groupby](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/sonder-art/fdd_p26/blob/main/clase/14_pandas_transformaciones/code/03_groupby.ipynb)
