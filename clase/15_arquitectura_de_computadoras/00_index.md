---
title: "Módulo 15: Arquitectura y hardware de computadoras"
---

Un programa no trabaja en el vacío. **Calcula**, **guarda** y **mueve datos** sobre una máquina física. El desempeño aparece cuando esas tres acciones encajan; el cuello de botella aparece cuando una de ellas no alcanza a las otras.

<img class="hardware-lead-visual" src="./images/hero_compute_city.webp" alt="Ciudad retrofuturista vista desde arriba: una torre central de cómputo conectada por rutas luminosas a distritos de memoria y almacenamiento." loading="eager" decoding="async">

*Creación original generativa para este curso, producida con OpenAI, 2026.*

**Lectura textual de la imagen:** el núcleo de cómputo no está aislado. Depende de capas de memoria, almacenamiento y rutas capaces de llevarle datos.

Esta unidad construye un mapa para leer una laptop, una GPU o un centro de datos según cuatro dimensiones: ubicación de los datos, unidad que los transforma, costo de moverlos y recurso que se satura primero.

## Al terminar

Podrás explicar por qué un programa compatible necesita la ISA correcta; distinguir reloj, ciclos, latencia y throughput; razonar sobre RAM, VRAM, caché y almacenamiento; y elegir una dirección de optimización a partir de mediciones, no de slogans.

## Ruta en dos sesiones

**ESTIMATE (diseño docente):** la ruta requiere 125 minutos netos en dos sesiones nominales de 90. Los escenarios se trabajan en grupos pequeños y en paralelo; las flashcards quedan para después de clase.

### Sesión 1 — De la máquina al movimiento

1. **Orientación** — este mapa de la unidad (~5 min).
2. [**Compute, instrucciones y CPU**](./01_compute_instrucciones_cpu.md) — piezas físicas, ISA, reloj, ciclos, cores, threads y SIMD (~20 min).
3. [**Memoria y movimiento de datos**](./02_memoria_y_datos.md) — jerarquía, latencia, ancho de banda y rutas CPU↔GPU (~25 min).

### Sesión 2 — Del paralelismo a la decisión

1. [**Paralelismo, performance y energía**](./03_paralelismo_performance_energia.md) — CPU, GPU, aceleradores, Roofline y potencia (~43 min).
2. [**IA, escala y selección de hardware**](./04_ai_escala_y_decision.md) — memoria de modelos, comunicación, selección y repaso final (~32 min).

## Siete modelos mentales

1. **La computadora es un sistema de especialistas.** CPU, memoria, almacenamiento, red y aceleradores colaboran mediante interconexiones.
2. **La ISA es un contrato.** Define qué instrucciones entiende un procesador; no es lo mismo que el lenguaje en el que escribiste el programa.
3. **El reloj asigna pasos, no garantiza trabajo útil.** Los ciclos pueden ocuparse en cálculo, espera o coordinación.
4. **La proximidad de los datos tiene precio.** Cerca del cómputo suele significar menor latencia, pero menor capacidad y mayor costo por byte.
5. **El paralelismo tiene forma.** Pocos flujos complejos y muchos flujos regulares necesitan arquitecturas distintas.
6. **El cuello de botella decide la métrica.** Más FLOPS no ayuda si faltan memoria, ancho de banda o comunicación.
7. **Escalar amplifica movimiento y energía.** Chip, servidor, rack y centro de datos son niveles del mismo sistema.

## Cómo leer las cifras

- **FACT**: dato reportado directamente por una fuente identificada.
- **DERIVED**: resultado reproducible a partir de datos o una fórmula mostrada.
- **ESTIMATE**: supuesto o escenario útil, no una medición.

Estas etiquetas importan: una especificación máxima, una derivación y una observación real no responden la misma pregunta.
