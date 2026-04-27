# Examen de repaso — Cómputo (notebooks 01, 02 y 03)

Formato: pregunta corta + respuesta modelo. Úsalo para autoevaluarte: intenta responder sin mirar y luego compara.

---

## Parte A — Notebook 01: Procesos, hilos y GIL

### A1. ¿Qué diferencia hay entre un proceso y un hilo en cuanto a memoria?

**Respuesta:** Un proceso tiene su propio espacio de memoria aislado. Los hilos del mismo proceso comparten el heap (variables globales y objetos mutables accesibles entre hilos). Por eso un cambio en una lista compartida lo ven todos los hilos, pero el proceso padre no ve los cambios del hijo tras `fork`/`multiprocessing` como si fueran la misma variable en el padre.

---

### A2. ¿Qué es el GIL y qué efecto tiene en código **CPU-bound** que usa `threading`?

**Respuesta:** El Global Interpreter Lock es un cerrojo que permite que solo un hilo ejecute bytecode de CPython a la vez. En trabajo CPU-bound puro, los hilos no obtienen speedup real (suelen quedar ~1× o incluso algo peor por overhead), porque no ejecutan bytecode Python en paralelo de verdad.

---

### A3. ¿Por qué `threading` sí puede acelerar tareas **I/O-bound**?

**Respuesta:** Durante operaciones de I/O (red, disco, `sleep`, etc.), el intérprete puede liberar el GIL y otro hilo puede avanzar. Así se solapan esperas y el tiempo total puede acercarse al del trabajo más lento o a la suma “en paralelo” según el caso.

---

### A4. En el notebook, ¿por qué el padre puede seguir viendo `0` en su lista tras un `Process` hijo que incrementa una copia?

**Respuesta:** Tras crear un proceso hijo, el hijo recibe una copia del estado; lo que modifica el hijo no actualiza la memoria del padre. No comparten el mismo objeto en RAM (salvo mecanismos explícitos: `Manager`, `multiprocessing.Value`, etc.).

---

### A5. (Contexto Jupyter / Python 3.14) ¿Por qué a veces falla `multiprocessing` con `AttributeError: __main__ has no attribute '...'` y qué estrategia se menciona en Linux?

**Respuesta:** Con `spawn`/`forkserver`, el hijo debe poder importar de nuevo el target; las funciones definidas solo en una celda de notebook no siempre están disponibles como en un script. En Linux, usar `multiprocessing.get_context('fork')` suele evitar el problema porque el hijo hereda el espacio de direcciones del proceso padre (con matices según plataforma).

---

## Parte B — Notebook 02: Concurrencia y asyncio

### B1. ¿En qué se diferencia M2 (await secuencial) de M4 (`asyncio.gather`) cuando las tareas son I/O-bound?

**Respuesta:** En M2 cada `await` espera a que termine esa tarea antes de lanzar la siguiente: el tiempo total tiende a la suma de las esperas. En M4 las tareas concurrentes se solapan durante los `await` (esperas explotadas), y el tiempo total se acerca al del camino crítico (p. ej. ~el máximo de las duraciones si son independientes).

---

### B2. ¿Por qué `time.sleep` dentro de una coroutine puede “romper” el beneficio de `gather`?

**Respuesta:** `time.sleep` bloquea el hilo del sistema operativo que ejecuta el event loop, impidiendo que otras coroutines avancen. Para no bloquear hay que usar `await asyncio.sleep`.

---

### B3. ¿Qué modelo (M3) usa hilos para CPU-bound y qué resultado cabe esperar en Python por el GIL?

**Respuesta:** M3 sería `threading` ejecutando trabajo CPU-bound. No se espera speedup sustancial frente a secuencial; a veces hay pequeñas variaciones por el scheduler, pero no paralelismo real de bytecode.

---

### B4. ¿Cómo debes lanzar varios hilos para medir M3 correctamente (no serializar por error)?

**Respuesta:** Hacer `start()` de todos los hilos en un bucle y luego `join()` a todos en otro bucle. Si haces `start()` y `join()` del mismo hilo dentro del mismo ciclo, ejecutas casi en serie.

---

### B5. ¿Qué es una race condition y cómo se evita en el ejemplo del contador compartido?

**Respuesta:** Varias hebras leen-modifican-escriben una variable sin sincronización y el resultado depende del interleaving. Se evita con primitivas como `threading.Lock`, protegiendo la sección crítica (p. ej. `with lock: contador += 1`).

---

### B6. ¿Por qué “sin lock” puede dar el valor correcto a veces aunque el código sea incorrecto?

