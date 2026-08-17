---
title: "Librerías Python y Árbol de Decisión"
---

# Librerías Python y Árbol de Decisión

Los modelos M1–M5 ahora son concretos. Este archivo mapea cada modelo a las librerías Python que lo implementan y ofrece un árbol de decisión para elegir la herramienta correcta en práctica.

---

## El Pool — concepto base

### En la cocina: la brigada de guardia

En una cocina de alto volumen, los cocineros no se contratan y despiden por pedido — eso sería imposiblemente costoso. En cambio, hay una **brigada de guardia**: un número fijo de cocineros que esperan junto al ticket rail. Cuando llega un pedido, el primer cocinero disponible lo toma. Cuando termina, vuelve a esperar.

Esto es un **pool**: trabajadores pre-creados, compartidos, listos para tomar trabajo de una cola.

### Formalmente

```
Pool = (Workers, Q)

Workers = {θ₁, θ₂, ..., θₙ}   workers pre-creados (hilos o procesos)
Q                               cola FIFO de tareas pendientes
```

Los workers se crean **una sola vez** al inicializar el pool. Cuando llega una tarea, se encola. El primer worker libre la toma.

### Pool vs creación por tarea

```python
# ❌ Anti-patrón: crear proceso por cada tarea
for item in dataset:                     # 10,000 items
    p = multiprocessing.Process(...)     # overhead de creación × 10,000
    p.start(); p.join()
# Costo: O(N) × 50–200ms = inaceptable

# ✓ Correcto: pool (creación amortizada)
with ProcessPoolExecutor(max_workers=4) as pool:
    resultados = list(pool.map(fn, dataset))
# Costo creación: O(1) × 4 workers — amortizado en todas las tareas
```

---

## Tabla de librerías Python

| Librería | Modelo | Tipo de tarea | Cuándo usar | Cuándo NO usar |
|----------|--------|--------------|-------------|----------------|
| `threading.Thread` | M3 | I/O-bound | Control fino de un hilo, pocos hilos | CPU-bound (GIL), muchas tareas |
| `ThreadPoolExecutor` | M3+pool | I/O-bound | Muchas tareas I/O con pool, API síncrona | CPU-bound (GIL no escapa) |
| `asyncio` | M4 | I/O-bound | Máxima concurrencia I/O, librerías async | CPU-bound sin run_in_executor |
| `multiprocessing.Process` | M5a | CPU-bound | Control fino de un proceso, pocos procesos | Muchas tareas (crear N procesos es costoso) |
| `ProcessPoolExecutor` | M5a+pool | CPU-bound | Muchas tareas CPU-bound, integra con asyncio | Funciones no-picklable (lambdas) |
| `joblib.Parallel` | M5a+pool | CPU-bound | Scikit-learn ecosystem, arrays numpy | Integración con asyncio |

### threading vs asyncio para I/O-bound

```
asyncio:  más eficiente, menor overhead — pero requiere librerías async (aiohttp, asyncpg)
threading: más simple, funciona con librerías síncronas — pero escala peor (N hilos = N stacks)
```

### joblib

```python
from joblib import Parallel, delayed

resultados = Parallel(n_jobs=4)(
    delayed(procesar)(item) for item in dataset
)
```

`joblib` usa `loky` como backend por defecto (más robusto que `multiprocessing` para notebooks). Backends `threading` y `multiprocessing` intercambiables con un parámetro.

---

## Árbol de decisión

