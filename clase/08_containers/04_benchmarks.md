# Benchmarks: midiendo el rendimiento de contenedores

Los contenedores prometen ser "casi nativos" en rendimiento. Pero ¿qué tan cerca están? ¿Docker y Podman rinden igual? En esta sección vamos a **medir**, no asumir.

Vamos a correr nueve experimentos que miden diferentes aspectos del rendimiento:

| # | Experimento | ¿Qué mide? |
|---|------------|-------------|
| 1 | Startup latency | Tiempo para arrancar un contenedor |
| 2 | Memory consumption | Memoria que consume cada contenedor |
| 3 | CPU under load | Rendimiento de CPU en contenedores vs bare metal |
| 4 | Disk I/O | Velocidad de escritura: overlay vs volumen vs bare metal |
| 5 | Nested containers | Contenedores dentro de contenedores |
| 6 | Scaling | Comportamiento al escalar a muchos contenedores |
| 7 | CPU puro (exec) | CPU sin overhead de startup, vía `docker exec` |
| 8 | Memoria cgroup | Memoria por contenedor vía cgroup (exacta) |
| 9 | Nested v2 | 6 enfoques diferentes para contenedores anidados |

> **Importante**: Los resultados varían según tu hardware, SO y versiones de Docker/Podman. Lo valioso no son los números exactos sino las **tendencias** y **proporciones**.

## Scripts de benchmark

Todos los scripts están en el directorio `scripts/` de este capítulo. Puedes correrlos individualmente o todos juntos:

```bash
# Correr todos los benchmarks
cd clase/08_containers/scripts
bash run_all.sh

# O correr uno específico
bash bench_startup.sh
bash bench_memory.sh
bash bench_cpu.sh
bash bench_io.sh
bash bench_nested.sh
bash bench_scale.sh
bash bench_cpu_exec.sh
bash bench_memory_cgroup.sh
bash bench_nested_v2.sh

# Generar gráficas (requiere matplotlib)
pip install -r requirements.txt
python3 analyze.py
```

Los resultados (CSVs y gráficas PNG) se guardan en `scripts/results/`.

---

## Experimento 1: Startup latency

**Objetivo**: ¿Cuánto tarda un contenedor en arrancar y ejecutar un comando simple comparado con ejecutarlo directamente?

### ¿Qué medimos?

El tiempo de ejecutar `echo ok` en tres contextos:
- **Bare metal**: directamente en tu shell
- **Docker**: `docker run --rm ubuntu echo ok`
- **Podman**: `podman run --rm ubuntu echo ok`

### El script

```bash
#!/bin/bash
# bench_startup.sh - Mide latencia de arranque
set -e

REPS=${1:-10}  # repeticiones (default: 10)
OUTFILE="results/startup.csv"
mkdir -p results

echo "runtime,metric,value" > "$OUTFILE"

echo "=== Startup Latency ($REPS repeticiones) ==="

# Bare metal
for i in $(seq 1 "$REPS"); do
    t=$( { time echo ok > /dev/null; } 2>&1 | grep real | awk '{print $2}' )
    ms=$(echo "$t" | sed 's/0m//;s/s//' | awk '{printf "%.1f", $1 * 1000}')
    echo "bare,$i,$ms" >> "$OUTFILE"  # NOTA: el script real usa formato runtime,metric,value
done

# Docker
if command -v docker &>/dev/null; then
    docker pull -q ubuntu > /dev/null 2>&1
    for i in $(seq 1 "$REPS"); do
        ms=$( { time docker run --rm ubuntu echo ok > /dev/null; } 2>&1 | \
              grep real | awk '{print $2}' | sed 's/0m//;s/s//' | \
              awk '{printf "%.1f", $1 * 1000}')
        echo "docker,startup_ms,$ms" >> "$OUTFILE"
    done
fi

# Podman
if command -v podman &>/dev/null; then
    podman pull -q ubuntu > /dev/null 2>&1
    for i in $(seq 1 "$REPS"); do
        ms=$( { time podman run --rm ubuntu echo ok > /dev/null; } 2>&1 | \
              grep real | awk '{print $2}' | sed 's/0m//;s/s//' | \
              awk '{printf "%.1f", $1 * 1000}')
        echo "podman,startup_ms,$ms" >> "$OUTFILE"
    done
fi

echo "Resultados en $OUTFILE"
```

### Resultados de referencia

Estos resultados se obtuvieron en nuestra máquina de prueba (Docker 28.4.0, Podman 4.6.2, Linux 6.12). Se hicieron 10 repeticiones por runtime con un warm-up run previo.

**Datos crudos (10 repeticiones, en milisegundos):**

| Rep | Bare Metal | Docker | Podman |
|-----|-----------|--------|--------|
| 1 | 1.4 | 313.9 | 152.8 |
| 2 | 1.4 | 299.8 | 240.8 |
| 3 | 1.2 | 305.1 | 165.1 |
| 4 | 1.4 | 310.0 | 207.4 |
| 5 | 1.1 | 312.9 | 207.5 |
| 6 | 1.1 | 302.3 | 168.2 |
| 7 | 1.8 | 299.8 | 164.9 |
| 8 | 1.2 | 324.1 | 154.6 |
| 9 | 1.2 | 308.5 | 160.5 |
| 10 | 1.3 | 301.5 | 158.5 |

**Promedios y multiplicadores:**

| Runtime | Promedio | Rango | vs Bare Metal |
|---------|---------|-------|---------------|
| Bare Metal | **1.3 ms** | 1.1 - 1.8 ms | — |
| Docker | **307.8 ms** | 299.8 - 324.1 ms | **237x más lento** |
| Podman | **178.0 ms** | 152.8 - 240.8 ms | **137x más lento** |

Docker vs Podman: Podman fue **1.7x más rápido** que Docker.

**Análisis**: El overhead de arranque no viene de ejecutar el comando, sino de crear namespaces, configurar cgroups, montar el overlay filesystem y arrancar el proceso.

Dato sorprendente: **Podman fue más rápido que Docker** en startup. ¿Por qué? Docker usa una arquitectura cliente → daemon → containerd → runc, donde cada paso es una llamada IPC. Podman usa fork-exec directo — menos intermediarios, menos overhead. El daemon "pre-calentado" de Docker no compensa el costo de la comunicación API.

