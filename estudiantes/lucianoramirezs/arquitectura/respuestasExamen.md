Prueba la IA directamente en tus aplicaciones favoritas … Usa Gemini para generar borradores y pulir contenido, y disfruta de Gemini Pro con acceso a la IA de nueva generación de Google por 395 MXN 0 MXN durante 1 mes
---
geometry: "top=1.2cm, bottom=1.2cm, left=1.6cm, right=1.6cm"
fontsize: 10pt
header-includes:
  - \usepackage{enumitem}
  - \usepackage{fancyhdr}
  - \usepackage{lastpage}
  - \usepackage{amsmath}
  - \setlist[enumerate]{topsep=1pt, itemsep=1pt, parsep=0pt}
  - \setlist[itemize]{topsep=1pt, itemsep=1pt, parsep=0pt}
  - \pagestyle{fancy}
  - \fancyhf{}
  - \renewcommand{\headrulewidth}{0pt}
  - \fancyfoot[R]{\footnotesize Página \thepage\ de \pageref{LastPage}}
  - \setlength{\parskip}{3pt}
  - \setlength{\parindent}{0pt}
---

\begin{center}
{\large \textbf{\underline{SOLUCIONARIO — Examen Parcial: Arquitectura y Cómputo (A)}}}
\end{center}

\begin{center}
\rule{\textwidth}{1.2pt}
{\normalsize \textbf{SECCIÓN I — ARQUITECTURA DE COMPUTADORAS (10 pts)}}
\rule{\textwidth}{0.4pt}
\end{center}

## PARTE A — Conceptos (5 pts)

### 1. (2 pts) Jerarquía de memoria

**Dibujo esperado:**

```
       Velocidad ↑     Capacidad ↓     Costo ↑

       ┌───────────┐
       │ Registros │  ~0.3 ns    < 1 KB
       └─────┬─────┘
       ┌─────┴─────┐
       │  Caché L1 │  ~1 ns      32-64 KB
       └─────┬─────┘
       ┌─────┴─────┐
       │  Caché L2 │  ~4 ns      256 KB - 1 MB
       └─────┬─────┘
       ┌─────┴─────┐
       │  Caché L3 │  ~40 ns     4-32 MB
       └─────┬─────┘
       ┌─────┴─────┐
       │    RAM    │  ~100 ns    8-64 GB
       └─────┬─────┘
       ┌─────┴─────┐
       │  SSD/NVMe │  ~0.1 ms    512 GB - 4 TB
       └─────┬─────┘
       ┌─────┴─────┐
       │    HDD    │  ~10 ms     1-20 TB
       └───────────┘
```

Patrón: velocidad ALTA arriba, BAJA abajo. Capacidad PEQUEÑA arriba, GRANDE abajo. Cada nivel es más lento pero más grande que el anterior.

**Criterio de evaluación:** Se espera al menos 5 niveles (registros, caché, RAM, SSD, HDD). Indicar correctamente que velocidad y capacidad son inversamente proporcionales. No es necesario dar números exactos de latencia.

\vspace{4pt}

**1.a) ¿Por qué existe esta jerarquía?**

Existe porque hay un **trade-off fundamental entre velocidad y capacidad** (y costo). La memoria más rápida (SRAM usada en registros y caché) es extremadamente cara por byte --- es imposible construir terabytes de SRAM. La memoria grande y barata (DRAM, disco) es lenta. La jerarquía resuelve esto explotando la **localidad** de los programas: los datos más usados (calientes) se copian automáticamente a niveles rápidos, y el resto queda en niveles lentos. Funciona porque los programas tienden a acceder repetidamente a los mismos datos (localidad temporal) y a datos cercanos en memoria (localidad espacial).

**Criterio:** Debe mencionar el trade-off velocidad/capacidad/costo Y por qué no se puede hacer toda la memoria rápida (costo o física). Mencionar localidad es un plus.

\vspace{4pt}

**1.b) VRAM del GPU**

La VRAM vive a un nivel comparable a la RAM del sistema en términos de latencia (~100ns), pero es **memoria dedicada** conectada al GPU con un bus de ancho de banda mucho mayor. Un GPU moderno con HBM3e alcanza ~3,000--3,350 GB/s internamente, vs ~100 GB/s de la DDR5 del sistema.

