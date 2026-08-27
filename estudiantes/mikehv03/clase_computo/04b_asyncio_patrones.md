---
title: "asyncio — Patrones Avanzados y Anti-patrones"
---

# asyncio — Patrones Avanzados y Anti-patrones

`04a_asyncio_fundamentos.md` cubrió `gather` como la forma básica de M4. Este archivo completa la familia de mecanismos de sincronización y documenta los errores más comunes — cada uno con su consecuencia formal.

---

## asyncio.create_task — "lanzar y continuar"

### En la cocina

El cocinero recibe dos órdenes. La primera requiere el horno. El cocinero:

1. Prepara la parte que va al horno y la **mete** → `create_task(tarea_A())`
2. **Mientras el horno trabaja**, prepara la guarnición — trabajo independiente que no necesita el horno
3. Cuando necesita emplatar, **verifica que A esté lista** → `await tarea_A_obj`

La guarnición se preparó "gratis" — el tiempo del horno se aprovechó completamente. Si el horno termina antes que la guarnición, no hay espera extra. Si tarda más, el `await` esperará solo el tiempo restante.

### Formalmente

```
t₁: τᵢ = create_task(fn_A)    # τᵢ se registra en el event loop → READY
    [t₁, t₂]: τⱼ ejecuta trabajo independiente
               exec(τⱼ) ∩ wait(τᵢ) ≠ ∅   ← espera de A explotada ✓
t₂: await τᵢ                  # punto de dependencia de datos
    Si τᵢ ya terminó: continúa sin espera
    Si τᵢ aún espera: el event loop bloquea τⱼ hasta que τᵢ complete
```

`t₂` es el **punto de dependencia de datos**: el momento donde el código necesita el resultado de τᵢ. La posición del `await` es una decisión de diseño, no un detalle técnico.

### Código

```python
async def preparar_pedido():
    # ① Lanzar τᵢ en background — empieza inmediatamente en el event loop
    tarea_principal = asyncio.create_task(calentar_en_horno("plato_principal"))

    # ② Trabajo independiente — se ejecuta MIENTRAS τᵢ espera en el horno
    ensalada  = preparar_ensalada()       # exec — no necesita await
    guarnicion = preparar_guarnicion()    # exec — no necesita await

    # ③ Punto de dependencia — necesitamos el resultado aquí
    plato_principal = await tarea_principal  # si ya terminó: sin espera extra

    return emplatar(plato_principal, ensalada, guarnicion)
```

### create_task vs gather

```python
# gather — barrera: espera TODOS, devuelve resultados en orden de creación
resultados = await asyncio.gather(fn_A(), fn_B(), fn_C())
# resultados[0]=A, resultados[1]=B, resultados[2]=C (siempre en orden)

# create_task — flexible: await exactamente donde se necesita el resultado
tarea_A = asyncio.create_task(fn_A())
tarea_B = asyncio.create_task(fn_B())
resultado_B = await tarea_B    # cuando necesito B
# ... más trabajo ...
resultado_A = await tarea_A    # cuando necesito A (quizá ya terminó)
```

La concurrencia producida es la misma — la diferencia es el control de flujo. `gather` es una barrera; `create_task + await` permite continuar con el resultado disponible en cuanto se necesita.

---

## asyncio.as_completed — procesar conforme llegan

### En la cocina

El mesero no espera a que **todos** los platos de la mesa estén listos para llevarlos juntos al comedor. Lleva cada plato al comensal **tan pronto como sale del horno**. El comensal con la orden más rápida come más rápido — no espera al que pidió el corte más elaborado.

### Código

```python
tareas = [
    asyncio.create_task(buscar_en_fuente("wikipedia", query)),
    asyncio.create_task(buscar_en_fuente("arxiv", query)),
    asyncio.create_task(buscar_en_fuente("github", query)),
]

# Procesa resultados conforme llegan — no en orden de creación
async for tarea in asyncio.as_completed(tareas):
    resultado = await tarea    # await aquí nunca bloquea — ya terminó
    print(f"  resultado recibido: {resultado[:50]}...")
    procesar_parcialmente(resultado)
```

**Cuándo usar:** cuando las tareas tienen duraciones variables y quieres minimizar latencia del primer resultado, o cuando cada resultado puede procesarse independientemente.

---

## asyncio.wait con FIRST_COMPLETED — reaccionar al primero

### En la cocina

Se mandaron pedidos a tres proveedores distintos para conseguir el mismo ingrediente. El primero en responder gana la orden; los otros dos se cancelan. No tiene sentido esperar a los tres.

### Código

