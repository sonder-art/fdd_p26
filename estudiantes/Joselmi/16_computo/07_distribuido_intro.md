---
title: "Cómputo Distribuido — Introducción Conceptual y Síntesis"
---

# Cómputo Distribuido — Introducción Conceptual y Síntesis

Los modelos M1–M5 operan dentro de una sola máquina. El cómputo distribuido rompe esa frontera: múltiples máquinas físicamente separadas cooperan para resolver un problema. Este archivo es conceptual — la implementación real (Ray, Dask, sistemas de mensajería) es tema de un módulo posterior.

---

## Modelo 6 — Distribuido (M6)

### En la cocina

N restaurantes en ciudades distintas — cada uno con su propia despensa, su propia cocina, su propio equipo y sus propios relojes de pared. Un pedido que llega al restaurante de CDMX no puede acceder directamente a los ingredientes del restaurante de GDL. La comunicación entre restaurantes es por mensajero físico: tarda tiempo real en llegar, y puede llegar tarde, en desorden, o perderse.

Esto es radicalmente diferente de tener múltiples estaciones en la misma cocina (M5): allí todos comparten el mismo espacio y se comunican al instante.

### En lenguaje natural

Múltiples máquinas físicamente separadas, cada una con su propia memoria, coordinadas por red. La comunicación tiene latencia no despreciable. No existe un reloj global que sincronice los eventos de todas las máquinas.

### Formalmente

```
M6 — Distribuido:
N ≥ 2 nodos   (máquinas físicamente separadas)

Para todo nᵢ, nⱼ ∈ Nodos, i ≠ j:
  (1) Mem(nᵢ) ∩ Mem(nⱼ) = ∅        no hay memoria compartida entre nodos
  (2) δᵢⱼ > 0                        latencia de red no despreciable
  (3) ∄ reloj global                  no existe un reloj único y sincronizado
```

### La analogía mapeada formalmente

```
Ciudad separada            ↔  nodo físico     ↔  nᵢ ∈ Nodos
Despensa propia            ↔  RAM del nodo    ↔  Mem(nᵢ), aislada
Mensajero entre ciudades   ↔  mensaje de red  ↔  msg: nᵢ → nⱼ
Tiempo de viaje            ↔  latencia de red ↔  δᵢⱼ > 0
Relojes de pared distintos ↔  sin reloj global↔  ∄ t_global
```

### Las tres diferencias con M5 (paralelo)

| Eje | Paralelo (M5) | Distribuido (M6) |
|-----|--------------|-----------------|
| **Ubicación** | Misma máquina física, mismo OS | Máquinas físicamente separadas |
| **Latencia de comunicación** | IPC del OS (pipe, queue): δ ≈ μs | Red (HTTP, gRPC, TCP): δ ≈ ms a s |
| **Reloj** | Reloj de hardware compartido | Relojes locales independientes |

> **Nota:** en Python, `multiprocessing` ya usa procesos con memoria aislada (`Mem(pᵢ) ∩ Mem(pⱼ) = ∅`). La diferencia entre paralelo y distribuido NO es "memoria compartida vs no" — es **latencia de comunicación y ubicación física**.

---

## El problema del reloj global

En una sola máquina, existe un reloj de hardware que todos los procesos comparten. El OS puede ordenar eventos con precisión de nanosegundos.

En un sistema distribuido, cada nodo tiene su propio reloj — y estos relojes divergen inevitablemente:

```
- Osciladores de cuarzo con frecuencias ligeramente distintas
- Temperatura y voltaje afectan la velocidad del reloj
- NTP (Network Time Protocol) sincroniza aproximadamente, con error de ms
```

### El problema concreto con el chatbot v4

```
Servidor CDMX (reloj local: 10:00:00.001):
  Petición de usuario_A llega
  timestamp_local = "10:00:00.001"

Servidor GDL (reloj local: 10:00:00.000 — 1ms adelantado):
  Petición de usuario_B llega
  timestamp_local = "10:00:00.000"

¿Cuál llegó primero?
  Por timestamps locales: usuario_B (GDL) parece anterior
  Por realidad física: puede haber llegado después
```

No podemos saber cuál llegó primero solo comparando timestamps locales de servidores distintos. Esto importa para: ordenamiento de transacciones, consistencia de historial de chat, debugging de eventos distribuidos.

### La solución conceptual: Relojes Lógicos

Sin reloj global, los sistemas distribuidos usan **relojes lógicos** para ordenar eventos causalmente:

- **Relojes de Lamport:** cada nodo mantiene un contador entero. Al enviar un mensaje, incluye su contador. Al recibir, el receptor actualiza al máximo + 1. Garantiza: si A causó B, entonces timestamp(A) < timestamp(B).

- **Relojes Vectoriales:** cada nodo mantiene un vector de contadores (uno por nodo). Permiten detectar concurrencia real entre eventos: dos eventos son concurrentes si ninguno causó al otro.

---

## Chatbot v4 — el sistema distribuido

### En la cocina

La cadena de restaurantes tiene una sede central de pedidos online que distribuye las órdenes entre sucursales. Cada sucursal procesa las órdenes de forma independiente. Hay un sistema de mensajería entre sucursales para coordinar pedidos grandes. Cada sucursal escala por sí sola añadiendo más cocineros.

### Arquitectura