**Respuesta:** Porque la condición de carrera no es determinista: si el scheduler no intercala en el momento vulnerable, puede “pasar de casualidad”. Eso no hace el programa seguro.

---

### B7. En el chatbot del notebook, ¿qué representa `servidor_v1` frente a `servidor_v2`?

**Respuesta:** `v1` procesa usuarios uno tras otro (secuencial). `v2` usa `asyncio.gather` para atender muchas peticiones concurrentes, solapando I/O y reduciendo mucho el tiempo total para N usuarios.

---

## Parte C — Notebook 03: Paralelismo y benchmarks

### C1. ¿Qué ventaja conceptual tiene `create_task` frente a `gather` cuando hay trabajo independiente mientras esperas otra coroutine?

**Respuesta:** Con `create_task` puedes lanzar una tarea y seguir ejecutando código (p. ej. CPU) hasta el `await` donde realmente necesitas el resultado. `gather` actúa más como barrera: esperas todas las tareas que agrupaste antes de seguir.

---

### C2. ¿Cuándo prefieres `asyncio.as_completed` frente a `gather`?

**Respuesta:** Cuando quieres procesar resultados en cuanto van llegando (latencias heterogéneas), en lugar de esperar al más lento para obtener cualquier resultado.

---

### C3. Describe el patrón productor-consumidor con `asyncio.Queue` y el papel del sentinel.

**Respuesta:** El productor hace `put` de ítems; los consumidores hacen `get`, procesan y `task_done`. Para terminar, se envían valores centinela (p. ej. `None`) para que cada worker sepa que debe salir sin quedar bloqueado en `get` forever.

---

### C4. ¿Por qué “fire-and-forget” con `create_task` puede ocultar excepciones y cómo se corrige?

**Respuesta:** Si no haces `await` ni revisas la tarea, el error puede quedar en el `Task` hasta que el loop lo marque como fallido. Un patrón es `add_done_callback` que llame a `exception()` y registre el error.

---

### C5. Para I/O simulado, ¿qué comparan `ThreadPoolExecutor` y `asyncio.gather`?

**Respuesta:** Ambos permiten solapar esperas. Los threads usan varios hilos OS con código bloqueante (`time.sleep`); asyncio usa un solo hilo y `await asyncio.sleep`. Para I/O puro simulado suelen acercarse en tiempo; asyncio evita el overhead de muchos hilos.

---

### C6. En CPU-bound, ¿qué muestra la comparación threading vs `ProcessPoolExecutor`?

**Respuesta:** Threading no escala por el GIL. `ProcessPoolExecutor` lanza procesos con memoria separada y puede usar varios núcleos de verdad para código Python CPU-bound (asumiendo trabajo repartible y overhead de serialización aceptable).

---

### C7. ¿Por qué `lambda` en `ProcessPoolExecutor.map` puede fallar y cuáles son dos arreglos?

**Respuesta:** El worker debe recibir una función serializable (pickle). Las lambdas a menudo dan problemas. Arreglos: función nombrada en el nivel adecuado (`def cuadrado(x): ...`) o `functools.partial` sobre una función picklable con argumentos fijos.

---

### C8. ¿Qué muestra el benchmark “pool por petición” vs “pool compartido”?

**Respuesta:** Crear y destruir un `ProcessPoolExecutor` en cada petición añade el coste de arrancar/terminar procesos repetidamente. Reutilizar un pool amortiza ese coste.

---

### C9. Explica la versión “a” vs “b” de M5b (asyncio + CPU local).

**Respuesta:** **a)** I/O con `await asyncio.sleep` pero inferencia CPU con `time.sleep` en la misma coroutine: bloquea el event loop y serializa el trabajo de otras peticiones. **b)** I/O en asyncio y CPU en `run_in_executor` con `ProcessPoolExecutor`: la inferencia no bloquea el loop y puede paralelizarse entre procesos. La mejora se relaciona con Amdahl: la parte que antes era secuencial en el loop limitaba el speedup.

---

### C10. ¿Qué limita el speedup según la intuición de Amdahl en un sistema híbrido I/O + CPU?

**Respuesta:** La fracción del trabajo que no puede paralelizarse (o que bloquea el único hilo del loop) impone un techo: aunque el resto sea infinitamente paralelo, el tiempo no puede bajar de esa parte serial.

---

## Parte D — Sección de código

Preguntas sobre fragmentos reales o típicos de los notebooks. Intenta predecir salida o corregir antes de leer la respuesta.

---

### D1. ¿Qué está mal en este lanzamiento de hilos para medir paralelismo?

```python
for i in range(4):
    h = threading.Thread(target=tarea_cpu, args=(N,))
    h.start()
    h.join()
```

