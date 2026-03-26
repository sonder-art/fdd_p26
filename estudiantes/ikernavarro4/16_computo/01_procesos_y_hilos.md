---
title: "Procesos, Hilos y el GIL"
---

# Procesos, Hilos y el GIL

Antes de hablar de concurrencia o paralelismo, necesitamos tener claro qué es lo que se ejecuta. Todo modelo de ejecución opera sobre procesos y hilos. En este archivo los definimos con precisión — en los tres lenguajes que usaremos en todo el módulo: la analogía de cocina, el lenguaje de cómputo y las matemáticas.

---

## El sistema que construiremos: un chatbot

A lo largo del módulo construimos este sistema:

```
  Usuario A ──┐
  Usuario B ──┤──▶  [ Servidor chatbot ]  ──▶  [ LLM ]  ──▶  respuesta
  Usuario C ──┘           (Python)
                               │
                               ▼
                         [ Base de datos ]
                         (historial de chat)
```

Una petición recorre estas etapas:

```
recv_request
    │  exec ~1ms   (parsear JSON, validar)
    ▼
read_BD
    │  wait ~50ms  (consultar historial del usuario)
    ▼
[llamar al LLM]          ← aquí está la diferencia entre escenarios
    │
    ▼
send_response
    │  wait ~5ms   (escribir socket)
    ▼
  done
```

### Escenario A — LLM como API remota

El LLM está en los servidores de OpenAI, Anthropic, Google, etc. La llamada es una petición HTTP.

```
recv(1ms exec) → read_BD(50ms wait) → API LLM(1500ms wait) → send(5ms wait)

exec_total / T_petición ≈  1ms / 1556ms  ≈  0.06%
wait_total / T_petición ≈ 99.94%

→ I/O-bound  →  M4 (asyncio) es el modelo óptimo
```

### Escenario B — LLM local en hardware propio

El LLM corre en la misma máquina (llama.cpp, ollama, vLLM). La inferencia usa CPU/GPU local.

```
recv(1ms exec) → read_BD(50ms wait) → inferencia(2000ms exec) → send(5ms wait)

exec_total / T_petición ≈ 2001ms / 2056ms ≈ 97%
wait_total / T_petición ≈  3%

→ CPU-bound  →  M5b (asyncio + ProcessPoolExecutor) es el modelo óptimo
```

![Descomposición exec/wait por escenario](./images/chatbot_timeline.png)

Estos dos escenarios atraviesan todo el módulo. En cada modelo de ejecución preguntaremos: ¿esto conviene más para el Escenario A, para el B, o para ambos?

---

## La analogía: el restaurante

Usaremos un restaurante como modelo del sistema computacional. Esta analogía se define **una sola vez aquí** y se referenciará en todos los archivos del módulo sin redefinirla.

### Tabla de correspondencia completa

| Analogía (cocina) | Cómputo (OS/Python) | Matemáticas |
|---|---|---|
| **Restaurante** | Computadora | — |
| **Fogón / quemador** | CPU core | c ∈ Cores, \|Cores\| = P |
| **Despensa / refrigerador** | RAM (espacio de memoria) | Mem: Addr → Value |
| **Horno, cafetera, tostadora** | Dispositivo I/O (disco, red, GPU) | IO = {disk, net, gpu, ...} |
| **Pared sellada entre estaciones** | Aislamiento de memoria entre procesos | Mem(pᵢ) ∩ Mem(pⱼ) = ∅ |
| **Estación de cocina** (tiene su propia despensa) | Proceso | p ∈ Proc |
| **Cocinero** (trabaja dentro de una estación) | Hilo | θ ∈ Thread(p) |
| **Despensa compartida entre cocineros** | Heap compartido dentro del proceso | ∀ θₐ, θᵦ ∈ Thread(p): comparten Mem(p) |
| **Chef jefe / tablero de órdenes** | Scheduler del OS | sched: Thread → Core × Time |
| **Timbre de turno** (cada N segundos) | Quantum de scheduling | q ∈ ℝ⁺ |
| **Cambiar al cocinero en el fogón** | Context switch | overhead δ_ctx > 0 por switch |
| **Mensajero entre estaciones** | IPC (pipe, queue, socket) | msg: Proc × Proc → Data |
| **El único juego de cuchillos** (Python) | GIL | ver sección GIL más abajo |
| **Ticket de orden** | Tarea | τᵢ ∈ Task |
| **Cocinero trabajando activamente** (corta, mezcla, emplata) | CPU execution | exec(τᵢ) ⊆ T |
| **Orden esperando en el horno / timer** | I/O wait | wait(τᵢ) ⊆ T |

