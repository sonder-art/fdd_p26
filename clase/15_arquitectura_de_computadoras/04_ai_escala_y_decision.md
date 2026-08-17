---
title: "IA, escala y selección de hardware"
---

Un modelo de IA convierte parámetros y entradas en resultados. El hardware aloja su estado, lo mueve y ejecuta operaciones con objetivos de latencia, throughput, energía y costo. **Los parámetros inician el presupuesto, no lo completan.**

## Inferencia y entrenamiento ocupan memoria distinta

![Comparación categórica: inferencia usa pesos, caché KV y temporales; entrenamiento añade activaciones, gradientes y estados del optimizador.](./images/memoria_ai.svg)

*Diagrama propio del curso, SVG accesible, 2026. Los bloques nombran componentes; sus tamaños no están a escala.*

**Lectura textual del diagrama:** inferencia necesita pesos, caché KV y temporales. Entrenamiento conserva además activaciones, gradientes y estados del optimizador. El runtime puede reservar buffers y memoria de comunicación.

En **inferencia**, los pesos se leen repetidamente. El *prefill* procesa el prompt; el *decode* produce tokens sucesivos y reutiliza claves y valores anteriores mediante la **caché KV**. Evita recalcular la historia, pero consume memoria.

La caché KV crece con las secuencias simultáneas, los tokens conservados y la arquitectura. Más contexto y batching pueden elevar throughput, pero dejan menos espacio para solicitudes concurrentes. El máximo de contexto no determina cuántas peticiones caben ni su latencia.

En **entrenamiento**, el forward pass crea activaciones; el backward pass obtiene gradientes; el optimizador actualiza parámetros. La recomputación ahorra activaciones a cambio de cálculo. Dividir estados ahorra memoria local a cambio de comunicación.

## La cuenta mínima de los pesos

Para parámetros almacenados con precisión uniforme, sea $N_p$ su cantidad y $b$ sus bits. B = $10^9$ y T = $10^{12}$.

$$M_{pesos}=N_p\times\frac{b}{8}$$

**DERIVED (GB decimales, sólo pesos):**

- **7B:** BF16 = $7\times10^9\times2$ bytes = **14 GB**; INT8 = **7 GB**; INT4 = **3.5 GB**.
- **70B:** BF16 = **140 GB**; INT8 = **70 GB**; INT4 = **35 GB**.
- **1T:** BF16 = **2 TB**; INT8 = **1 TB**; INT4 = **0.5 TB**.

Son capacidades lógicas. Archivos, runtimes y fabricantes pueden reportar GB decimales o GiB binarios; además aparecen escalas, metadatos, padding y buffers. Repartir 140 GB entre cuatro GPU tampoco garantiza 35 GB exactos por GPU: depende del particionado.

**DERIVED (piso didáctico de entrenamiento):** mixed precision con Adam clásico puede presupuestarse como **~18 bytes por parámetro**: 2 bytes de pesos BF16/FP16 + 4 de copia maestra FP32 + 4 de gradiente FP32 + 8 de dos estados Adam FP32. Así, 7B, 70B y 1T requieren aproximadamente **126 GB**, **1.26 TB** y **18 TB**, respectivamente, antes de activaciones y temporales.

Ese piso no es universal. Optimizador, precisión, sharding e implementación cambian la cifra. Activaciones, comunicación y picos temporales pueden decidir el máximo real.

## Cuantizar cambia más que capacidad

Cuantizar pesos reduce bytes y tráfico, pero implica escalas y riesgo numérico. INT4 no garantiza duplicar la velocidad de INT8: requiere kernels y hardware compatibles, y otro recurso puede limitar.

La cuantización de pesos no reduce automáticamente la caché KV ni todas las activaciones. Valida modelo, precisión, contexto, lote y calidad en el mismo hardware.

## Distribuir crea una segunda carga

Un acelerador evita comunicación remota, pero queda limitado por memoria y throughput locales. Al distribuir aparecen varias estrategias:

- **Paralelismo de datos:** en entrenamiento, replica el modelo, divide batches y sincroniza gradientes; en inferencia, réplicas independientes pueden atender solicitudes distintas.
- **Paralelismo de modelo o tensor:** divide parámetros u operaciones de una capa. Aloja modelos mayores, pero intercambia activaciones o resultados parciales.
- **Paralelismo de pipeline:** coloca grupos de capas en dispositivos distintos. Reduce estado local, pero agrega transferencias y burbujas de espera.

La red se vuelve parte del computador. Bandwidth, latencia y topología entre chips, servidores y racks determinan si más aceleradores terminan más trabajo. **Más dispositivos no prometen speedup lineal.**

## Del chip al centro de datos