El GPU necesita su propia memoria porque:

1. Sus miles de cores necesitan alimentarse simultáneamente --- el bus PCIe entre CPU-RAM y GPU (~32 GB/s) sería un cuello de botella.
2. Si compartiera la RAM del sistema, competiría con el CPU y se saturaría el bus.
3. La VRAM está optimizada para el patrón de acceso del GPU: muchos accesos simultáneos a bloques contiguos.

**Criterio:** Debe identificar que la VRAM está al nivel de la RAM (no del caché). Debe justificar la necesidad de memoria separada con al menos una razón válida (ancho de banda, no saturar bus, paralelismo).

---

### 2. (1.5 pts) CPU vs GPU

**2.a) Filosofía de diseño**

- **CPU**: Pocos cores (8--24) muy potentes y complejos. Predicción de saltos, ejecución fuera de orden, caché jerárquico grande. Diseñado para hacer **pocas cosas complejas muy rápido**. Optimizado para lógica condicional, acceso irregular a datos, baja latencia por tarea.

- **GPU**: Miles de cores (16,000+) simples. Modelo SIMT (misma instrucción, múltiples datos). Sin predicción de saltos sofisticada. Diseñado para hacer **millones de cosas simples simultáneamente**. Optimizado para operaciones regulares y masivamente paralelas.

**Criterio:** Debe contrastar pocos-cores-complejos (CPU) vs muchos-cores-simples (GPU). Mencionar qué tipo de tarea resuelve mejor cada uno con la justificación correcta.

\vspace{4pt}

**2.b) Ejemplos**

- **CPU mejor**: Compilar código, recorrer un árbol de decisiones con ramas impredecibles, ejecutar un servidor web con lógica compleja. Justificación: flujo de control irregular, acceso impredecible a memoria, requiere predicción de saltos.

- **GPU mejor**: Multiplicar dos matrices grandes (entrenamiento de red neuronal), aplicar un filtro a cada pixel de una imagen, sumar dos arreglos de millones de elementos. Justificación: misma operación sobre muchos datos (SIMT), altamente paralelo, acceso regular a memoria.

**Criterio:** Un ejemplo correcto por cada uno con justificación que conecte con la diferencia de diseño. No basta decir "GPU para ML" sin explicar por qué.

---

### 3. (1.5 pts) Frecuencia del CPU

**3.a) ¿Por qué no se puede aumentar la frecuencia?**

El **power wall** (muro de potencia). Aumentar la frecuencia requiere aumentar el voltaje, y la potencia disipada crece de forma superlineal: $P \propto V^2 \times f$. Duplicar la frecuencia más que duplica el consumo energético, generando calor que no se puede disipar con refrigeración convencional. Alrededor de 2005 (~3--4 GHz), el calor hizo impracticable seguir subiendo. Además, a frecuencias muy altas las señales eléctricas no llegan a tiempo entre componentes del chip.

**Criterio:** Debe mencionar la relación potencia/calor con la frecuencia. "Se calienta demasiado" es válido si se explica por qué (más voltaje, más frecuencia → más calor). Mencionar la relación cuadrática con el voltaje es un plus.

\vspace{4pt}

**3.b) ¿Programa secuencial se beneficia de más cores?**

**No.** Un programa secuencial ejecuta instrucciones una tras otra en un solo hilo, usando un solo core. Los cores adicionales quedan ociosos. Para aprovechar múltiples cores, el programador debe **paralelizar explícitamente**: dividir el trabajo en tareas independientes usando hilos o procesos (threading, multiprocessing, asyncio + ProcessPoolExecutor).

**Criterio:** Respuesta clara "No" con justificación de que el programa usa un solo core. Debe mencionar que el programador tiene que hacer algo explícito para aprovechar los cores.

---

## PARTE B — Análisis aplicado (5 pts)

### 4. (5 pts) E-commerce

**4.a) Necesidad 1: Búsqueda (300 GB RAM, queries irregulares, <10ms)**

- **Componente crítico: RAM.** El índice de 300 GB debe caber entero en memoria para lograr latencia <10ms. Si cayera a disco (SSD ~0.1ms, HDD ~10ms), la latencia se dispararía.

