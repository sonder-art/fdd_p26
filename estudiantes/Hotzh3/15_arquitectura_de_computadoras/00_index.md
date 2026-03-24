---
title: "Módulo 15: Arquitectura de Computadoras"
---

# Módulo 15: Arquitectura de Computadoras

Entrenar un modelo de lenguaje moderno puede costar cien millones de dólares. Un chip H100 ejecuta casi cuatro mil billones de operaciones por segundo. La diferencia entre correr código en CPU o GPU puede ser de cien veces. ¿Por qué? ¿Cuándo importa?

Este módulo explica la arquitectura de la computadora desde la perspectiva de quien trabaja con datos y modelos: qué hay dentro de la máquina, cómo se mueve la información, por qué algunos cómputos son baratos y otros son prohibitivos, y qué significa "cuello de botella" en términos concretos de hardware.

No es un curso de sistemas. No vas a escribir drivers ni compiladores. Pero sí vas a entender por qué tu código de NumPy es cien veces más rápido que un loop de Python, por qué `.to("cuda")` existe, y cómo se relaciona el número de parámetros de un LLM con millones de dólares en cómputo.

## Contenido

| Sección | Tema | Tiempo |
|---------|------|--------|
| [La máquina](./01_la_maquina.md) | Von Neumann, jerarquía de memoria, CPU y GPU en el sistema | ~15 min |
| [Los procesadores](./02_procesadores.md) | CPU vs GPU vs NPU, ARM vs x86, cores y reloj, ensamblador | ~15 min |
| [Rendimiento y escala](./03_rendimiento_y_escala.md) | FLOPs, cuellos de botella de memoria, vectorización, LLMs | ~20 min |

## Notebook

| Notebook | Tema | Tiempo |
|----------|------|--------|
| [Hardware y escala](./code/01_arquitectura.ipynb) | Inspección de hardware, benchmark de vectorización, efectos de caché, escala de LLMs | ~25 min |

[![Open in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/sonder-art/fdd_p26/blob/main/clase/15_arquitectura_de_computadoras/code/01_arquitectura.ipynb)

## Prerequisitos

- Módulo 9: Python completado
- `pip install -r requirements.txt`

## Idea central del módulo

El hardware no es magia ni detalle de implementación: es el contrato físico que determina qué operaciones son rápidas, qué operaciones son lentas y por qué ciertos algoritmos escalan y otros no.

Tres principios que guían el módulo:

1. **La velocidad y el tamaño siempre se oponen.** Los registros son instantáneos pero caben en tu puño; los discos duros guardan terabytes pero son miles de veces más lentos. Todo el diseño de software eficiente vive dentro de esa tensión.

2. **CPU y GPU no hacen lo mismo rápido.** No es que uno sea mejor que el otro: tienen filosofías de diseño opuestas. Entender cuál usar es tan importante como saber programar.

3. **La escala de la IA moderna es literalmente imposible de intuir sin números.** Los gráficos de este módulo existen para hacer concreta una magnitud que el lenguaje informal no puede transmitir.