**Sobre la varianza de Podman**: Las repeticiones 2 (240.8 ms) y 4-5 (~207 ms) son outliers — probablemente arranques en frío del caché de `fuse-overlayfs`. El estado estable de Podman está más cerca de ~160 ms (repeticiones 6-10). Docker es más consistente (~300 ms, desviación de ~8 ms) porque el daemon centralizado mantiene caché caliente pero paga el costo fijo de la comunicación API.

> **Nota**: Tus resultados van a variar según tu hardware. Lo que importa es la **proporción**, no los números exactos.

![Comparación de startup latency entre bare metal, Docker y Podman](./images/startup_comparison.png)

:::exercise{title="Medir startup latency" difficulty="1"}

1. Ejecuta el benchmark:

```bash
cd scripts
bash bench_startup.sh 20
```

2. Revisa los resultados:

```bash
cat results/startup.csv
```

3. Calcula el promedio de cada runtime. ¿Cuántas veces más lento es Docker que bare metal? ¿Y Podman? ¿Cuál de los dos runtimes fue más rápido?

4. Ejecuta una segunda ronda. ¿Los tiempos cambian entre la primera y segunda ejecución? ¿Por qué podría ser? (Pista: caché del sistema operativo)

:::

---

## Experimento 2: Memory consumption

**Objetivo**: ¿Cuánta memoria consume un contenedor idle? ¿Cuánto agrega el daemon de Docker?

### ¿Qué medimos?

1. Memoria base del sistema (sin contenedores)
2. Memoria con 5 contenedores idle en Docker
3. Memoria con 5 contenedores idle en Podman
4. Overhead del daemon de Docker

### El script

{% raw %}
```bash
#!/bin/bash
# bench_memory.sh - Mide consumo de memoria
set -e

OUTFILE="results/memory.csv"
mkdir -p results

echo "runtime,metric,value" > "$OUTFILE"

get_used_mb() {
    free -m | awk '/^Mem:/ {print $3}'
}

echo "=== Memory Consumption ==="

# Baseline
baseline=$(get_used_mb)
echo "baseline,used_mb,$baseline" >> "$OUTFILE"
echo "Memoria base: ${baseline} MB"

# Docker: lanzar 5 contenedores idle
if command -v docker &>/dev/null; then
    for i in $(seq 1 5); do
        docker run -d --name "mem_docker_$i" ubuntu sleep 3600 > /dev/null
    done
    sleep 3
    docker_mem=$(get_used_mb)
    docker_overhead=$((docker_mem - baseline))
    echo "docker,5_containers_mb,$docker_mem" >> "$OUTFILE"
    echo "docker,overhead_mb,$docker_overhead" >> "$OUTFILE"

    # Docker stats
    docker stats --no-stream --format "{{.Name}},{{.MemUsage}}" | while read line; do
        echo "docker,container_stats,$line" >> "$OUTFILE"
    done

    # Cleanup
    for i in $(seq 1 5); do
        docker stop "mem_docker_$i" > /dev/null 2>&1
        docker rm "mem_docker_$i" > /dev/null 2>&1
    done
    sleep 2
    echo "Docker: ${docker_mem} MB (overhead: ${docker_overhead} MB)"
fi

# Podman: lanzar 5 contenedores idle
if command -v podman &>/dev/null; then
    for i in $(seq 1 5); do
        podman run -d --name "mem_podman_$i" ubuntu sleep 3600 > /dev/null
    done
    sleep 3
    podman_mem=$(get_used_mb)
    podman_overhead=$((podman_mem - baseline))
    echo "podman,5_containers_mb,$podman_mem" >> "$OUTFILE"
    echo "podman,overhead_mb,$podman_overhead" >> "$OUTFILE"

    # Cleanup
    for i in $(seq 1 5); do
        podman stop "mem_podman_$i" > /dev/null 2>&1
        podman rm "mem_podman_$i" > /dev/null 2>&1
    done
    echo "Podman: ${podman_mem} MB (overhead: ${podman_overhead} MB)"
fi

echo "Resultados en $OUTFILE"
```
{% endraw %}

### Resultados de referencia

Memoria base del sistema: **9,924 MB** usados. El script lanza 1, 5, 10, 20 contenedores idle (`sleep 3600`) y mide el delta de `free -m` antes y después.

**Datos crudos (delta en MB vs baseline previa a cada batch):**

| Contenedores | Docker (overhead) | Podman (overhead) |
|-------------|-------------------|-------------------|
| 1 | **-41 MB** | +39 MB |
| 5 | +71 MB | **-143 MB** |
| 10 | +11 MB | +33 MB |
| 20 | +73 MB | +61 MB |

**¿Por qué hay números negativos?** Este es el resultado más interesante del experimento. El script mide `free -m` antes y después de lanzar contenedores. Entre esas dos mediciones (que incluyen arrancar contenedores, esperar 3 segundos, y la limpieza del batch anterior), el sistema operativo está **constantemente** reciclando page cache, buffer cache y slab memory en segundo plano.

- **Docker -41 MB** (1 contenedor): El OS liberó ~45 MB de caché entre mediciones, enmascarando los ~4 MB que el contenedor realmente usó. El delta real fue probablemente: +4 MB (contenedor) - 45 MB (caché liberado) = -41 MB.
- **Podman -143 MB** (5 contenedores): El OS liberó ~160 MB de caché (quizá la limpieza del batch de Docker anterior disparó una cascada de liberación de páginas), enmascarando los ~15-20 MB que los 5 contenedores usaron.

**¿Cuánta memoria usa realmente un contenedor idle?** No podemos saberlo con `free -m` porque el ruido del sistema (~50-150 MB de fluctuación) es mayor que la señal (~3-5 MB por contenedor). El único dato confiable es 20 contenedores, donde el delta es lo suficientemente grande para dominar el ruido:
- Docker 20 contenedores: +73 MB → ~3.7 MB/contenedor
- Podman 20 contenedores: +61 MB → ~3.1 MB/contenedor