- **Procesador: CPU**, no GPU. Las queries tienen **acceso irregular** (cada query toca partes diferentes del índice), lo cual causa muchos cache misses y patrones impredecibles. El GPU necesita accesos regulares y paralelos para ser eficiente (SIMT); el acceso irregular destruye su rendimiento. El CPU, con predicción de saltos, ejecución fuera de orden y caché jerárquico, maneja mucho mejor los patrones irregulares.

**Criterio:** Identificar RAM como componente crítico (1 pt). Elegir CPU con justificación del acceso irregular (1 pt). Si eligen GPU, deben justificar por qué el patrón irregular no es problema (difícil de sostener).

\vspace{4pt}

**4.b) Necesidad 2: Recomendaciones (inferencia NN, 8 GB, 500 req/s)**

**GPU.** La inferencia de redes neuronales consiste en multiplicaciones de matrices --- exactamente el patrón regular y masivamente paralelo para el que el GPU está diseñado. El modelo de 8 GB cabe en la VRAM de un GPU moderno (16--80 GB). El alto throughput (500 req/s) favorece al GPU porque puede procesar peticiones en batch, explotando su paralelismo.

**Criterio:** Elegir GPU con justificación conectada a la arquitectura (multiplicación de matrices, paralelismo). También se acepta NPU si se justifica correctamente. 1 pt.

\vspace{4pt}

**4.c) ¿Ambos en la misma máquina?**

Sí, es posible pero con conflictos:

1. **RAM**: Búsqueda necesita 300 GB + overhead del OS y recomendación → servidor de 320+ GB, costoso.
2. **Disponibilidad**: Si el servidor cae, pierdes ambos servicios.
3. **Interferencia de latencia**: El GPU puede generar interrupciones o consumir ancho de banda de memoria, degradando la latencia <10ms de búsqueda.

**Criterio:** Identificar al menos 2 conflictos concretos. 1.5 pts.

\vspace{4pt}

**4.d) Escalar a 5000 req/s**

Al menos 2 estrategias:

1. **Escalamiento horizontal**: Múltiples servidores con GPU detrás de un load balancer. Cada uno maneja una fracción del tráfico.
2. **Batching**: Agrupar múltiples peticiones en un solo batch (ej: 32 peticiones como una multiplicación de matrices). Multiplica throughput sin hardware adicional.

Otras válidas: cuantización del modelo (FP16/INT8), caché de resultados frecuentes, uso de NPU para serving, modelo más pequeño (destilación).

**Criterio:** 2 estrategias con justificación. 1.5 pts.

---

\begin{center}
\rule{\textwidth}{1.2pt}
{\normalsize \textbf{SECCIÓN II — CÓMPUTO (10 pts)}}
\rule{\textwidth}{0.4pt}
\end{center}

## PARTE A — Definiciones (5 pts)

### 5. (2 pts) Paradigma concurrente + asíncrono (M4)

**5.a) Definición formal**

Este es el **Modelo M4 --- Concurrente + Asíncrono**:

$$\exists\ \tau_i, \tau_j \in Task,\ i \neq j: [start(\tau_i), end(\tau_i)] \cap [start(\tau_j), end(\tau_j)] \neq \emptyset \quad \text{(concurrencia)}$$

$$\exists\ \tau_k \in Task: wait(\tau_k) \neq \emptyset \quad \text{(hay esperas I/O)}$$

$$\exists\ i \neq j: exec(\tau_j) \cap wait(\tau_i) \neq \emptyset \quad \text{(esperas explotadas --- asincronía)}$$

$$P = 1,\ H = 1 \quad \text{(un core, un hilo --- event loop)}$$

**Criterio:** Las tres condiciones deben estar presentes. La notación debe usar exec/wait/start/end. Mencionar P=1 es un plus. 1 pt.

\vspace{4pt}

**5.b) Diagrama de Gantt**

Cada petición: parsear(1ms, exec) → BD(50ms, wait) → responder(1ms, exec).

```
t(ms): 0  1  2  3          51 52  53          103 104
       |  |  |  |           |  |   |            |   |
U1:    [P]==================[R]
U2:       [P]====================[R]
U3:          [P]=========================[R]

P = parsear (1ms exec)     === = wait BD (50ms)     R = responder (1ms exec)
```

