# Módulo 8: Contenedores

En el módulo anterior instalaste Docker y Podman. Ahora vamos a entender **qué son los contenedores**, **por qué existen** y **cómo usarlos** en la práctica.

## Prerequisitos

Antes de continuar, verifica que completaste la tarea 7.0 (instalación de Docker y Podman). Si no la hiciste, regresa y complétala — todo este módulo asume que ya tienes ambas herramientas instaladas.

:::exercise{title="Verificación de instalación" difficulty="1"}

Ejecuta los siguientes comandos y confirma que obtienes una versión válida:

```bash
docker --version
# Docker version 2X.X.X, build XXXXXXX

podman --version
# podman version 4.X.X o 5.X.X
```

Ahora ejecuta el contenedor de prueba en ambos:

```bash
docker run hello-world
podman run hello-world
```

Si ambos imprimen el mensaje "Hello from Docker!" (o equivalente en Podman), estás listo.

Si algo falla, usa el siguiente prompt para diagnosticar:

:::

:::prompt{title="Diagnosticar instalación de Docker/Podman" for="ChatGPT/Claude"}

Estoy en un curso de ciencia de datos. Necesito tener Docker y Podman instalados.

Mi sistema operativo es: [Windows/macOS/Linux]

Al ejecutar:

```
[pega el comando que falló]
```

Obtuve este error:

```
[pega el error aquí]
```

¿Cómo lo soluciono?

:::

## Contenido del módulo

Este módulo tiene cuatro secciones:

| # | Sección | Descripción |
|---|---------|-------------|
| 1 | [¿Qué son los contenedores?](./01_que_son_contenedores.md) | El concepto, analogías, VMs vs contenedores, namespaces y cgroups |
| 2 | [Docker](./02_docker.md) | Arquitectura, Dockerfile, imágenes, contenedores, comandos esenciales |
| 3 | [Podman](./03_podman.md) | Diferencias con Docker, rootless, daemonless, pods |
| 4 | [Benchmarks](./04_benchmarks.md) | Experimentos de rendimiento: startup, memoria, CPU, I/O, escalamiento |

## ¿Por qué contenedores?

Si trabajas en ciencia de datos o ingeniería de software, eventualmente vas a escuchar:

> "En mi máquina sí funciona"

Los contenedores resuelven exactamente ese problema. Empaquetan tu código **junto con todas sus dependencias** en una unidad portable que funciona igual en cualquier máquina.

Pero más allá de eso, los contenedores son la base de:

- **Ambientes reproducibles** — tu análisis corre igual hoy que en 6 meses
- **Despliegue en la nube** — AWS, GCP, Azure, todos usan contenedores
- **Pipelines de datos** — Airflow, Prefect, Dagster ejecutan tareas en contenedores
- **Machine Learning** — entrenamiento y serving de modelos en contenedores

En este módulo no solo vas a aprender a **usar** contenedores, sino a **entender** cómo funcionan por dentro y a **medir** su rendimiento con experimentos reales.