![Escala de decisión: primero medir si limita memoria, cómputo o red; después pasar de equipo a servidor y cluster, aceptando más coordinación.](./images/escala_decision.svg)

*Diagrama propio del curso, SVG accesible, 2026.*

**Lectura textual del diagrama:** la decisión inicia midiendo memoria, cómputo y comunicación. Sólo después se escala de equipo a servidor y cluster. Cada salto añade capacidad, pero también coordinación, fallas posibles, energía y operación.

La cadena física es **chip → board → servidor → rack → cluster → centro de datos**. La board conecta chips y memoria; el servidor añade CPU, RAM, almacenamiento y red; el rack agrega switches, potencia y refrigeración; el centro de datos aporta electricidad, enfriamiento y enlaces.

<img src="./images/real_tsubame4_node.webp" alt="Interior de un nodo de TSUBAME 4.0 con cuatro GPU NVIDIA H100, tuberías de refrigeración y módulos de memoria." loading="lazy">

**FACT (objeto fotografiado, no ejemplo GB300):** nodo de TSUBAME 4.0 con cuatro GPU NVIDIA H100. Ilustra el nivel servidor multi-GPU; no muestra Blackwell Ultra ni un rack GB300. Foto de [Fukumoto en Wikimedia Commons](https://commons.wikimedia.org/wiki/File:TSUBAME4.0_P5160984.jpg), [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0); redimensionada y convertida a WebP para el curso.

## Cuatro ejemplos representativos, no un ranking

<img src="./images/real_macbook_m5.webp" alt="MacBook Pro de 14 pulgadas con chip M5, abierto sobre una mesa; la foto muestra el equipo M5, no las especificaciones del M5 Max." loading="lazy">

**FACT (objeto fotografiado):** MacBook Pro de 14 pulgadas con M5; no es el M5 Max de las especificaciones siguientes. Foto de [AzureSaturn en Wikimedia Commons](https://commons.wikimedia.org/wiki/File:MacBook_Pro_(14-inch,_M5,_Space_Black).jpg), [CC0 1.0](http://creativecommons.org/publicdomain/zero/1.0/deed.en); redimensionada y convertida a WebP para el curso.

- **FACT (límite oficial de producto):** Apple M5 Max admite hasta **128 GB de memoria unificada** y hasta **614 GB/s**. Favorece trabajo local que valora capacidad compartida y evita una copia obligatoria RAM↔VRAM en ciertos flujos. Esos máximos no son benchmark ni TDP.
- **FACT (especificación de referencia):** GeForce RTX 5090 tiene **32 GB GDDR7**, **1,792 GB/s** y **575 W TGP**. Favorece un ecosistema GPU de escritorio, pero el modelo debe compartir 32 GB con cachés y temporales; tarjetas de ensambladores pueden variar.
- **FACT (por chip, picos oficiales):** TPU7x Ironwood ofrece **192 GiB HBM**, **7,380 GB/s**, **2,307 TFLOPS BF16** y **4,614 TFLOPS FP8**; un pod llega a **9,216 chips**. Los picos cambian con precisión y no son desempeño observado.
- **FACT (sistema oficial, máximos agregados):** DGX GB300 integra **72 GPU Blackwell Ultra**, **36 CPU Grace**, **20 TB de memoria GPU**, hasta **576 TB/s** HBM y **130 TB/s NVLink**. El rack usa refrigeración líquida y admite hasta **142 kW**; es capacidad máxima, no consumo medido.

M5 Max, RTX 5090, TPU7x y GB300 cubren escalas distintas. Compararlos sin aplicación, precisión, disponibilidad y medición de extremo a extremo produce una falsa clasificación.

## Guía de decisión

1. **Define la carga:** inferencia o entrenamiento, modelo, precisión aceptable, contexto, concurrencia, latencia objetivo y volumen diario.
2. **Presupuesta memoria:** pesos más caché KV o activaciones, gradientes, optimizador, temporales y margen del runtime.
3. **Mide un perfil pequeño:** utilización, memoria máxima, bytes movidos, latencia, throughput, potencia de pared y calidad.
4. **Ataca el límite:** más capacidad para OOM; mejor localidad o bandwidth para espera de datos; más compute para unidades saturadas; mejor interconexión para comunicación dominante.
5. **Escala sólo el tramo útil:** batching para throughput, cuantización validada para huella y cluster sólo cuando capacidad o servicio lo exige.
6. **Incluye operación:** compatibilidad del software, disponibilidad, confiabilidad, seguridad, costo total y energía. Comprar hardware sin ese stack compra una posibilidad, no un resultado.

## Repaso conceptual

1. ¿Por qué conocer sólo el tamaño de los pesos no basta para decidir si una inferencia cabe?
2. ¿Cómo cambian contexto y batching la memoria y los objetivos de servicio?
3. ¿Qué omite el piso didáctico de 18 bytes por parámetro?
4. ¿Cuándo cuantizar puede ahorrar memoria sin reducir proporcionalmente la latencia?
5. ¿Por qué el paralelismo de datos y el de modelo generan comunicación distinta?
6. ¿Qué evidencia justificaría pasar de un servidor a un cluster?

## Escenarios de decisión

### Escenario 1 — Asistente local

Un modelo 70B cuantizado a INT4 debe correr sin red y responder a una persona. **DERIVED:** los pesos ocupan 35 GB antes de caché KV y temporales. ¿Elegirías los **32 GB FACT** de VRAM dedicada, hasta **128 GB FACT** unificados o un modelo menor? Justifica capacidad, contexto, software y latencia.

### Escenario 2 — API concurrente

Un modelo cabe en una GPU, pero al subir concurrencia aparecen OOM y peor tiempo por token. ¿Reducirías contexto, limitarías batching, cuantizarías la caché, añadirías réplicas o dividirías el modelo? Propón primero dos mediciones que separen memoria, compute y comunicación.

### Escenario 3 — Entrenamiento distribuido

Un entrenamiento escala bien dentro de un servidor y casi no mejora al cruzar racks. Las GPU esperan durante sincronización. ¿Comprarías más GPU, cambiarías el particionado o mejorarías red y colocación? Explica qué tráfico crea la estrategia actual y qué resultado confirmaría la intervención.

## Flashcards

- **Pesos:** parámetros aprendidos que la inferencia lee para transformar entradas.
- **Caché KV:** claves y valores de atención conservados para no recalcular el contexto previo.
- **Contexto:** tokens de entrada más historial y salida que el servicio debe mantener.
- **Batching:** agrupar trabajo para elevar utilización y throughput, usando más memoria y quizá latencia.
- **Cuantización:** representar tensores con menos bits, con requisitos de kernel y validación numérica.
- **Activaciones:** resultados intermedios; entrenamiento guarda parte para calcular gradientes.
- **Gradiente:** señal de cambio de cada parámetro durante backward.
- **Estado Adam:** momentos que el optimizador conserva además de pesos y gradientes.
- **Paralelismo de datos:** réplicas del modelo procesan batches distintos y sincronizan gradientes.
- **Paralelismo de modelo:** parámetros u operaciones se reparten entre dispositivos.
- **All-reduce:** operación colectiva que combina y distribuye valores, por ejemplo gradientes.
- **Regla final:** medir el cuello de botella antes de añadir escala.

## Fuentes

- [Hugging Face Transformers — GPU memory usage](https://huggingface.co/docs/transformers/model_memory_anatomy): pesos mixed precision, gradientes, estados Adam, activaciones y temporales.
- [NVIDIA NIM — Troubleshooting GPU Memory OOM](https://docs.nvidia.com/nim/large-language-models/latest/troubleshooting/memory.html): fórmula de pesos, KV cache, contexto y overhead de inferencia.
- [NVIDIA Megatron Bridge — Parallelisms Guide](https://docs.nvidia.com/nemo/megatron-bridge/latest/parallelisms.html): paralelismo de datos/modelo y comunicación colectiva.
- [Apple Newsroom — MacBook Pro con M5 Pro y M5 Max](https://www.apple.com/newsroom/2026/03/apple-introduces-macbook-pro-with-all-new-m5-pro-and-m5-max/): memoria unificada y bandwidth del M5 Max.
- [NVIDIA — GeForce RTX 5090](https://www.nvidia.com/en-us/geforce/graphics-cards/50-series/rtx-5090/): capacidad y TGP; [arquitectura RTX Blackwell](https://images.nvidia.com/aem-dam/Solutions/geforce/blackwell/nvidia-rtx-blackwell-gpu-architecture.pdf): bandwidth.
- [Google Cloud — TPU7x Ironwood](https://docs.cloud.google.com/tpu/docs/tpu7x): HBM, picos por precisión, interconexión y tamaño de pod.
- [NVIDIA — DGX GB300](https://www.nvidia.com/en-us/data-center/dgx-gb300/): composición, memoria y bandwidth; [NVL72 System Components](https://docs.nvidia.com/enterprise-reference-architectures/nvl72-ai-factory/latest/components.html): NVLink, refrigeración y potencia máxima.
- [Wikimedia Commons — MacBook Pro M5](https://commons.wikimedia.org/wiki/File:MacBook_Pro_(14-inch,_M5,_Space_Black).jpg): AzureSaturn, CC0 1.0; [TSUBAME 4.0](https://commons.wikimedia.org/wiki/File:TSUBAME4.0_P5160984.jpg): Fukumoto, CC BY-SA 4.0.