> **Lección importante de benchmarking**: Cuando tu señal es más pequeña que tu ruido, necesitas un instrumento más preciso. Para medir memoria por contenedor necesitarías `cgroup memory.current` (lee directamente cuánta memoria asignó el kernel a cada cgroup del contenedor), no `free -m` del sistema completo.

Lo que sí podemos observar en la tendencia (especialmente en el experimento de escalamiento más adelante con 50 contenedores): Docker tiende a usar más memoria total que Podman, en parte por el overhead constante del daemon (`dockerd` + `containerd`).

![Comparación de memoria por número de contenedores](./images/memory_comparison.png)

:::exercise{title="Medir memoria" difficulty="2"}

1. Antes de empezar, cierra aplicaciones pesadas para tener una medición más limpia.

2. Ejecuta:

```bash
bash bench_memory.sh
```

3. Revisa los resultados y responde:
   - ¿Cuánta memoria usó el daemon de Docker?
   - ¿Cuánta memoria agregó cada contenedor idle?
   - ¿Qué runtime tuvo menos overhead total?

:::

---

## Experimento 3: CPU under load

**Objetivo**: ¿Cuánto overhead de CPU agrega un contenedor? Si una tarea tarda X segundos en bare metal, ¿cuánto tarda en Docker y Podman?

### ¿Qué medimos?

Un loop de bash que cuenta hasta 10,000,000 — una tarea intensiva de CPU:

```bash
i=0; while [ $i -lt 10000000 ]; do i=$((i+1)); done
```

Lo ejecutamos en tres contextos: bare metal, Docker y Podman.

### El script

```bash
#!/bin/bash
# bench_cpu.sh - Mide overhead de CPU
set -e

OUTFILE="results/cpu.csv"
mkdir -p results

echo "runtime,metric,value" > "$OUTFILE"

CPU_CMD='i=0; while [ $i -lt 10000000 ]; do i=$((i+1)); done'

echo "=== CPU Benchmark ==="
echo "Contando hasta 10M en un loop de bash..."

# Bare metal
bare_time=$( { time bash -c "$CPU_CMD"; } 2>&1 | grep real | awk '{print $2}' | \
             sed 's/0m//;s/s//')
echo "bare,cpu_seconds,$bare_time" >> "$OUTFILE"
echo "Bare metal: ${bare_time}s"

# Docker
if command -v docker &>/dev/null; then
    docker_time=$( { time docker run --rm ubuntu bash -c "$CPU_CMD"; } 2>&1 | \
                   grep real | awk '{print $2}' | sed 's/0m//;s/s//')
    echo "docker,cpu_seconds,$docker_time" >> "$OUTFILE"
    echo "Docker: ${docker_time}s"
fi

# Podman
if command -v podman &>/dev/null; then
    podman_time=$( { time podman run --rm ubuntu bash -c "$CPU_CMD"; } 2>&1 | \
                   grep real | awk '{print $2}' | sed 's/0m//;s/s//')
    echo "podman,cpu_seconds,$podman_time" >> "$OUTFILE"
    echo "Podman: ${podman_time}s"
fi

echo "Resultados en $OUTFILE"
```

### Resultados de referencia

Se ejecutó el loop 3 veces por runtime.

**Datos crudos (segundos):**

| Rep | Bare Metal | Docker | Podman |
|-----|-----------|--------|--------|
| 1 | 46.21 | 50.81 | 57.89 |
| 2 | 48.10 | 52.18 | 55.85 |
| 3 | 46.87 | 55.52 | 55.91 |

**Promedios y overhead:**

| Runtime | Promedio | Delta vs Bare | Overhead % |
|---------|---------|---------------|------------|
| Bare Metal | **47.06s** | — | — |
| Docker | **52.84s** | +5.78s | **+12.3%** |
| Podman | **56.55s** | +9.49s | **+20.2%** |

**Análisis**: Los porcentajes de overhead parecen altos (12-20%), pero son engañosos. Nuestro benchmark mide **tiempo total** (`docker run` incluido), no solo CPU pura. Desglosemos los ~5.78 segundos extra de Docker:

| Componente | Tiempo estimado | Explicación |
|-----------|----------------|-------------|
| Startup del contenedor | ~0.3s | Crear namespaces, montar overlay (lo medimos en Exp 1) |
| Carga de bash | ~1-2s | El binario de bash de `ubuntu:22.04` puede ser diferente (versión, libs) al del host |
| Overlay filesystem I/O | ~3-4s | Cada acceso a archivo del intérprete bash pasa por la capa overlay |

**Docker rep 3 spike** (55.52s vs ~51s en reps 1-2): probablemente contención de CPU por procesos en segundo plano durante esa ejecución.

**Podman consistentemente ~4s más lento que Docker**: En modo rootless, Podman usa `fuse-overlayfs` (un filesystem en espacio de usuario) en lugar del overlay nativo del kernel. Cada lectura de archivo que hace el intérprete de bash pasa por una capa FUSE extra, lo que acumula overhead en un loop de 10 millones de iteraciones.

> **Conclusión práctica**: Para tareas de cómputo intensivo reales (entrenamiento de ML, procesamiento de datos), el overhead de CPU del contenedor es despreciable. Si tu modelo tarda 2 horas en entrenar, los 5-9 segundos extra del contenedor son el 0.07% del tiempo total.

![Comparación de CPU: tiempo para contar hasta 10M](./images/cpu_comparison.png)

:::exercise{title="Medir CPU" difficulty="2"}

1. Ejecuta:

```bash
bash bench_cpu.sh
```

2. Calcula el porcentaje de overhead: `(tiempo_contenedor - tiempo_bare) / tiempo_bare * 100`

3. ¿Es significativo el overhead de CPU? ¿Cuándo podría importar?

:::

---

## Experimento 4: Disk I/O

**Objetivo**: ¿Es más lento escribir a disco dentro de un contenedor? ¿Los volúmenes montados son más rápidos que el overlay filesystem?

### ¿Qué medimos?

Escribir 100 MB con `dd` en tres modos:
1. **Bare metal**: escritura directa al disco
2. **Overlay**: escritura dentro del contenedor (overlay filesystem)
3. **Volume**: escritura a un volumen montado del host