---

## Proceso

**En la cocina:** una estación de trabajo con su propia despensa, utensilios y área de trabajo. Ninguna otra estación puede meter la mano en su refrigerador. Si la estación A quiere pasarle algo a la estación B, debe hacerlo a través del mensajero (IPC) — no puede leer directamente de la despensa de B.

**En cómputo:** el OS crea un proceso cuando lanzas un programa. Tiene su propio heap, stack, descriptores de archivo y variables de entorno. La comunicación con otros procesos requiere mecanismos explícitos (IPC).

**Formalmente:**
```
Proc = conjunto de procesos en ejecución
p ∈ Proc
Mem(p) = espacio de direcciones del proceso p

Aislamiento:  ∀ pᵢ, pⱼ ∈ Proc, i ≠ j:  Mem(pᵢ) ∩ Mem(pⱼ) = ∅
```

**En el chatbot:** `python servidor_chatbot.py` crea un proceso con su propio Mem(p). En el Escenario B, `ProcessPoolExecutor` crea procesos adicionales con memoria aislada — por eso los resultados de la inferencia deben serializarse para volver al proceso principal.

---

## Hilo (Thread)

**En la cocina:** cocineros que trabajan en la misma estación. Todos usan la misma despensa — si uno mueve un ingrediente, los demás lo ven inmediatamente. Esto acelera la comunicación pero crea el riesgo de que dos cocineros intenten usar el mismo utensilio al mismo tiempo.

**En cómputo:** un proceso puede tener H ≥ 1 hilos. Todos comparten el heap del proceso pero tienen su propio stack y contador de programa. El OS los puede asignar a distintos cores.

**Formalmente:**
```
Thread(p) = conjunto de hilos del proceso p
θ ∈ Thread(p)

Memoria compartida:  ∀ θₐ, θᵦ ∈ Thread(p):  ambos acceden a Mem(p)
```

**Diagrama de memoria:**
```
┌─────────────────────────────┐    ┌─────────────────────────────┐
│        Proceso A            │    │        Proceso B            │
│  ┌──────────────────────┐   │    │  ┌──────────────────────┐   │
│  │    Heap de A         │   │    │  │    Heap de B         │   │
│  │  (variables, objetos)│   │    │  │  (variables, objetos)│   │
│  └──────────────────────┘   │    │  └──────────────────────┘   │
│  ┌────────┐  ┌────────┐     │    │  ┌────────┐  ┌────────┐     │
│  │Hilo θ₁ │  │Hilo θ₂ │     │    │  │Hilo θ₃ │  │Hilo θ₄ │     │
│  │stack   │  │stack   │     │    │  │stack   │  │stack   │     │
│  └────────┘  └────────┘     │    │  └────────┘  └────────┘     │
│  θ₁ y θ₂ comparten Heap A   │    │  θ₃ y θ₄ comparten Heap B  │
└─────────────────────────────┘    └─────────────────────────────┘
       Mem(A) ∩ Mem(B) = ∅
```

**En el chatbot:** en el Escenario A, un servidor asyncio usa un solo hilo (el event loop) que maneja cientos de conexiones I/O-bound — no necesita varios hilos porque el tiempo de espera de la API LLM es tan largo que con un solo hilo se pueden intercalar muchas peticiones.

---

## I/O-bound vs CPU-bound

Esta distinción determina **qué modelo de ejecución conviene usar**. Es la pregunta más importante antes de elegir entre asyncio, threading o multiprocessing.

**En la cocina:**
- **CPU-bound** = trabajo puro de cuchillo — cortar, mezclar, batir. El cocinero no puede alejarse del fogón; requiere atención continua.
- **I/O-bound** = poner algo en el horno o la cafetera. El cocinero puede alejarse mientras el dispositivo trabaja. Cuando el temporizador suene, vuelve.

**En cómputo:**
```
CPU-bound  ≡  wait(τᵢ) = ∅
               (la tarea requiere CPU continuamente — no espera dispositivos externos)

I/O-bound  ≡  wait(τᵢ) ≠ ∅
               (la tarea delega trabajo a dispositivos externos y espera su respuesta)
```

*(La notación exec/wait se define formalmente en `02_secuencial.md`)*

**En el chatbot:**

| Operación | Escenario A | Escenario B |
|---|---|---|
| recv + parsear JSON | exec (CPU) | exec (CPU) |
| leer BD historial | wait (I/O) | wait (I/O) |
| LLM | **wait (API remota, I/O)** | **exec (inferencia local, CPU)** |
| send respuesta | wait (red, I/O) | wait (red, I/O) |
| **Tipo dominante** | **I/O-bound → M4** | **CPU-bound → M5b** |