**Respuesta:** `join()` inmediatamente después de cada `start()` serializa la ejecución: termina un hilo antes de arrancar el siguiente. Lo correcto es un bucle de `start()` para todos y otro bucle de `join()` para todos.

---

### D2. Corrige el `Thread` para que el trabajo se ejecute **en** el hilo (no en el principal).

```python
# Incorrecto
h = threading.Thread(target=tarea_cpu(N))
```

**Respuesta:** `target` debe ser la función, no el resultado de llamarla. Usa `threading.Thread(target=tarea_cpu, args=(N,))`.

---

### D3. ¿Por qué este `gather` no solapa bien las tareas?

```python
async def trabajo():
    time.sleep(1.0)  # "espera" 1 segundo
    return "listo"

await asyncio.gather(trabajo(), trabajo(), trabajo())
```

**Respuesta:** `time.sleep` bloquea el hilo del event loop; las tres coroutines no avanzan en paralelo durante la espera. Sustituir por `await asyncio.sleep(1.0)`.

---

### D4. Completa el servidor concurrente (M4) equivalente a un `for` secuencial de peticiones.

```python
async def servidor_v1(n):
    resultados = []
    for i in range(n):
        resultados.append(await handle_request(i))
    return resultados

# Versión concurrente (M4):
async def servidor_v2(n):
    # ...
```

**Respuesta:** `return await asyncio.gather(*[handle_request(i) for i in range(n)])` (o construir la lista de tareas y pasarla a `gather`).

---

### D5. Protege el incremento con un lock (solo la parte crítica).

```python
contador = [0]
lock = threading.Lock()

def inc():
    for _ in range(1000):
        # ¿?
        contador[0] += 1
```

**Respuesta:** `with lock:` rodeando `contador[0] += 1` (toda la operación read-modify-write debe ser atómica respecto a otros hilos).

---

### D6. ¿Qué imprime aproximadamente este código async (I/O simulado) y por qué?

```python
async def t():
    await asyncio.sleep(1.0)

t0 = time.perf_counter()
await asyncio.gather(t(), t(), t())
print(time.perf_counter() - t0)
```

**Respuesta:** Un valor cercano a **1 s**, no 3 s, porque las tres esperas se solapan: `gather` programa las tres coroutines y el loop avanza mientras todas están en `sleep`.

---

### D7. Arregla el `ProcessPoolExecutor` sin usar `lambda`.

```python
# Puede fallar al serializar
with ProcessPoolExecutor() as pool:
    r = list(pool.map(lambda x: x ** 2, [1, 2, 3]))
```

**Respuesta:** Define `def cuadrado(x): return x * x` y usa `pool.map(cuadrado, [1, 2, 3])`, o `functools.partial` sobre una función picklable con argumentos fijos.

---

### D8. Escribe el patrón mínimo de **productor + 2 workers** con `asyncio.Queue` y sentinel `None` para terminar.

**Respuesta modelo (esquema):**

```python
async def productor(q, n_items, n_workers):
    for i in range(n_items):
        await q.put(i)
    for _ in range(n_workers):
        await q.put(None)

async def worker(q, nombre):
    while True:
        item = await q.get()
        try:
            if item is None:
                return
            await asyncio.sleep(0.1)  # procesar
        finally:
            q.task_done()

# await asyncio.gather(productor(q, 10, 2), worker(q, "A"), worker(q, "B"))
```

---

### D9. Versión M5b: completa la línea que mueve la CPU fuera del event loop.

```python
async def peticion(user_id):
    await asyncio.sleep(0.1)          # I/O
    historial = f"user-{user_id}"
    # Inferencia CPU pesada (bloqueante) — no bloquear el loop:
    return await ???  # loop.run_in_executor(pool, inferencia_local, historial)
```

**Respuesta:** `return await asyncio.get_running_loop().run_in_executor(pool, inferencia_local, historial)` (asumiendo `pool = ProcessPoolExecutor(...)` creado y gestionado en el mismo contexto).

---

### D10. ¿Qué hace este callback en una tarea fire-and-forget?

```python
def log_si_falla(task):
    exc = task.exception()
    if exc:
        print("Error:", exc)

t = asyncio.create_task(puede_fallar())
t.add_done_callback(log_si_falla)
```

**Respuesta:** Cuando la tarea termina, el callback revisa si hubo excepción con `.exception()` y la registra; así no queda “silenciada” si nunca haces `await` a la tarea.

---

## Cierre

- Si dominas A–D sin mirar, llevas bien los tres notebooks.
- Repasa los experimentos donde mediste tiempos: saber **qué** comparaste es tan importante como el resultado numérico.