```
                 Internet
    Usuarios ────────────→ Balanceador de carga (nginx / cloud LB)
                              │           │
                     ┌────────┴──┐   ┌────┴────────┐
                     │ Servidor  │   │  Servidor   │
                     │  CDMX     │   │   GDL       │
                     │ (v3: M5b) │   │  (v3: M5b)  │
                     └────┬──────┘   └──────┬──────┘
                          │                 │
                     ┌────┴─────────────────┴────┐
                     │     Cola de mensajes       │
                     │  (Redis / RabbitMQ)        │
                     └────────────────────────────┘
                               │
                     ┌─────────┴────────────────┐
                     │    Workers LLM           │
                     │  (GPUs en la nube)       │
                     └──────────────────────────┘
```

**Propiedades formales del sistema:**

```
Cada servidor: Mem(CDMX) ∩ Mem(GDL) = ∅  ← sin memoria compartida
Comunicación:  δ_CDMX↔GDL > 0            ← latencia de red real
Escalado:      agregar servidores sin límite de cores (vs Amdahl en M5)
```

El balanceador distribuye peticiones entre instancias. Las colas de mensajes desacoplan servidores de workers GPU. Cada componente escala independientemente.

**Scope de este módulo:** entender conceptualmente qué es M6 y por qué es diferente de M5. La implementación real (Ray, Dask, Celery, Kafka) requiere infraestructura específica — tema de un módulo posterior.

---

## La evolución del chatbot: v1 → v4

```
Chatbot v1 — Secuencial (M1)
  Un usuario a la vez
  T_total = N × T_usuario
  Latencia con 100 usuarios: 155s  [Escenario A]
  ↓ problema: CPU idle durante I/O (99.94% del tiempo)

Chatbot v2 — Concurrent + Async (M4)  [Escenario A optimizado]
  N usuarios simultáneos con asyncio
  T_total ≈ T_max_usuario ≈ 1.55s
  ↓ pregunta: ¿y si el LLM es local? → inferencia bloquea el event loop

Chatbot v3 — Parallel + Async (M5b)  [Escenario B]
  asyncio para I/O + ProcessPoolExecutor para inferencia
  Speedup de inferencia ≈ P (limitado por Amdahl)
  ↓ límite: una máquina tiene P cores finitos

Chatbot v4 — Distribuido (M6)
  Múltiples servidores + balanceador + cola de mensajes
  Escalado horizontal: agregar máquinas sin límite de cores
  Desafíos: consistencia, latencia de red, ausencia de reloj global
```

---

## Síntesis final: los 6 modelos

| Modelo | Condición formal clave | Analogía | Escenario chatbot | Librería principal |
|--------|----------------------|----------|-------------------|-------------------|
| **M1** Secuencial | end(τᵢ) ≤ start(τⱼ) | Cocinero: una orden completa antes de la siguiente | v1: 1 usuario a la vez | (ninguna) |
| **M2** Async no concurrent | wait≠∅ pero exec(τⱼ) ∩ wait(τᵢ) = ∅ | Cocinero parado frente al horno | Anti-patrón: `await fn1(); await fn2()` | asyncio (mal usado) |
| **M3** Concurrent no async | Solapamiento, wait=∅, P=1 | Turnos con los cuchillos únicos | CPU-bound con threading — evitar | `threading` (ineficiente) |
| **M4** Concurrent + async | exec(τⱼ) ∩ wait(τᵢ) ≠ ∅, H=1 | Lista de pendientes, aprovecha el horno | v2: Escenario A, LLM API | `asyncio` |
| **M5a** Paralelo puro | ∃t: exec(τᵢ) ∩ exec(τⱼ) ≠ ∅, wait=∅ | Dos estaciones CPU-bound | Procesamiento numérico masivo | `ProcessPoolExecutor`, `joblib` |
| **M5b** Paralelo + async | ∃t: exec(τᵢ) ∩ exec(τⱼ) ≠ ∅, wait≠∅ | Dos estaciones con hornos, coordinadas | v3: Escenario B, LLM local | `asyncio` + `ProcessPoolExecutor` |
| **M6** Distribuido | N≥2 nodos, Mem∩Mem=∅, δ>0, ∄ reloj | N restaurantes en ciudades distintas | v4: múltiples servidores | Ray, Dask, Celery |

### La jerarquía

```
Distribuido ⊇ Paralelo ⊇ Concurrente    (jerarquía de alcance)
Asíncrono: ortogonal — se combina con cualquier nivel

Dentro de Python:
  Concurrente (M3, M4): mismo proceso, mismo OS
  Paralelo    (M5):     múltiples procesos, misma máquina
  Distribuido (M6):     múltiples máquinas, red de por medio
```

---

:::exercise{title="Reflexión de cierre"}
Regresa a la pregunta de `01_procesos_y_hilos.md`: "si tu chatbot recibe 10 peticiones simultáneas y cada una tarda ~1.55s, ¿cuánto tiempo espera el último usuario?"

Ahora responde para los 4 modelos:

1. **v1 (M1):** latencia del usuario 10 — justifica con end(τᵢ) ≤ start(τᵢ₊₁)
2. **v2 (M4, Escenario A):** latencia del usuario 10 — justifica con exec(τⱼ) ∩ wait(τᵢ) ≠ ∅
3. **v3 (M5b, Escenario B):** si la inferencia tarda 2s y tienes P=4 cores, ¿cuál es el speedup esperado con S≈0.05?
4. **v4 (M6):** con 3 servidores v3 en el balanceador, ¿cuántos usuarios concurrentes puedes manejar antes de degradar?
:::