### El script

```bash
#!/bin/bash
# bench_io.sh - Mide rendimiento de I/O
set -e

OUTFILE="results/io.csv"
mkdir -p results

echo "runtime,metric,value" > "$OUTFILE"

DD_CMD='dd if=/dev/zero of=/tmp/testfile bs=1M count=100 oflag=direct 2>&1 | tail -1'

echo "=== Disk I/O Benchmark ==="
echo "Escribiendo 100MB con dd..."

# Bare metal
bare_result=$(bash -c "$DD_CMD")
bare_speed=$(echo "$bare_result" | grep -oP '[\d.]+ [MG]B/s' || echo "$bare_result" | awk '{print $(NF-1), $NF}')
echo "bare,io_write,$bare_speed" >> "$OUTFILE"
echo "Bare metal: $bare_speed"

for runtime in docker podman; do
    if ! command -v "$runtime" &>/dev/null; then continue; fi

    # Overlay (dentro del contenedor)
    overlay_result=$($runtime run --rm ubuntu bash -c "$DD_CMD" 2>&1)
    overlay_speed=$(echo "$overlay_result" | grep -oP '[\d.]+ [MG]B/s' || echo "$overlay_result" | awk '{print $(NF-1), $NF}')
    echo "${runtime},io_overlay,$overlay_speed" >> "$OUTFILE"
    echo "${runtime} overlay: $overlay_speed"

    # Volume mount
    tmpdir=$(mktemp -d)
    volume_result=$($runtime run --rm -v "$tmpdir":/mnt ubuntu bash -c \
        'dd if=/dev/zero of=/mnt/testfile bs=1M count=100 oflag=direct 2>&1 | tail -1')
    volume_speed=$(echo "$volume_result" | grep -oP '[\d.]+ [MG]B/s' || echo "$volume_result" | awk '{print $(NF-1), $NF}')
    echo "${runtime},io_volume,$volume_speed" >> "$OUTFILE"
    echo "${runtime} volume: $volume_speed"
    rm -rf "$tmpdir"
done

echo "Resultados en $OUTFILE"
```

### Resultados de referencia

Se escribieron 100 MB con `dd` usando `conv=fdatasync` para forzar escritura a disco. 3 repeticiones por modo.

**Datos crudos (MB/s):**

| Rep | Bare Metal | Docker overlay | Docker volume | Podman overlay | Podman volume |
|-----|-----------|----------------|---------------|----------------|---------------|
| 1 | 448 | 380 | 510 | **1,700** | 519 |
| 2 | 458 | 370 | 499 | **1,700** | 512 |
| 3 | 504 | 381 | 511 | **1,600** | 508 |

**Promedios y comparación:**

| Modo | Promedio | vs Bare Metal | Veredicto |
|------|---------|---------------|-----------|
| Bare Metal (directo) | **470 MB/s** | — | Referencia |
| Docker overlay | **377 MB/s** | 80% (-20%) | Overhead real del overlay2 del kernel |
| Docker volume | **507 MB/s** | 108% (+8%) | Nativo — bypasea el overlay |
| Podman overlay | **1,667 MB/s** | 354% (+254%) | **DATO FALSO** — ver abajo |
| Podman volume | **513 MB/s** | 109% (+9%) | Nativo — igual que Docker |

**El dato falso de Podman overlay**: 1.7 GB/s es más de 3x la velocidad de bare metal. ¿Podman descubrió un disco más rápido? No. Lo que pasa es:

1. Podman rootless usa `fuse-overlayfs` (un filesystem implementado en **espacio de usuario** vía FUSE) en lugar del `overlay2` nativo del kernel que usa Docker.
2. Cuando `dd` llama `fdatasync()` dentro de `fuse-overlayfs`, esa llamada puede no propagarse hasta el disco real — los datos quedan en la **page cache** del kernel (que es RAM).
3. Estamos midiendo velocidad de escritura a RAM (~20+ GB/s de bandwidth), no a SSD (~500 MB/s). 1.7 GB/s cae justo en el rango de page cache con algo de overhead FUSE.

Docker **no tiene este problema** porque corre como root y usa el driver `overlay2` nativo del kernel, donde `fdatasync()` sí llega al disco real.

> **Lección de benchmarking**: Un número inesperadamente bueno es tan sospechoso como uno malo. Siempre pregúntate "¿tiene sentido este resultado?" antes de celebrar. 1.7 GB/s en un SSD que normalmente da ~470 MB/s es una señal clara de que el benchmark no está midiendo lo que creemos.

**Lo que sí podemos concluir con confianza:**
- **Docker overlay** (~377 MB/s) tiene ~20% de overhead real vs bare metal (~470 MB/s) — este es el costo del overlay filesystem
- **Volúmenes montados** (~510 MB/s en ambos runtimes) recuperan e incluso superan ligeramente el rendimiento directo, porque escriben directamente al filesystem del host sin pasar por ninguna capa overlay
- **Docker overlay vs Docker volume**: 377 vs 507 MB/s — los volúmenes son **1.34x más rápidos**

**Moraleja: para operaciones intensivas de I/O (bases de datos, logs, archivos grandes), siempre usa volúmenes.**

![Comparación de I/O: escritura de 100MB](./images/io_comparison.png)

:::exercise{title="Medir I/O" difficulty="2"}

1. Ejecuta:

```bash
bash bench_io.sh
```

2. Compara las velocidades. ¿Cuánto más lento es overlay vs bare metal?

3. ¿Los volúmenes recuperan el rendimiento perdido?

4. ¿Qué implicaciones tiene esto para bases de datos en contenedores?

:::

---

## Experimento 5: Nested containers

**Objetivo**: ¿Se pueden correr contenedores dentro de contenedores? ¿Cómo se compara Docker-in-Docker vs Podman-in-Podman?

### ¿Qué medimos?

Tiempo de arrancar un contenedor **dentro** de otro contenedor.

### El script