```python
tareas = {asyncio.create_task(fn()) for fn in [fuente_a, fuente_b, fuente_c]}

# Espera hasta que UNA tarea complete
completadas, pendientes = await asyncio.wait(
    tareas,
    return_when=asyncio.FIRST_COMPLETED
)

# Cancela las que no terminaron
for t in pendientes:
    t.cancel()

resultado = completadas.pop().result()
```

**Cuándo usar:** búsqueda en múltiples fuentes donde solo necesitas la primera respuesta, timeout con cancelación, race entre alternativas.

---

## asyncio.Queue — productor-consumidor

### En la cocina: el ticket rail

El ticket rail es el carril metálico donde los meseros cuelgan los tickets de las órdenes. Los meseros (productores) cuelgan tickets conforme llegan los pedidos. Los cocineros (consumidores) los toman y los procesan. El rail tiene capacidad limitada — si está lleno, los meseros esperan; si está vacío, los cocineros esperan.

Este mecanismo desacopla la velocidad de llegada de pedidos de la velocidad de preparación.

### Formalmente

```
Queue = (Workers, Q_buffer)

maxsize > 0: put() hace await si Q lleno → backpressure natural
             (mesero espera si el rail está lleno)
get() hace await si Q vacío → workers no consumen CPU en espera activa
             (cocinero espera si no hay tickets)
```

### Código

```python
import asyncio

async def productor(queue: asyncio.Queue, items: list):
    for item in items:
        await queue.put(item)
        print(f"  productor: puso {item} (qsize={queue.qsize()})")
        await asyncio.sleep(0.1)   # simula llegada de peticiones
    await queue.put(None)          # sentinel: indica fin de trabajo

async def consumidor(queue: asyncio.Queue, nombre: str):
    while True:
        item = await queue.get()
        if item is None:
            queue.task_done()
            break
        print(f"  {nombre}: procesando {item}")
        await asyncio.sleep(0.3)   # simula I/O de procesamiento
        queue.task_done()

async def pipeline(items: list, n_workers: int = 2):
    queue = asyncio.Queue(maxsize=5)   # buffer limitado — backpressure
    await asyncio.gather(
        productor(queue, items),
        *[consumidor(queue, f"worker-{i}") for i in range(n_workers)]
    )
```

**Cuándo usar:** procesamiento de streaming, rate limiting, separar responsabilidades de producción y consumo, N productores / M consumidores.

---

## Estos patrones en el chatbot

### Escenario A — consultas independientes con create_task

En el chatbot v2, cada petición de usuario requiere consultar la BD **y** buscar contexto en el caché. Estas dos operaciones son independientes entre sí — se pueden lanzar en paralelo:

```python
async def handle_request_v2b(user_id: int) -> str:
    # Lanzar BD y caché juntos — ambas son I/O-bound independientes
    tarea_bd     = asyncio.create_task(consultar_bd(user_id))
    tarea_cache  = asyncio.create_task(consultar_cache(user_id))

    # Esperar ambas (gather equivalente, pero con nombres explícitos)
    historial = await tarea_bd
    contexto  = await tarea_cache

    # LLM depende de ambas — correcto esperar aquí
    respuesta = await llamar_llm_api(historial, contexto)
    return respuesta

# Tiempo: max(T_bd, T_cache) + T_llm  en lugar de  T_bd + T_cache + T_llm
```

### Escenario A — múltiples fuentes con as_completed

Si el chatbot busca en múltiples fuentes de conocimiento, `as_completed` permite construir la respuesta con lo que llega primero:

```python
async def enriquecer_contexto(query: str) -> list:
    tareas = [
        asyncio.create_task(buscar_bd_usuario(query)),
        asyncio.create_task(buscar_documentos(query)),
        asyncio.create_task(buscar_web(query)),         # puede tardar más
    ]
    contextos = []
    async for tarea in asyncio.as_completed(tareas):
        resultado = await tarea
        contextos.append(resultado)
        if len(contextos) >= 2:    # con 2 fuentes es suficiente
            break
    return contextos
```

### Escenario A — cola de peticiones con Queue

Para un servidor de producción con backpressure (no aceptar más peticiones de las que podemos procesar):

```python
async def servidor_con_backpressure(capacidad: int):
    cola = asyncio.Queue(maxsize=capacidad)

    async def receptor():
        while True:
            peticion = await recibir_peticion()   # wait — red
            await cola.put(peticion)              # backpressure si cola llena

    async def procesador(worker_id: int):
        while True:
            peticion = await cola.get()
            respuesta = await handle_request(peticion)
            await enviar(respuesta)
            cola.task_done()

    await asyncio.gather(
        receptor(),
        *[procesador(i) for i in range(10)]   # 10 workers concurrentes
    )
```

---

## Anti-patrones con consecuencias formales

### 1. time.sleep en función async