---

## Context Switch y Quantum

**En la cocina:** el chef jefe pone un timbre. Cuando suena, el cocinero en el fogón debe soltar exactamente lo que está haciendo, anotar su estado en una libreta ("estaba en el paso 3 de la salsa, el agua hervía, tenía la sartén a 180°"), y el siguiente cocinero toma su lugar leyendo esa libreta. Esto lleva tiempo — el tiempo de leer y escribir la libreta es el overhead δ_ctx.

**En cómputo:** el scheduler del OS asigna CPU cores a hilos usando *time-slicing*. Cada hilo tiene un **quantum** q (típicamente 1–100ms). Al agotarse, el scheduler hace un **context switch**: guarda el estado del hilo actual (registros, stack pointer, program counter) y restaura el estado del siguiente.

**Formalmente:**
```
q ∈ ℝ⁺          quantum de scheduling (duración máxima de un turno)
δ_ctx > 0        overhead de context switch (guardar/restaurar estado)
```

> **Implicación importante:** N context switches producen un overhead total N × δ_ctx. Si los hilos son CPU-bound y hay muchos switches, este overhead puede dominar sobre el trabajo útil. Esto es clave para entender el Modelo M3.

---

## El GIL — Global Interpreter Lock

El GIL es una restricción **específica de CPython** (la implementación estándar de Python). Es la razón por la que threading en Python no produce paralelismo real para tareas CPU-bound.

**En la cocina:** hay un único juego de cuchillos de chef en toda la estación. Cualquier cocinero que quiera trabajar activamente debe tomar los cuchillos. Solo uno puede tenerlos a la vez — no importa cuántos cocineros haya ni cuántos fogones estén libres.

**En cómputo:** el GIL es un mutex que protege el estado interno del intérprete de Python. Solo un hilo puede ejecutar bytecode Python a la vez.

**Formalmente:**
```
GIL constraint:
∀ t: |{θ ∈ Thread(p) | θ ejecuta bytecode Python en t}| ≤ 1

En cualquier instante, a lo mucho UN hilo por proceso puede ejecutar
bytecode Python — sin importar cuántos cores físicos tenga la máquina.
```

**La excepción crítica — cuando el GIL se libera:**

**En la cocina:** mientras una orden está en el horno (I/O wait), el cocinero suelta los cuchillos. Otro cocinero puede tomarlos y trabajar en otra orden. Pero si el trabajo es pure-knife work (CPU-bound), el cocinero nunca suelta los cuchillos, y los demás esperan sin hacer nada.

**Formalmente:**
```
Durante wait(τᵢ): el hilo θᵢ suelta el GIL
→ otro hilo θⱼ puede tomarlo y ejecutar
→ por eso threading SÍ funciona para I/O-bound
→ por eso threading NO funciona para CPU-bound
```

| Tipo de tarea | GIL durante ejecución | Threading ayuda |
|---|---|---|
| CPU-bound (wait = ∅) | Nunca se libera | No — serializa los hilos |
| I/O-bound (wait ≠ ∅) | Se libera durante el wait | Sí — otro hilo avanza |

**En el chatbot:**
- **Escenario A** (API remota, I/O-bound): el GIL se libera durante la llamada HTTP → threading podría funcionar, pero asyncio es más eficiente y más escalable.
- **Escenario B** (inferencia local, CPU-bound): el GIL **nunca** se libera durante la inferencia → threading es inútil → necesitamos `multiprocessing` (procesos separados, cada uno con su propio GIL).

---

## Arquitectura del chatbot según el escenario

```
Escenario A — API remota (I/O-bound)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                 ┌─────────────────────────────┐
  petición ───▶  │  Proceso principal           │ ──▶ API OpenAI (HTTPS)
                 │  event loop asyncio          │          │
                 │  1 hilo, N coroutines        │ ◀── resp │
                 │  maneja 100s de peticiones   │
                 └─────────────────────────────┘
                               │
                         ┌─────┴──────┐
                         │  Base de   │
                         │  datos     │
                         └────────────┘

Escenario B — LLM local (CPU-bound)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                 ┌─────────────────────────────┐
  petición ───▶  │  Proceso principal           │
                 │  event loop asyncio          │
                 │  maneja recv / BD / send     │
                 └──────────┬──────────────────┘
                            │  run_in_executor (IPC — datos serializados)
               ┌────────────┼────────────┐
               ▼            ▼            ▼
          ┌─────────┐ ┌─────────┐ ┌─────────┐
          │Worker 1 │ │Worker 2 │ │Worker 3 │
          │proceso  │ │proceso  │ │proceso  │
          │inferLLM │ │inferLLM │ │inferLLM │
          └─────────┘ └─────────┘ └─────────┘
          (ProcessPoolExecutor — P procesos paralelos)
```