```bash
#!/bin/bash
# bench_nested.sh - Mide contenedores anidados
set -e

OUTFILE="results/nested.csv"
mkdir -p results

echo "runtime,metric,value" > "$OUTFILE"

echo "=== Nested Containers ==="

# Docker-in-Docker (necesita --privileged)
if command -v docker &>/dev/null; then
    echo "Docker-in-Docker (requiere --privileged)..."
    dind_time=$( { time docker run --rm --privileged \
        docker:dind sh -c '
            # Esperar a que el daemon arranque
            timeout 30 sh -c "until docker info > /dev/null 2>&1; do sleep 1; done"
            time docker run --rm alpine echo ok
        '; } 2>&1 | grep real | tail -1 | awk '{print $2}' | \
        sed 's/0m//;s/s//')
    echo "docker,nested_seconds,$dind_time" >> "$OUTFILE"
    echo "Docker-in-Docker: ${dind_time}s"
fi

# Podman-in-Podman (no necesita --privileged)
if command -v podman &>/dev/null; then
    echo "Podman-in-Podman..."
    pinp_time=$( { time podman run --rm --security-opt label=disable \
        quay.io/podman/stable podman run --rm alpine echo ok; } 2>&1 | \
        grep real | tail -1 | awk '{print $2}' | sed 's/0m//;s/s//')
    echo "podman,nested_seconds,$pinp_time" >> "$OUTFILE"
    echo "Podman-in-Podman: ${pinp_time}s"
fi

echo "Resultados en $OUTFILE"
```

### Resultados de referencia

En nuestra ejecución, **ambos fallaron**:

| Modo | Resultado | Motivo |
|------|-----------|--------|
| Docker-in-Docker | Error | `--privileged` no disponible en este entorno |
| Podman-in-Podman | Error | Configuración de `fuse` / user namespaces insuficiente |

**Análisis**: Este resultado es en sí mismo instructivo. Correr contenedores anidados es **difícil** y depende mucho del entorno:

- **Docker-in-Docker** necesita `--privileged`, que desactiva casi todas las protecciones de seguridad del contenedor. Muchos entornos (CI/CD, servidores compartidos, entornos restringidos) lo bloquean por razones de seguridad.
- **Podman-in-Podman** necesita acceso a `/dev/fuse` y una configuración correcta de user namespaces anidados. En distribuciones más antiguas o con configuraciones restrictivas, esto falla.

> **Lección práctica**: Si necesitas correr contenedores dentro de contenedores (común en CI/CD), investiga las alternativas: Kaniko para builds de imágenes sin daemon, o Podman rootless con la configuración correcta de `/etc/subuid` y `/etc/subgid`.

> ⚠️ **Advertencia**: `--privileged` desactiva la mayoría de las protecciones de seguridad del contenedor. No lo uses en producción a menos que sea estrictamente necesario.

:::exercise{title="Contenedores anidados" difficulty="3"}

1. Ejecuta:

```bash
bash bench_nested.sh
```

⚠️ **Es probable que falle.** Eso es parte del ejercicio. Lee el error con atención.

2. Si falló:
   - ¿Qué error dio Docker-in-Docker? ¿Qué permisos pide `--privileged`?
   - ¿Qué error dio Podman-in-Podman? ¿Qué configuración falta?

3. Si no falló (o después de investigar):
   - ¿Por qué Docker-in-Docker necesita `--privileged`?
   - ¿Por qué Podman *en teoría* no lo necesita?

4. ¿En qué escenarios necesitarías contenedores anidados? (Pista: CI/CD, builds de imágenes)

5. Investiga qué es **Kaniko** y por qué es una alternativa a Docker-in-Docker para builds en CI/CD.

:::

---

## Experimento 6: Scaling

**Objetivo**: ¿Qué pasa cuando lanzamos muchos contenedores? ¿Cómo escala la memoria y el tiempo de arranque?

### ¿Qué medimos?

Lanzamos 10, 20 y 50 contenedores y medimos:
- Tiempo total de arranque
- Memoria total consumida

### El script

```bash
#!/bin/bash
# bench_scale.sh - Mide escalamiento
set -e

OUTFILE="results/scale.csv"
mkdir -p results

echo "runtime,count,time_seconds,memory_mb" > "$OUTFILE"

cleanup() {
    local runtime=$1
    local prefix=$2
    for id in $($runtime ps -aq --filter "name=$prefix" 2>/dev/null); do
        $runtime stop "$id" > /dev/null 2>&1
        $runtime rm "$id" > /dev/null 2>&1
    done
}

get_used_mb() {
    free -m | awk '/^Mem:/ {print $3}'
}

echo "=== Scaling Benchmark ==="

for runtime in docker podman; do
    if ! command -v "$runtime" &>/dev/null; then continue; fi

    for count in 10 20 50; do
        echo "${runtime}: lanzando $count contenedores..."
        baseline_mem=$(get_used_mb)

        start_time=$(date +%s%N)
        for i in $(seq 1 "$count"); do
            $runtime run -d --name "scale_${runtime}_${count}_${i}" ubuntu sleep 300 > /dev/null 2>&1
        done
        end_time=$(date +%s%N)

        elapsed=$(echo "scale=2; ($end_time - $start_time) / 1000000000" | bc)
        current_mem=$(get_used_mb)
        mem_used=$((current_mem - baseline_mem))

        echo "${runtime},${count},${elapsed},${mem_used}" >> "$OUTFILE"
        echo "  ${count} contenedores: ${elapsed}s, +${mem_used}MB"

        # Cleanup
        cleanup "$runtime" "scale_${runtime}_${count}"
        sleep 2
    done
done

echo "Resultados en $OUTFILE"
```

### Resultados de referencia

Se lanzaron 10, 20 y 50 contenedores (`sleep 300`) en serie, midiendo tiempo total y delta de memoria.

**Datos crudos:**

| Runtime | Contenedores | Tiempo total | Memoria overhead |
|---------|-------------|-------------|-----------------|
| Docker | 10 | 2.00s | +50 MB |
| Docker | 20 | 7.76s | +119 MB |
| Docker | 50 | 10.70s | +199 MB |
| Podman | 10 | 1.04s | +35 MB |
| Podman | 20 | 2.05s | +14 MB* |
| Podman | 50 | 5.28s | +87 MB |

*\*Valor ruidoso — mismo problema de `free -m` del Experimento 2.*

**Métricas por contenedor:**