- t=0: U1 parsea (exec 1ms)
- t=1: U1 entra en wait(BD). Event loop toma U2, parsea (exec 1ms)
- t=2: U2 entra en wait(BD). Event loop toma U3, parsea (exec 1ms)
- t=3: U3 entra en wait(BD). Event loop idle.
- t=51: BD1 responde. U1 responde (exec 1ms)
- t=52: BD2 responde. U2 responde (exec 1ms)
- t=53: BD3 responde. U3 responde (exec 1ms)

**Tiempo total ≈ 54ms** (vs 156ms secuencial). Las esperas de BD se solapan.

**Criterio:** El diagrama debe mostrar que las esperas se solapan (las tres BD queries corren "en paralelo" desde la perspectiva del event loop). El exec de U2 debe ocurrir durante el wait de U1. Tiempo total debe ser significativamente menor que 156ms. 1 pt.

---

### 6. (1.5 pts) GIL

**6.a) Restricción formal**

$$\forall\ t: |\{\theta \in Thread(p) \mid \theta \text{ ejecuta bytecode Python en } t\}| \leq 1$$

En cualquier instante, **a lo mucho un hilo** por proceso Python puede ejecutar bytecode, sin importar cuántos cores tenga la máquina.

**Criterio:** La restricción debe decir "máximo 1 hilo ejecutando a la vez." La notación formal es ideal pero se acepta en lenguaje natural si es precisa. 0.5 pts.

\vspace{4pt}

**6.b) ¿Por qué threading NO acelera CPU-bound?**

Porque si la tarea es 100% exec ($wait(\tau_i) = \emptyset$), los hilos nunca sueltan el GIL voluntariamente. El scheduler los fuerza a turnarse (time-slicing), pero solo uno ejecuta en cualquier instante. El resultado es equivalente a secuencial **más** el overhead de context switches ($\delta_{ctx} > 0$). Threading es **peor** que secuencial para CPU-bound en Python.

**Criterio:** Debe explicar que el GIL impide ejecución simultánea y que el overhead lo hace peor que secuencial. 0.5 pts.

\vspace{4pt}

**6.c) ¿Cuándo SÍ ayudan los hilos?**

Cuando la tarea es **I/O-bound** ($wait(\tau_i) \neq \emptyset$). Durante I/O (red, disco, BD), el hilo **suelta el GIL** mientras espera. Otro hilo puede tomarlo y ejecutar. Ejemplo: descargar 100 archivos en paralelo --- cada hilo espera la red, y mientras tanto otros hilos lanzan sus descargas.

**Criterio:** Debe identificar I/O-bound y explicar que el GIL se suelta durante I/O. Dar un ejemplo concreto. 0.5 pts.

---

### 7. (1.5 pts) Ley de Amdahl (S = 25%)

Fórmula: $Speedup(P) = \dfrac{1}{S + \dfrac{1-S}{P}}$

\vspace{4pt}

**7.a) Speedup máximo (infinitos cores)**

$$\lim_{P \to \infty} Speedup(P) = \frac{1}{S} = \frac{1}{0.25} = \mathbf{4\times}$$

**Criterio:** Resultado correcto = 4x. Debe mostrar que viene de 1/S. 0.5 pts.

\vspace{4pt}

**7.b) Speedup con P=4 y P=8**

$$Speedup(4) = \frac{1}{0.25 + \frac{0.75}{4}} = \frac{1}{0.25 + 0.1875} = \frac{1}{0.4375} = \mathbf{2.29\times}$$

$$Speedup(8) = \frac{1}{0.25 + \frac{0.75}{8}} = \frac{1}{0.25 + 0.09375} = \frac{1}{0.34375} = \mathbf{2.91\times}$$

**Criterio:** Ambos cálculos correctos (se acepta redondeo razonable). 0.5 pts.

\vspace{4pt}

**7.c) ¿Vale la pena pasar de 8 a 64 cores?**

$$Speedup(64) = \frac{1}{0.25 + \frac{0.75}{64}} = \frac{1}{0.25 + 0.01172} = \frac{1}{0.26172} = \mathbf{3.82\times}$$