### Lectura del diagrama — Escenario A

El proceso principal es **un único proceso Python** con **un único hilo del OS** (el event loop). Dentro de ese hilo corren N *coroutines* — funciones que ceden control voluntariamente al event loop cuando llegan a un `await`. Cuando una petición espera la respuesta de la API de OpenAI (wait ≈ 1500ms), el hilo no se bloquea: el event loop pasa a atender otra petición. Desde el punto de vista del OS, es siempre el mismo hilo ejecutando; desde el punto de vista del GIL, nunca hay conflicto porque solo hay un hilo. La base de datos también es I/O-bound — el event loop la maneja con el mismo mecanismo.

**Por qué funciona:** el 99.94% del tiempo de cada petición es espera de dispositivos externos. Con un solo hilo podemos intercalar cientos de esas esperas. No necesitamos más procesos ni más hilos.

### Lectura del diagrama — Escenario B

Aquí hay **dos niveles de procesos**. El proceso principal sigue siendo el event loop asyncio: recibe peticiones, consulta la BD, envía respuestas — todo I/O-bound, igual que en A. Pero la inferencia del LLM local es CPU-bound: mantiene el hilo ocupado durante ~2000ms, lo que bloquearía el event loop y paralizaría al servidor entero.

La solución es `run_in_executor`: el event loop delega la inferencia a un `ProcessPoolExecutor`. Cada worker es un **proceso separado** — con su propio intérprete Python y su propio GIL. Por eso pueden ejecutar Python puro en paralelo real. Los datos del historial viajan del proceso principal a cada worker por IPC (serialización via `pickle`); el resultado regresa por el mismo canal. Desde el punto de vista del event loop, esta delegación es un `wait(τᵢ)` más — puede seguir atendiendo nuevas peticiones mientras los workers procesan en paralelo.

**Por qué es necesario multiprocessing y no threading:** la inferencia nunca libera el GIL (no hay I/O). Con `threading`, los hilos se turnarían en lugar de ejecutar en paralelo. Los procesos separados son la única forma de usar múltiples cores para código Python puro.

---

### Hoja de ruta del módulo

Esta es la arquitectura hacia la que construimos. Cada archivo y notebook cubre un eslabón específico:

| Archivo | Contenido | Versión chatbot | Escenario |
|---------|-----------|-----------------|-----------|
| **`01` (este archivo)** + notebook `01` | Procesos, hilos, GIL, I/O-bound vs CPU-bound | base conceptual | A y B definidos |
| **`02`** + notebook `01` | Modelo secuencial M1 — por qué falla con múltiples usuarios | chatbot v1 | A: 155s para 100 usuarios |
| **`03`** | Concurrencia M2/M3/M4 — qué es solapamiento, qué es async | framework teórico | A en M4, B excluido por GIL |
| **`04a`** + notebook `02` | `asyncio` fundamentos — `async def`, `await`, `gather` | chatbot v2 | **A implementado** |
| **`04b`** + notebook `02` | `asyncio` patrones — `create_task`, `Queue`, anti-patrones | chatbot v2 refinado | A con backpressure |
| **`05`** + notebook `03` | Paralelismo M5, Ley de Amdahl, `ProcessPoolExecutor` | chatbot v3 | **B implementado** |
| **`06`** | Librerías Python y árbol de decisión | referencia | A→M4, B→M5b |
| **`07`** | Cómputo distribuido M6 — introducción conceptual | chatbot v4 conceptual | A y B escalados horizontalmente |

Cada notebook está diseñado para ejecutarse en orden. Las celdas sin completar son trabajo autónomo — no hay distinción explícita entre "en clase" y "tarea"; el límite es hasta dónde lleguemos juntos.

---

:::exercise{title="Reflexión previa al código"}
Antes de abrir el notebook, responde:

1. En el Escenario A, si el chatbot recibe 10 peticiones simultáneas y cada una tarda 1500ms en completarse, ¿cuánto tiempo espera el décimo usuario con un servidor secuencial? ¿Y con asyncio?

2. En el Escenario B, ¿por qué threading no resuelve el problema de la inferencia lenta aunque tengamos 8 cores disponibles?

3. ¿En qué se diferencia la arquitectura de los dos escenarios? ¿Qué componente cambia?
:::