| Runtime | Contenedores | Tiempo/contenedor | MB/contenedor |
|---------|-------------|-------------------|---------------|
| Docker | 10 | 200 ms | 5.0 MB |
| Docker | 20 | 388 ms | 6.0 MB |
| Docker | 50 | 214 ms | 4.0 MB |
| Podman | 10 | 104 ms | 3.5 MB |
| Podman | 20 | 103 ms | 0.7 MB* |
| Podman | 50 | 106 ms | 1.7 MB |

**Comparación directa a 50 contenedores:**

| Métrica | Docker | Podman | Diferencia |
|---------|--------|--------|------------|
| Tiempo total | 10.70s | 5.28s | Podman **2.03x más rápido** |
| Memoria total | +199 MB | +87 MB | Podman **2.29x menos memoria** |
| Tiempo/contenedor | 214 ms | 106 ms | Podman **2.02x más rápido** |

**Análisis detallado:**

**Podman fue más rápido en todo.** ¿Por qué? El modelo fork-exec de Podman lanza cada contenedor como un proceso independiente — no hay cuello de botella en un daemon central. Nota cómo el tiempo por contenedor de Podman es **perfectamente consistente**: ~104 ms sin importar si hay 10, 20 o 50 contenedores. Cada `podman run` es independiente.

Docker, en cambio, muestra un patrón interesante:
- 10 contenedores: 200 ms/cont — el daemon maneja bien
- 20 contenedores: **388 ms/cont** — el daemon se congestiona, el doble de lento
- 50 contenedores: 214 ms/cont — se recupera, posiblemente por batching interno de `containerd`

El salto a 388 ms/cont con 20 contenedores revela el cuello de botella del daemon: `dockerd` serializa las peticiones API, y `containerd` tiene un queue interno. Con 20 peticiones concurrentes, la cola se satura.

**Podman usó menos memoria.** Sin daemon, no hay overhead constante de `dockerd` + `containerd`. Cada contenedor en Podman solo tiene un proceso `conmon` (container monitor), que es más ligero que la infraestructura por-contenedor de `containerd`.

> **Observación sobre Podman 20 = +14 MB**: Este valor es sospechosamente bajo (0.7 MB/contenedor). Es el mismo problema de ruido con `free -m` del Experimento 2 — entre mediciones, el OS liberó caché que enmascaró el overhead real. Los valores de 50 contenedores (+87 MB = 1.7 MB/cont) son más confiables porque el delta es mayor.

El escalamiento es **aproximadamente lineal** en ambos: el doble de contenedores toma aproximadamente el doble de tiempo.

![Escalamiento: memoria y tiempo vs número de contenedores](./images/scale_memory.png)

:::exercise{title="Medir escalamiento" difficulty="3"}

1. Ejecuta:

```bash
bash bench_scale.sh
```

⚠️ Este benchmark puede tardar varios minutos y usar recursos significativos.

2. Grafica los resultados (o usa `analyze.py`):
   - Eje X: número de contenedores
   - Eje Y1: tiempo de arranque total
   - Eje Y2: memoria consumida

3. ¿El escalamiento es lineal o exponencial?

4. ¿A cuántos contenedores llenarías la memoria de tu máquina? Calcula: `RAM_disponible / overhead_por_contenedor`

:::

---

## Experimento 7: CPU puro (sin startup)

**Objetivo**: El Experimento 3 midió 12-20% de overhead de CPU, pero ese número incluye el tiempo de startup del contenedor y la carga del binario de bash. ¿Cuánto overhead hay realmente una vez que el contenedor ya está corriendo?

### ¿Qué medimos?

El mismo loop de bash, pero usando `docker exec` en un contenedor **ya corriendo** en vez de `docker run` (que crea uno nuevo). Esto aísla el overhead puro de CPU.

Redujimos el conteo a 1,000,000 (vs 10M del Exp 3) para que cada medición tome ~5 segundos en vez de ~50.

### El script

```bash
#!/bin/bash
# bench_cpu_exec.sh - CPU sin startup
# Pre-arranca el contenedor, luego mide vía exec
docker run -d --name cpu_test ubuntu sleep 300
sleep 1  # estabilizar

CPU_CMD='i=0; while [ $i -lt 1000000 ]; do i=$((i+1)); done'

# Bare metal
time bash -c "$CPU_CMD"

# Docker exec (sin startup)
time docker exec cpu_test bash -c "$CPU_CMD"

docker rm -f cpu_test
```

### Resultados de referencia

Se ejecutó 3 veces por runtime. El contenedor se pre-arrancó y se esperó 1 segundo antes de medir.

**Datos crudos (segundos, contando hasta 1M):**

| Rep | Bare Metal | Docker exec | Podman exec |
|-----|-----------|-------------|-------------|
| 1 | 4.82 | 5.16 | 5.32 |
| 2 | 4.60 | 4.68 | 5.71 |
| 3 | 5.18 | 4.61 | 5.23 |

**Promedios y overhead:**

| Runtime | Promedio | Overhead % |
|---------|---------|------------|
| Bare Metal | **4.87s** | — |
| Docker exec | **4.82s** | **-1.1%** |
| Podman exec | **5.42s** | **+11.4%** |

**Comparación con Experimento 3 (docker run):**

| Runtime | Overhead con `run` (Exp 3) | Overhead con `exec` (Exp 7) | Diferencia |
|---------|---------------------------|----------------------------|------------|
| Docker | +12.3% | **-1.1%** | El overhead de Docker era **todo startup** |
| Podman | +20.2% | **+11.4%** | ~9% era startup, ~11% es overhead real de fuse-overlayfs |

**Análisis**: Docker exec tiene **cero overhead de CPU** — el resultado de -1.1% está dentro del margen de error (ruido de ~0.5s entre repeticiones). Esto confirma que los contenedores Docker no añaden overhead al cómputo puro; todo el +12.3% del Exp 3 venía de crear namespaces, montar el overlay y cargar el binario de bash.

Podman sigue mostrando ~11% de overhead incluso sin startup. Esto es consistente con `fuse-overlayfs`: cada vez que el intérprete de bash lee un archivo (librerías, el script mismo), pasa por una capa FUSE en espacio de usuario. En un loop de 1M iteraciones, ese overhead se acumula.