```
¿Cuál librería usar?
│
├─ ¿La tarea es I/O-bound? (wait(τᵢ) ≠ ∅)
│  │
│  │  [Chatbot Escenario A: LLM como API remota → I/O-bound]
│  │
│  ├─ ¿Hay librerías async disponibles? (aiohttp, asyncpg, aiofiles...)
│  │  └─ SÍ → asyncio + asyncio.gather / create_task        [M4]  ← Escenario A
│  │
│  └─ ¿Solo librerías síncronas? (requests, psycopg2...)
│     ├─ ¿Pocas tareas (<10)?   → threading.Thread           [M3]
│     └─ ¿Muchas tareas (≥10)?  → ThreadPoolExecutor         [M3+pool]
│
├─ ¿La tarea es CPU-bound? (wait(τᵢ) = ∅)
│  │
│  │  [Chatbot Escenario B: LLM local, inferencia CPU → CPU-bound]
│  │
│  ├─ ¿Usa NumPy/extensiones C que liberan el GIL?
│  │  └─ SÍ → ThreadPoolExecutor puede funcionar             [M3]
│  │
│  ├─ ¿Python puro?
│  │  ├─ ¿Pocas tareas (<10)?   → multiprocessing.Process    [M5a]
│  │  ├─ ¿Muchas tareas (≥10)?  → ProcessPoolExecutor        [M5a+pool]
│  │  └─ ¿Scikit-learn / numpy? → joblib.Parallel            [M5a+pool]
│  │
│  └─ ¿Carga mixta (I/O + CPU)?
│     │
│     │  [Chatbot Escenario B: recv/BD = I/O + inferencia = CPU]
│     │
│     └─ asyncio + loop.run_in_executor(ProcessPoolExecutor) [M5b]  ← Escenario B
│
└─ ¿Distribuido? (múltiples máquinas)
   └─ ver 07_distribuido_intro.md                            [M6]
```

### Chatbot: qué cambia entre Escenario A y B

| Componente | Escenario A | Escenario B |
|---|---|---|
| recv + parse | asyncio (exec, instantáneo) | asyncio (exec, instantáneo) |
| leer BD | asyncio (wait I/O) | asyncio (wait I/O) |
| LLM | asyncio (wait I/O — API remota) | `run_in_executor` → ProcessPool (exec CPU-bound) |
| send | asyncio (wait I/O) | asyncio (wait I/O) |
| **Modelo** | **M4** | **M5b** |

---

## Anti-patrones cross-cutting

### 1. Lambda en ProcessPoolExecutor (PicklingError)

**Por qué falla:** `multiprocessing` envía funciones a los procesos worker serializándolas con `pickle`. Las lambdas son funciones anónimas — no tienen nombre a nivel de módulo, por lo que `pickle` no puede localizarlas en el espacio de nombres global y lanza `PicklingError` en el momento de enviarlas, antes de ejecutar ningún trabajo.

```python
# ❌ Anti-patrón
with ProcessPoolExecutor() as pool:
    resultados = list(pool.map(lambda x: x**2, datos))
# → PicklingError: Can't pickle <function <lambda> at 0x7f...>
# El error ocurre al serializar la función, no al ejecutarla.
```

La misma restricción aplica a funciones anidadas (`def` dentro de otra `def`) y a métodos de instancia que capturen `self` con estado no-picklable.

```python
# ✓ Fix 1: función definida a nivel de módulo (picklable por nombre)
def al_cuadrado(x):
    return x**2

with ProcessPoolExecutor() as pool:
    resultados = list(pool.map(al_cuadrado, datos))

# ✓ Fix 2: functools.partial para parámetros extra
from functools import partial

def potencia(x, n):
    return x**n

al_cubo = partial(potencia, n=3)   # partial sí es picklable
with ProcessPoolExecutor() as pool:
    resultados = list(pool.map(al_cubo, datos))
```

> **Notebook 03 — Sección 8:** reproduce el `PicklingError` con lambda, verifica que `partial` lo resuelve, y compara ambos con la versión de función de módulo.

---

### 2. Pool creado por petición

**Por qué falla:** crear un `ProcessPoolExecutor(max_workers=N)` implica lanzar N procesos del OS — cada uno cuesta entre 50 ms y 200 ms (fork + inicialización del intérprete Python). En un servidor bajo carga, esto se convierte en el cuello de botella principal:

```
100 req/s × 4 workers × ~100ms/proceso = 400 procesos/s creados y destruidos
→ overhead de creación ≈ tiempo real de trabajo
```

```python
# ❌ Anti-patrón — chatbot Escenario B
async def handle_request(peticion):
    with ProcessPoolExecutor(max_workers=4) as pool:  # nuevo pool por petición
        resultado = await loop.run_in_executor(pool, calcular, peticion)
# Al salir del with, pool.shutdown() destruye los 4 procesos.
# La próxima petición los crea de nuevo.

# ✓ Correcto: pool compartido a nivel de aplicación (creado una sola vez)
_POOL = ProcessPoolExecutor(max_workers=os.cpu_count())

async def handle_request(peticion):
    loop = asyncio.get_event_loop()
    resultado = await loop.run_in_executor(_POOL, calcular, peticion)
# Los workers se reusan entre peticiones — costo de creación: O(1) total.
```