```python
# ❌ Anti-patrón
async def tarea():
    time.sleep(2)       # bloquea el hilo del OS → event loop congelado

# Consecuencia formal:
# ∀ τₖ ≠ τᵢ, ∀ t ∈ sleep_interval:  τₖ ∉ ExecutingAt(t)
# M4 colapsa a M1 o peor
```

```python
# ✓ Correcto
async def tarea():
    await asyncio.sleep(2)   # libera event loop → otras coroutines ejecutan
```

### 2. Código CPU-bound en coroutine sin delegar

```python
# ❌ Anti-patrón
async def calcular_embedding(texto: str):
    vector = modelo_local.encode(texto)   # CPU-bound 500ms — bloquea event loop

# Consecuencia:
# ∀ t ∈ [inicio_encode, fin_encode]:  ExecutingAt(t) = {τᵢ}
# El chatbot deja de atender a TODOS los usuarios durante 500ms por UN embedding
```

```python
# ✓ Correcto: delegar a executor
from concurrent.futures import ProcessPoolExecutor

executor = ProcessPoolExecutor(max_workers=4)

async def calcular_embedding(texto: str):
    loop = asyncio.get_event_loop()
    vector = await loop.run_in_executor(executor, modelo_local.encode, texto)
    return vector
```

### 3. Fire-and-forget sin tracking

```python
# ❌ Anti-patrón
async def servidor():
    for peticion in peticiones:
        asyncio.create_task(handle(peticion))   # excepción → silenciada

# ✓ Correcto
async def servidor():
    tareas = set()
    for peticion in peticiones:
        t = asyncio.create_task(handle(peticion))
        tareas.add(t)
        t.add_done_callback(tareas.discard)
        t.add_done_callback(lambda t: print(f"ERROR: {t.exception()}") if not t.cancelled() and t.exception() else None)
```

### 4. await inmediato después de create_task

```python
# ❌ Anti-patrón (create_task es inútil)
async def main():
    tarea = asyncio.create_task(fn_A())
    resultado = await tarea              # await inmediato → ningún trabajo pudo ocurrir
    # Equivale exactamente a: resultado = await fn_A()

# ✓ Correcto: trabajo intermedio entre create_task y await
async def main():
    tarea = asyncio.create_task(fn_A())
    resultado_B = await fn_B()           # trabajo independiente aquí
    resultado_A = await tarea            # ahora el await tiene sentido
```

### 5. awaits secuenciales de tareas independientes

```python
# ❌ Anti-patrón — BD y caché son independientes pero se esperan en serie
async def obtener_datos(user_id):
    historial = await consultar_bd(user_id)    # espera BD completa
    contexto  = await consultar_cache(user_id) # solo empieza después
    respuesta = await llamar_llm(historial, contexto)
# Tiempo: T_bd + T_cache + T_llm

# ✓ Correcto
async def obtener_datos(user_id):
    historial, contexto = await asyncio.gather(
        consultar_bd(user_id),
        consultar_cache(user_id)        # corren concurrentemente
    )
    respuesta = await llamar_llm(historial, contexto)
# Tiempo: max(T_bd, T_cache) + T_llm  ← mejora real
```

---

## Tabla de resumen

| Mecanismo | Semántica | Cuándo usar |
|-----------|-----------|-------------|
| `await fn()` | Secuencial — espera resultado antes de continuar | Una tarea, o dependencia estricta |
| `gather(*fns)` | Barrera — espera todas, devuelve en orden | N tareas independientes, necesitas todos los resultados |
| `create_task + await` | Lanzar → trabajo libre → await en punto de dependencia | Trabajo independiente entre lanzamiento y resultado |
| `as_completed` | Iterar por orden de llegada | N tareas con duraciones variables, procesar parcialmente |
| `wait(FIRST_COMPLETED)` | El primero en terminar, cancelar el resto | Race entre alternativas, timeout |
| `Queue` | Desacoplar producción y consumo | Streaming, N productores / M consumidores, backpressure |

---

:::exercise{title="Diagnosticar anti-patrones"}
Lee cada fragmento, identifica: (1) qué anti-patrón es, (2) cuál es la consecuencia formal, (3) cómo corregirlo.

```python
# Fragmento A
async def buscar(query):
    r1 = await buscar_en_bd(query)
    r2 = await buscar_en_cache(query)
    r3 = await buscar_en_api(query)
    return [r1, r2, r3]

# Fragmento B
async def procesar():
    tarea = asyncio.create_task(calcular())
    resultado = await tarea
    return resultado

# Fragmento C
async def servidor():
    while True:
        peticion = await recibir_peticion()
        asyncio.create_task(handle(peticion))
```
:::