> **Conclusión**: Para tareas de cómputo puro, Docker tiene **0% de overhead** una vez que el contenedor está corriendo. Podman tiene ~11% por fuse-overlayfs, que desaparece si usas Podman como root (overlay nativo del kernel).

![Comparación de CPU: exec vs run](./images/cpu_exec_comparison.png)

---

## Experimento 8: Memoria cgroup (medición exacta)

**Objetivo**: El Experimento 2 usó `free -m` y obtuvo valores negativos porque el ruido del sistema (~50-150 MB) era mayor que la señal (~4 MB por contenedor). Necesitamos un instrumento más preciso.

### ¿Qué medimos?

Usamos `docker stats` / `podman stats` que lee `memory.current` del cgroup de cada contenedor — da la memoria **exacta** asignada por el kernel a ese contenedor específico, inmune al ruido del sistema.

También medimos el RSS (Resident Set Size) del daemon de Docker (`dockerd`) y de los procesos `conmon` de Podman.

### El script

{% raw %}
```bash
#!/bin/bash
# bench_memory_cgroup.sh - Memoria exacta por contenedor

# Lanzar contenedores
docker run -d --name mem_test ubuntu sleep 3600

# Leer memoria del cgroup vía stats
docker stats --no-stream --format '{{.Name}},{{.MemUsage}}'

# Medir RSS del daemon
ps -p $(pgrep -x dockerd) -o rss=
```
{% endraw %}

### Resultados de referencia

Se midió con 1, 3 y 5 contenedores idle (`sleep 3600`).

**Memoria por contenedor (cgroup):**

| Contenedores | Docker (KB/cont) | Podman (KB/cont) |
|-------------|-------------------|-------------------|
| 1 | 432 | 94 |
| 3 | 428 | 99 |
| 5 | 429 | 98 |

**Comparación: cgroup vs free -m (Exp 2):**

| Método | Docker 1 cont. | Docker 5 cont. | Podman 1 cont. | Podman 5 cont. |
|--------|----------------|-----------------|-----------------|-----------------|
| `free -m` (Exp 2) | -41 MB | +71 MB | +39 MB | -143 MB |
| cgroup (Exp 8) | **432 KB** | **2,148 KB** | **94 KB** | **490 KB** |

La diferencia es abismal. `free -m` reportaba ±143 MB de fluctuación mientras que el dato real era **menos de 500 KB por contenedor**.

**Overhead del daemon / conmon:**

| Métrica | 0 cont. | 1 cont. | 3 cont. | 5 cont. |
|---------|---------|---------|---------|---------|
| dockerd RSS | 116.7 MB | 116.9 MB | 119.1 MB | 121.6 MB |
| conmon RSS | 0 MB | 1.8 MB | 5.2 MB | 8.8 MB |

**Análisis**:

- **Docker**: Cada contenedor usa ~430 KB de memoria de cgroup. El daemon `dockerd` consume ~117 MB como costo fijo (¡con 0 o 5 contenedores!), creciendo solo ~1 MB por contenedor extra.
- **Podman**: Cada contenedor usa solo ~97 KB de memoria de cgroup — **4.4x menos que Docker**. No hay daemon; cada contenedor tiene un proceso `conmon` (container monitor) que usa ~1.8 MB, creciendo linealmente.
- **Costo total para 5 contenedores**: Docker = 122 MB (daemon) + 2.1 MB (containers) = ~124 MB. Podman = 9 MB (conmon) + 0.5 MB (containers) = ~9.5 MB. Podman usa **13x menos memoria total**.

> **Lección de benchmarking**: La herramienta de medición importa tanto como lo que mides. `free -m` mide el sistema completo (ruido >> señal), mientras que `docker stats` lee el cgroup específico del contenedor (señal pura). Siempre usa el instrumento más específico disponible.

![Memoria por contenedor vía cgroup y RSS del daemon](./images/memory_cgroup_comparison.png)

---

## Experimento 9: Nested containers v2

**Objetivo**: El Experimento 5 probó 2 enfoques y ambos fallaron. Aquí probamos **6 enfoques diferentes** para entender cuáles funcionan y por qué.

### Los 6 enfoques

| # | Runtime | Enfoque | Descripción |
|---|---------|---------|-------------|
| 1 | Docker | `dind_privileged` | Docker-in-Docker clásico con `--privileged` |
| 2 | Docker | `socket_mount` | Montar `/var/run/docker.sock` (patrón CI/CD) |
| 3 | Docker | `dind_relaxed_security` | DinD con AppArmor/seccomp deshabilitados + `SYS_ADMIN` |
| 4 | Podman | `pinp_basic` | `--security-opt label=disable --device /dev/fuse` |
| 5 | Podman | `pinp_privileged` | Con `--privileged` |
| 6 | Podman | `pinp_vfs` | Con storage driver VFS (evita overlay-in-overlay) |

### Resultados de referencia

| # | Runtime | Enfoque | Resultado | Tiempo | Error |
|---|---------|---------|-----------|--------|-------|
| 1 | Docker | dind_privileged | **Error** | 30.6s | Timeout: el daemon interno no pudo conectar al socket |
| 2 | Docker | socket_mount | **Success** | 2.9s | — |
| 3 | Docker | dind_relaxed_security | **Error** | 30.5s | Mismo problema que #1 |
| 4 | Podman | pinp_basic | **Error** | 2.4s | `mount proc: Operation not permitted` |
| 5 | Podman | pinp_privileged | **Success** | 2.6s | — |
| 6 | Podman | pinp_vfs | **Error** | 2.6s | `mount proc: Operation not permitted` |

**Solo 2 de 6 enfoques funcionaron**: socket mount (Docker) y privileged (Podman).

### Análisis por enfoque