Pasar de 8 a 64 cores (8x más hardware) solo mejora de 2.91x a 3.82x --- una ganancia marginal de 0.91x por 56 cores adicionales. **No vale la pena.** Ya estamos cerca del límite teórico (4x). Los rendimientos son fuertemente decrecientes. Sería mejor invertir en reducir la fracción secuencial (S).

**Criterio:** Cálculo correcto de Speedup(64) + conclusión justificada de que no vale la pena (rendimientos decrecientes, cercanía al límite). 0.5 pts.

---

## PARTE B — Diseño y análisis (5 pts)

### 8. (5 pts) Chatbot con LLM remoto

Cada petición: recv(1ms) → BD(50ms) → API(1500ms) → send(5ms). Total = 1556ms.

\vspace{4pt}

**8.a) 200 usuarios en modo secuencial**

$$T_{sec} = 200 \times (1 + 50 + 1500 + 5) = 200 \times 1556 = \mathbf{311{,}200\text{ms} \approx 311\text{s} \approx 5.2\text{ min}}$$

**Criterio:** Cálculo correcto. 1 pt.

\vspace{4pt}

**8.b) ¿CPU-bound o I/O-bound?**

**I/O-bound.** Desglose:

- exec = recv(1ms) + send(5ms) = 6ms
- wait = BD(50ms) + API(1500ms) = 1550ms
- Fracción de espera: $1550/1556 \approx 99.6\%$

La CPU está ociosa el 99.6% del tiempo, esperando respuestas de red.

**Criterio:** Identificar I/O-bound con cálculo de la fracción wait/exec. 1 pt.

\vspace{4pt}

**8.c) ¿Qué paradigma? ¿Cuánto tardan 200 usuarios?**

**M4 --- Concurrente + Asíncrono (asyncio).**

Justificación formal:

- Carga I/O-bound: $wait(\tau_i) \neq \emptyset$ y $wait \gg exec$
- Un solo hilo con event loop puede solapar las esperas: mientras U1 espera API (1500ms), el event loop atiende las otras 199 peticiones
- No necesitamos múltiples cores porque la CPU solo trabaja 6ms por petición
- Formalmente: $\exists\ i \neq j: exec(\tau_j) \cap wait(\tau_i) \neq \emptyset$

**Tiempo aproximado:**

Con asyncio, las peticiones se lanzan casi simultáneamente. Las esperas se solapan. El exec total serializado es $200 \times 6\text{ms} = 1200\text{ms}$. El wait más largo es ~1556ms (primera petición completa).

$$T_{async} \approx 1556\text{ms} + 200 \times 6\text{ms} \approx 2{,}756\text{ms} \approx \mathbf{2.8\text{s}}$$

Speedup vs secuencial: $311s / 2.8s \approx 111\times$.

**Criterio:** Elegir M4/asyncio (1 pt). Justificar con I/O-bound (0.5 pts). Cálculo aproximado razonable del tiempo (0.5 pts). Se acepta cualquier estimación en el rango 1.5--3s.

\vspace{4pt}

**8.d) LLM local: inferencia\_CPU(2000ms)**

**No**, M4 ya no funciona para la inferencia. Ahora `inferencia_CPU(2000ms)` es **exec** (CPU-bound, $wait = \emptyset$), no wait. El event loop de asyncio se **bloquea** durante 2000ms de cómputo puro --- no puede atender a nadie más.

**Solución: M5b --- Paralelo + Asíncrono.**

- recv, BD, send → asyncio (event loop, un hilo) --- sigue siendo I/O
- inferencia\_CPU → `run_in_executor(ProcessPoolExecutor(4))` --- 4 workers en cores separados, cada uno con su propio GIL

Con 4 cores: throughput $\approx 4 / 2000\text{ms} = 2$ peticiones/segundo.
Para 200 usuarios: $\approx 200/2 = 100\text{s}$.

**Criterio:** Identificar que M4 falla porque la inferencia es exec, no wait (0.5 pts). Proponer M5b con ProcessPoolExecutor (0.5 pts). Explicar por qué se necesitan procesos y no hilos (GIL) es un plus.