> **Notebook 03 — Sección 9:** mide empíricamente el overhead de pool-por-petición vs pool compartido para N peticiones seguidas. El cociente de tiempos crece linealmente con N.

---

### 3. Código bloqueante en async sin run_in_executor

**Por qué falla:** el event loop de asyncio corre en **un solo hilo**. Cuando una corrutina llama a una función bloqueante (como `time.sleep()`, `requests.get()`, o `open().read()`), ese hilo queda detenido durante toda la espera. Como no hay otro hilo que ejecute el event loop, **todas las corrutinas pendientes se congelan** — no solo la que hizo la llamada bloqueante.

Formalmente: exec(τ_bloqueante) ocupa el hilo del event loop durante wait(τ_bloqueante), eliminando la capacidad de M4 de explotar las esperas de otras corrutinas.

```python
# ❌ Anti-patrón
async def handler():
    datos = open("archivo.csv").read()     # bloqueante → congela TODAS las corrutinas
    resultado = requests.get(url)          # bloqueante → ídem
    # Mientras espera, ningún otro usuario del chatbot avanza.

# ✓ Fix: delegar a un executor (hilo o proceso separado)
async def handler():
    loop = asyncio.get_event_loop()
    # run_in_executor corre la función en un ThreadPoolExecutor y
    # devuelve el control al event loop mientras espera.
    datos = await loop.run_in_executor(None, leer_archivo, "archivo.csv")

    # Para I/O de red: usar librería async nativa (no bloquea el hilo del event loop)
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            resultado = await response.json()
```

El `None` en `run_in_executor(None, ...)` usa el ThreadPoolExecutor por defecto del event loop — suficiente para I/O. Para CPU-bound usar explícitamente `ProcessPoolExecutor` (ver Sección 10 del Notebook 03).

> **Notebook 02 — Sección 2:** usa `asyncio` debug mode y `loop.slow_callback_duration` para detectar automáticamente cuándo una corrutina bloquea el event loop. La traza muestra exactamente cuánto tiempo se congela el loop.
>
> **Notebook 03 — Sección 10:** implementa el patrón completo M5b: `asyncio` para I/O + `ProcessPoolExecutor` para CPU-bound en el mismo servidor, comparando con la versión donde `time.sleep()` bloquea el event loop.

---

### 4. Más workers que cores para CPU-bound

**Por qué falla:** para tareas CPU-bound, `wait(τᵢ) = ∅` — los workers nunca se bloquean esperando I/O. Con P cores disponibles, el OS solo puede ejecutar P procesos simultáneamente. Si hay N > P workers, los N − P extra deben esperar su turno en el scheduler, añadiendo context-switches que consumen ciclos de CPU sin hacer trabajo útil (thrashing):

```
N = 100 procesos, P = 8 cores
→ En cualquier instante: 8 ejecutan, 92 esperan
→ Overhead de scheduling domina cuando N >> P
```

```python
# ❌ Anti-patrón (thrashing)
with ProcessPoolExecutor(max_workers=100) as pool:  # máquina tiene 8 cores
    resultados = list(pool.map(tarea_cpu_bound, datos))

# ✓ Correcto
with ProcessPoolExecutor(max_workers=os.cpu_count()) as pool:
    resultados = list(pool.map(tarea_cpu_bound, datos))
```

Para I/O-bound la lógica es opuesta: como `wait(τᵢ) ≠ ∅`, más workers que cores sí ayuda (los workers bloqueados en I/O no compiten por CPU). El óptimo para I/O-bound depende de la latencia del dispositivo externo y puede estar en 10× o más.

> **Notebook 03 — Sección 6:** mide threading vs multiprocessing para CPU-bound con distintos valores de workers. El GIL hace que threading no escale; multiprocessing escala hasta `os.cpu_count()` y luego se aplana.
>
> **La gráfica `pool_size_vs_throughput.png`** (en esta página) muestra el punto de inflexión empíricamente: throughput sube hasta P = `os.cpu_count()` y cae o se aplana con workers adicionales.

---

### 5. Falta de `if __name__ == "__main__"` en scripts