**Docker DinD (#1, #3) — Fallaron**: El contenedor `docker:dind` intenta arrancar un daemon `dockerd` interno. El daemon intenta conectar a `tcp://docker:2375` (que no existe en este entorno). Ni `--privileged` ni la relajación de seguridad resuelven esto porque el problema es de red/DNS, no de permisos. En un ambiente con Docker Compose y un servicio `docker:dind` separado, esto sí funciona.

**Docker socket mount (#2) — Funcionó**: Montar el socket del host (`/var/run/docker.sock`) permite al contenedor hablar con el Docker daemon del host. Técnicamente **no es nesting real** (no hay Docker dentro de Docker), pero es el patrón más usado en CI/CD porque es simple y rápido (~2.9s). El trade-off: el contenedor tiene acceso completo al daemon del host — puede ver, crear y eliminar **todos** los contenedores.

**Podman básico y VFS (#4, #6) — Fallaron**: `mount proc: Operation not permitted` indica que el user namespace del Podman interior no tiene permisos para montar `/proc`. Esto requiere que el kernel permita nested user namespaces y que `/proc/sys/kernel/unprivileged_userns_clone` esté habilitado.

**Podman privileged (#5) — Funcionó**: `--privileged` desactiva todas las restricciones de seguridad, permitiendo que el Podman interior monte `/proc` y cree sus propios namespaces. Funcionó en 2.6 segundos — más rápido que el socket mount de Docker.

> **Conclusión práctica**: Para CI/CD, usa **socket mount** — es el enfoque más simple y no requiere `--privileged`. Para Podman, necesitas `--privileged` o una configuración cuidadosa del kernel para permitir nested user namespaces. En ambos casos, ten cuidado con las implicaciones de seguridad.

![6 enfoques para contenedores anidados](./images/nested_v2_comparison.png)

---

## Tabla resumen de resultados

| Aspecto | Bare Metal | Docker | Podman | Veredicto |
|---------|-----------|--------|--------|-----------|
| **Startup** | ~1.3 ms | ~308 ms | ~178 ms | Podman más rápido (fork-exec directo) |
| **CPU (run)** | ~47s | ~53s (+12%) | ~57s (+20%) | Overhead bajo; incluye startup |
| **CPU (exec)** | ~4.87s | ~4.82s (-1%) | ~5.42s (+11%) | Docker = 0% overhead real |
| **Memoria (free -m)** | — | +199 MB / 50 cont. | +87 MB / 50 cont. | Ruidoso — ver cgroup |
| **Memoria (cgroup)** | — | 430 KB/cont | 97 KB/cont | Podman 4.4x menos |
| **I/O overlay** | ~470 MB/s | ~377 MB/s | ~1.7 GB/s* | *Podman: page cache, no disco real |
| **I/O volume** | ~470 MB/s | ~507 MB/s | ~513 MB/s | Ambos ≈ nativo |
| **Nested (Exp 5)** | — | Falló | Falló | Ambos difíciles |
| **Nested v2** | — | Socket mount ✓ | Privileged ✓ | 2 de 6 enfoques funcionan |
| **Escalamiento (50)** | — | 10.7s | 5.3s | Podman 2x más rápido |

> \* El resultado de Podman overlay es engañoso — ver el análisis en el Experimento 4.

![Resumen general de benchmarks](./images/summary.png)

## Conclusiones

1. **El overhead de CPU es cero (Docker) o bajo (Podman).** El Exp 3 midió 12-20%, pero el Exp 7 demostró que al eliminar el startup, Docker tiene **0% de overhead** (-1.1%, dentro del margen de error). Podman mantiene ~11% por fuse-overlayfs. Para tareas de cómputo intensivo, el overhead del contenedor es despreciable.

2. **El costo principal es el startup.** Crear namespaces, montar overlays y configurar cgroups toma cientos de milisegundos (~180-310 ms en nuestras pruebas). Esto importa si creas/destruyes contenedores frecuentemente (como en serverless o CI/CD).

3. **El overlay filesystem tiene overhead real.** Docker overlay fue ~20% más lento que bare metal. Para bases de datos o aplicaciones con I/O intensivo, usa volúmenes montados — recuperan el rendimiento nativo.

4. **Podman sorprende en rendimiento.** Contrario a la sabiduría convencional, Podman fue más rápido en startup (178 vs 308 ms) y en escalamiento (5.3s vs 10.7s para 50 contenedores). El modelo fork-exec sin daemon es más eficiente que la arquitectura cliente-daemon de Docker. La frase "Docker es más rápido porque tiene daemon pre-calentado" no se sostuvo en nuestras pruebas.

5. **La herramienta de medición importa.** El Exp 2 (`free -m`) reportó -41 MB para 1 contenedor Docker. El Exp 8 (cgroup) midió 432 KB. La diferencia: 5 órdenes de magnitud. Siempre usa el instrumento más específico disponible — `docker stats` lee el cgroup exacto del contenedor, inmune al ruido del sistema.

6. **Contenedores anidados: el pragmatismo gana.** De 6 enfoques probados, solo 2 funcionaron: socket mount (Docker, el patrón CI/CD) y `--privileged` (Podman). DinD puro falló por configuración de red. La solución práctica es montar el socket del daemon — no es "nesting real" pero resuelve el caso de uso real.

7. **Medir es difícil.** Varios de nuestros experimentos produjeron resultados que requirieron análisis cuidadoso: la memoria fue ruidosa, el I/O de Podman overlay midió RAM en vez de disco, y los contenedores anidados fallaron inicialmente. Esto es normal en benchmarking — la habilidad no es solo correr el script, sino **interpretar los resultados críticamente** y buscar mejores instrumentos cuando los resultados no tienen sentido.

8. **Para ciencia de datos**: el overhead es irrelevante. Tu modelo de ML no va a ser más lento en un contenedor. El beneficio de reproducibilidad supera por mucho el costo de rendimiento.

:::prompt{title="Analizar resultados de benchmarks" for="ChatGPT/Claude"}

Ejecuté benchmarks de contenedores (Docker vs Podman vs bare metal) y obtuve estos resultados:

```
[pega los contenidos de tus CSVs o la salida del benchmark aquí]
```

Mi hardware es:
- CPU: [modelo]
- RAM: [cantidad]
- Disco: [SSD/HDD]
- SO: [distribución y versión]

Analiza mis resultados:
1. ¿Son normales para mi hardware?
2. ¿Qué explica las diferencias que observo?
3. ¿Hay algo inesperado que debería investigar?

:::