**Por qué falla:** en Windows y macOS, `multiprocessing` usa el método `spawn` para crear procesos — cada worker lanza un nuevo intérprete Python e **importa el módulo principal desde cero**. Si el código que crea el pool está en el nivel de módulo (fuera de cualquier función), al importarse genera nuevos workers, que importan el módulo de nuevo, que generan más workers... recursión infinita hasta agotar la memoria o los PID del OS.

```python
# ❌ En scripts .py (no en notebooks)
from concurrent.futures import ProcessPoolExecutor

pool = ProcessPoolExecutor(max_workers=4)   # se ejecuta al importar
resultados = list(pool.map(mi_funcion, datos))
# En Windows/macOS: RuntimeError o cuelgue total al intentar ejecutar

# ✓ Correcto: el guard evita que el pool se cree durante el import
if __name__ == "__main__":
    with ProcessPoolExecutor(max_workers=4) as pool:
        resultados = list(pool.map(mi_funcion, datos))
```

En Linux el método por defecto es `fork` (copia el proceso padre tal cual), por lo que el error no aparece — pero el código sin guard seguirá fallando en producción si algún día corre en macOS/Windows o si el método se cambia a `spawn` explícitamente. El guard es obligatorio para portabilidad.

En notebooks este problema no ocurre porque el kernel de Jupyter ya proporciona el proceso raíz y no re-importa el notebook al crear workers.

> **Notebook 03 — Sección 8:** el ejemplo del PicklingError de lambda también cubre la picklabilidad general. Si adaptas el código del notebook a un script `.py` sin el guard, puedes reproducir el error de spawn en tu máquina.

---

## Benchmarks comparativos

### I/O-bound: asyncio vs ThreadPoolExecutor vs secuencial

![Benchmark I/O-bound: asyncio y threading vs secuencial](./images/benchmark_io_bound.png)

Tanto asyncio como ThreadPoolExecutor producen speedup ~N para N tareas I/O-bound. asyncio tiene menor overhead por tarea porque no crea hilos del OS — relevante para el Escenario A con muchos usuarios concurrentes.

> **Notebook 03 — Sección 5:** mide empíricamente asyncio vs ThreadPoolExecutor para I/O-bound. Ambos producen speedup, pero asyncio escala mejor porque los hilos tienen overhead de creación y stack. La diferencia crece con N.

### CPU-bound: ProcessPoolExecutor vs threading vs secuencial

![Benchmark CPU-bound: ProcessPoolExecutor vs threading vs secuencial](./images/benchmark_cpu_bound.png)

- `threading`: speedup ≈ 1 (o menor, por overhead del GIL) — confirma por qué threading no sirve para el Escenario B
- `ProcessPoolExecutor`: speedup ≈ P (limitado por Amdahl con S del overhead de serialización)

> **Notebook 03 — Sección 6:** reproduce este benchmark con tu máquina. La comparación threading/multiprocessing hace visible el GIL en números: threading puede ser más lento que secuencial por el overhead de sincronización, mientras multiprocessing escala hasta `os.cpu_count()`.
>
> **Notebook 01 — Sección 3 y 4:** establece la base: GIL bloqueado durante CPU-bound (sin speedup con threading) vs GIL liberado durante I/O-bound (sí hay speedup con threading). El benchmark de esta página es la extensión a procesamiento paralelo.

### Pool size vs throughput

![Pool size vs throughput: punto óptimo en os.cpu_count()](./images/pool_size_vs_throughput.png)

El punto de inflexión para CPU-bound ocurre en `max_workers = os.cpu_count()`. Para I/O-bound, el óptimo depende de la latencia del dispositivo externo y puede estar mucho más alto.

> **Notebook 03 — Sección 7:** compara joblib vs ProcessPoolExecutor con la misma tarea CPU-bound. También es el punto de partida para experimentar con distintos valores de `n_jobs` / `max_workers` y ver cómo el throughput se aplana o cae al sobrepasar el número de cores.

---

:::exercise{title="Elegir la herramienta correcta"}
Para cada escenario, elige la librería apropiada y justifica usando el árbol de decisión:

1. Descargar 500 imágenes de URLs distintas (sin librería async disponible)
2. Calcular PCA sobre una matriz 50,000×1,000 con scikit-learn
3. Un servidor de chatbot con LLM de Anthropic API (Escenario A)
4. Un servidor de chatbot con LLM local llama.cpp (Escenario B)
5. Procesar 1,000 archivos de audio con librería C pura que libera el GIL
:::
