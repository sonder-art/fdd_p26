# Volúmenes

Los contenedores son **efímeros** — cuando un contenedor se elimina, todo su sistema de archivos desaparece. Esto es una feature, no un bug: garantiza que cada ejecución empieza limpia. Pero en la práctica necesitas que ciertos datos persistan: bases de datos, logs, configuraciones, tu código fuente.

Para eso existen los **volúmenes**: un mecanismo para conectar directorios del host con directorios dentro del contenedor.

## El problema: el overlay filesystem es una caja cerrada

Recuerda la arquitectura de un contenedor: su sistema de archivos es un **overlay** — capas de solo lectura (la imagen) con una capa de escritura encima. Cuando el contenedor escribe un archivo, ese archivo vive en la capa de escritura. Cuando el contenedor se destruye (`docker rm`), esa capa se borra.

```
┌─────────────────────────────┐
│   Capa de escritura (efímera)│  ← tus datos viven aquí y MUEREN aquí
├─────────────────────────────┤
│   Capa imagen: ubuntu        │  ← solo lectura
└─────────────────────────────┘
```

Veámoslo en acción. Crea un archivo dentro de un contenedor y luego intenta encontrarlo:

```bash
# Crear un contenedor, escribir un archivo adentro
docker run --name efimero ubuntu bash -c 'echo "datos importantes" > /tmp/datos.txt'

# El contenedor terminó pero no lo borramos — el archivo sigue ahí
docker start -a efimero
docker exec efimero cat /tmp/datos.txt 2>/dev/null || echo "contenedor no está corriendo"

# Pero si borramos el contenedor...
docker rm efimero

# Adiós datos. No hay forma de recuperarlos.
```

Un volumen **perfora** el overlay y conecta un directorio del contenedor directamente con un directorio del host:

```
Host                            Contenedor
┌──────────────┐               ┌─────────────────────────────┐
│ /home/dev/app│ ◄────────────►│ /app                        │
└──────────────┘   bind mount   │                             │
                               ├─────────────────────────────┤
                               │   Capa imagen: python:3.11   │
                               └─────────────────────────────┘
```

Lo que escribes en `/app` dentro del contenedor aparece en `/home/dev/app` en tu host, y viceversa. El overlay no interviene — la escritura va directamente al filesystem del host.

## Tipos de volúmenes

Hay dos formas principales de montar almacenamiento en un contenedor:

### 1. Bind mount (`-v /ruta/host:/ruta/contenedor`)

Monta un directorio **específico** de tu host dentro del contenedor. Tú controlas exactamente dónde viven los datos.

```bash
# Docker
docker run --rm -v /home/dev/proyecto:/app python:3.11 python /app/main.py

# Podman (idéntico)
podman run --rm -v /home/dev/proyecto:/app python:3.11 python /app/main.py
```

El directorio `/home/dev/proyecto` de tu host se ve como `/app` dentro del contenedor. Cualquier cambio en un lado se refleja instantáneamente en el otro.

### 2. Named volume (`docker volume create`)

Docker/Podman gestionan el almacenamiento — tú solo le das un nombre.

```bash
# Crear un volumen nombrado
docker volume create mis-datos

# Usarlo
docker run --rm -v mis-datos:/datos ubuntu bash -c 'echo "hola" > /datos/test.txt'

# Otro contenedor puede leer los mismos datos
docker run --rm -v mis-datos:/datos ubuntu cat /datos/test.txt
# hola
```

¿Dónde viven físicamente los datos? Docker los guarda en `/var/lib/docker/volumes/mis-datos/_data/`. No necesitas saberlo — Docker lo gestiona.

**¿Cuándo usar cada uno?**

| Tipo | Caso de uso | Ejemplo |
|------|-------------|---------|
| Bind mount | Desarrollo, código fuente, archivos que editas | `-v ./mi-proyecto:/app` |
| Named volume | Datos persistentes que no editas directamente | `-v postgres-data:/var/lib/postgresql/data` |

---

## Laboratorio 1: entendiendo bind mounts paso a paso

Vamos a construir la intuición de qué le pasa al host, al contenedor y a la imagen cuando usas volúmenes.

> **IMPORTANTE**: Este laboratorio usa la imagen `python:3.11` directamente — **NO hay Dockerfile**. El punto es entender bind mounts sin construir nada.

**PRIMERO, navega al directorio del laboratorio:**

```bash
cd exercises/lab1_bind_mounts/
```

Ahí encontrarás un archivo `app.py`. **Ábrelo y lee qué hace** antes de continuar:

```bash
cat app.py
```

Es un script Python que imprime información del sistema y escribe un archivo `output.txt`.

### Paso 1: inspeccionar qué tienes en tu host

```bash
ls -la
# Deberías ver: app.py
```

Tienes UN archivo en tu host. No hay Dockerfile, no hay imagen custom. Vamos a usar la imagen `python:3.11` tal cual.

### Paso 2: ejecutar SIN volumen vs CON volumen

```bash
# SIN volumen — el contenedor NO ve tus archivos
docker run --rm python:3.11 ls /app 2>/dev/null
# Error: /app no existe en la imagen

# CON volumen — el contenedor VE tu directorio
docker run --rm -v "$(pwd)":/app python:3.11 ls -la /app
# Verás app.py
```

**La diferencia es `-v "$(pwd)":/app`** — eso conecta tu directorio actual con `/app` dentro del contenedor.

### Paso 3: ejecutar tu código dentro del contenedor

```bash
docker run --rm -v "$(pwd)":/app python:3.11 python /app/app.py
```

Tu `app.py` vive en el host. Python vive en la imagen. **El volumen los conecta.**

### Paso 4: el contenedor escribe, el host recibe

Después de ejecutar el paso 3, revisa tu directorio:

```bash
ls -la
# Ahora deberías ver: app.py Y output.txt
cat output.txt
```

`app.py` creó `output.txt` dentro de `/app` en el contenedor — pero como `/app` es tu directorio montado, **el archivo apareció en tu host**. El contenedor ya no existe (`--rm`), pero el archivo persiste.

### Paso 5: editar en el host, ejecutar en el contenedor

Ahora **abre `app.py` con tu editor** y cambia algo. Por ejemplo, agrega un `print("EDITADO EN CALIENTE")` al final. Guarda el archivo.

Re-ejecuta **sin rebuild, sin nada**:

```bash
docker run --rm -v "$(pwd)":/app python:3.11 python /app/app.py
```

Deberías ver tu cambio. **Esto es la magia del bind mount**: el contenedor siempre ve la versión actual de tus archivos.

### Paso 6: la imagen NO cambió

```bash
# La imagen python:3.11 NO tiene tus archivos
docker run --rm python:3.11 ls /app 2>/dev/null
# Error: /app no existe — el volumen solo existió durante el run anterior

docker run --rm python:3.11 cat /app/app.py 2>/dev/null
# Error: la imagen no sabe nada de tu código
```

El volumen es una conexión **temporal** durante la ejecución del contenedor. La imagen NUNCA se modifica.

:::exercise{title="Explorar bind mounts" difficulty="1"}

**ASEGURATE de estar en `exercises/lab1_bind_mounts/`** antes de empezar.

Ejecuta todos los pasos del laboratorio 1 **manualmente, uno por uno**. Después responde:

1. ¿Qué pasa si borras `app.py` desde **dentro** del contenedor?

```bash
docker run --rm -v "$(pwd)":/app ubuntu rm /app/app.py
ls -la
```

¿El archivo desapareció del host? ¿Por qué? (Si sí desapareció, recrea `app.py` antes de continuar.)

2. ¿Qué pasa si montas un directorio que no existe?

```bash
docker run --rm -v /tmp/no-existe-todavia:/app ubuntu ls -la /app
ls -la /tmp/no-existe-todavia
```

¿Docker lo crea? ¿Con qué permisos?

3. Ejecuta los mismos experimentos con **Podman** en vez de Docker. ¿Los resultados son iguales?

:::

---

## Laboratorio 2: named volumes y PostgreSQL

Los named volumes brillan cuando necesitas datos persistentes que **no** editas directamente — como una base de datos.

> **NOTA**: Este laboratorio NO tiene archivos base — usas la imagen `postgres:16` directamente. **Escribe cada comando manualmente en tu terminal** para entender qué hace cada paso.

Vamos a levantar PostgreSQL en un contenedor y ver cómo los volúmenes mantienen tus datos vivos entre reinicios.

### Paso 1: levantar PostgreSQL con un named volume

```bash
# Crear un volumen para los datos de Postgres
docker volume create pg-datos

# Levantar PostgreSQL
docker run -d \
    --name mi-postgres \
    -e POSTGRES_USER=alumno \
    -e POSTGRES_PASSWORD=secreto \
    -e POSTGRES_DB=curso \
    -v pg-datos:/var/lib/postgresql/data \
    -p 5432:5432 \
    postgres:16
```

¿Qué hace cada flag?
- `-d`: corre en background (daemon)
- `-e`: variables de entorno que PostgreSQL usa para configurarse al primer arranque
- `-v pg-datos:/var/lib/postgresql/data`: los datos de la DB van al named volume, no al overlay
- `-p 5432:5432`: expone el puerto para conectarte desde tu host

Espera unos segundos a que PostgreSQL arranque:

```bash
docker logs mi-postgres 2>&1 | tail -3
# ... database system is ready to accept connections
```

### Paso 2: crear datos

```bash
# Conectarte a PostgreSQL dentro del contenedor
docker exec -it mi-postgres psql -U alumno -d curso -c "
CREATE TABLE estudiantes (
    id SERIAL PRIMARY KEY,
    nombre TEXT NOT NULL,
    carrera TEXT
);

INSERT INTO estudiantes (nombre, carrera) VALUES
    ('Ana García', 'Ciencia de Datos'),
    ('Luis Pérez', 'Actuaría'),
    ('María López', 'Matemáticas Aplicadas');
"

# Verificar que los datos existen
docker exec mi-postgres psql -U alumno -d curso -c "SELECT * FROM estudiantes;"
```

### Paso 3: destruir el contenedor

```bash
# Parar y eliminar el contenedor
docker stop mi-postgres
docker rm mi-postgres

# El contenedor ya no existe
docker ps -a | grep mi-postgres
# (nada)
```

Sin volumen, tus datos habrían muerto aquí. Pero usamos un named volume.

### Paso 4: resucitar los datos con un contenedor nuevo

```bash
# Crear un contenedor NUEVO con el MISMO volumen
docker run -d \
    --name mi-postgres-2 \
    -e POSTGRES_USER=alumno \
    -e POSTGRES_PASSWORD=secreto \
    -e POSTGRES_DB=curso \
    -v pg-datos:/var/lib/postgresql/data \
    -p 5432:5432 \
    postgres:16

# Esperar a que arranque
sleep 3

# ¿Los datos sobrevivieron?
docker exec mi-postgres-2 psql -U alumno -d curso -c "SELECT * FROM estudiantes;"
#  id |    nombre     |       carrera
# ----+---------------+---------------------
#   1 | Ana García    | Ciencia de Datos
#   2 | Luis Pérez    | Actuaría
#   3 | María López   | Matemáticas Aplicadas
```

El contenedor es nuevo. La imagen es la misma. Pero los **datos viven en el volumen**, no en el contenedor. Destruir y recrear el contenedor no afecta los datos.

### Paso 5: limpiar

{% raw %}
```bash
docker stop mi-postgres-2
docker rm mi-postgres-2

# El volumen sigue existiendo incluso sin contenedores
docker volume ls | grep pg-datos
# local     pg-datos

# Inspeccionar dónde vive físicamente
docker volume inspect pg-datos --format '{{.Mountpoint}}'
# /var/lib/docker/volumes/pg-datos/_data

# Cuando ya no necesites los datos:
docker volume rm pg-datos
```
{% endraw %}

### ¿Por qué no usar un bind mount para la DB?

Podrías hacer `-v /tmp/pg-data:/var/lib/postgresql/data`, y funcionaría. Pero named volumes tienen ventajas para bases de datos:

- Docker gestiona permisos automáticamente (PostgreSQL necesita que los archivos sean de uid 999)
- Son portables entre hosts vía `docker volume` commands
- No contaminas tu filesystem con archivos internos de Postgres

La regla práctica: **bind mount para tu código**, **named volume para datos de servicios**.

:::exercise{title="PostgreSQL con volúmenes" difficulty="2"}

**Escribe TODOS los comandos manualmente** — no copies y pegues bloques completos. El punto es que entiendas cada flag.

1. Ejecuta el laboratorio completo de PostgreSQL (pasos 1-5).

2. Después del paso 4, agrega más datos:

```bash
docker exec mi-postgres-2 psql -U alumno -d curso -c "
INSERT INTO estudiantes (nombre, carrera) VALUES ('Carlos Ruiz', 'Economía');
"
```

3. Destruye el contenedor y crea `mi-postgres-3` con el mismo volumen. ¿Ves los 4 estudiantes?

4. Ahora destruye el contenedor Y el volumen:

```bash
docker stop mi-postgres-3
docker rm mi-postgres-3
docker volume rm pg-datos
```

Crea `mi-postgres-4` con el mismo nombre de volumen. ¿Qué pasa con los datos?

5. ¿Qué pasa si cambias la versión de PostgreSQL?

```bash
docker volume create pg-datos-v2
# Levanta con postgres:16 y crea datos
# Luego destruye el contenedor y levanta con postgres:17 usando el mismo volumen
# ¿Funciona? ¿Por qué podría no funcionar?
```

:::

---

## Edge cases y trampas

### 1. El volumen sobrescribe el contenido de la imagen

Si la imagen tiene archivos en `/app` y montas un volumen vacío en `/app`, **el volumen gana** — los archivos originales de la imagen desaparecen.

```bash
# La imagen python:3.11 tiene archivos en /usr/local/lib/python3.11/
# Si montas algo encima...
mkdir -p /tmp/vacio
docker run --rm -v /tmp/vacio:/usr/local/lib/python3.11 python:3.11 python -c "import os"
# Error: no encuentra módulos — el volumen vacío reemplazó la librería estándar
```

Veámoslo más claro:

```bash
# Ver qué hay en la imagen sin volumen
docker run --rm python:3.11 ls /usr/local/lib/python3.11/ | head -5
# _bootstrap_external.pyi, abc.py, aifc.py, ...

# Con volumen vacío encima: TODO desaparece
docker run --rm -v /tmp/vacio:/usr/local/lib/python3.11 python:3.11 ls /usr/local/lib/python3.11/
# (vacío)
```

**Regla**: solo monta volúmenes en directorios que **tú controlas** (como `/app`, `/data`), no en directorios del sistema de la imagen.

### 2. Permisos: UID del host vs UID del contenedor

El contenedor y el host comparten el kernel, y los permisos de archivos se resuelven por **UID numérico**, no por nombre de usuario.

```bash
# Preparar directorio limpio
rm -rf /tmp/test-permisos && mkdir -p /tmp/test-permisos

# El contenedor corre como root (uid=0) por default
docker run --rm -v /tmp/test-permisos:/data ubuntu bash -c 'echo "hola" > /data/archivo.txt'

ls -la /tmp/test-permisos/archivo.txt
# -rw-r--r-- 1 root root 5 ... archivo.txt
# ¡El archivo es de root en tu host!
```

Esto puede causar problemas: tu usuario no puede borrar archivos creados por root del contenedor.

**Solución**: usa `--user` para ejecutar el contenedor con tu UID:

```bash
docker run --rm --user "$(id -u):$(id -g)" -v /tmp/test-permisos:/data ubuntu bash -c 'echo "hola" > /data/desde-mi-user.txt'

ls -la /tmp/test-permisos/desde-mi-user.txt
# -rw-r--r-- 1 TU_USUARIO TU_GRUPO 5 ... desde-mi-user.txt
```

Podman en modo rootless no tiene este problema — mapea UIDs automáticamente a tu usuario.

### 3. El volumen es bidireccional (¡cuidado!)

Si borras archivos desde el contenedor, se borran en el host. Si el contenedor corrompe datos, tus datos reales se corrompen.

```bash
# Preparar
mkdir -p /tmp/peligro-test
echo "archivo importante" > /tmp/peligro-test/importante.txt
ls /tmp/peligro-test/
# importante.txt

# ¡PELIGRO! Esto borra archivos de tu host
docker run --rm -v /tmp/peligro-test:/app ubuntu rm -rf /app/*
ls /tmp/peligro-test/
# (vacío) — tu archivo desapareció
```

Para protegerte, puedes montar en **modo solo lectura** con `:ro`:

```bash
echo "protegido" > /tmp/peligro-test/seguro.txt
docker run --rm -v /tmp/peligro-test:/app:ro ubuntu cat /app/seguro.txt     # ✓ leer funciona
docker run --rm -v /tmp/peligro-test:/app:ro ubuntu rm /app/seguro.txt      # ✗ error: read-only
# rm: cannot remove '/app/seguro.txt': Read-only file system
```

### 4. Rutas relativas vs absolutas

Docker requiere rutas absolutas. Si usas rutas relativas, usa `$(pwd)`:

```bash
# Esto NO funciona (Docker no interpreta rutas relativas)
docker run -v ./mi-proyecto:/app ubuntu ls /app
# Error o directorio vacío

# Esto SÍ funciona
docker run -v "$(pwd)/mi-proyecto":/app ubuntu ls /app
```

Podman sí acepta rutas relativas, pero por portabilidad usa siempre `$(pwd)`.

:::exercise{title="Edge cases en acción" difficulty="2"}

Ejecuta cada edge case **manualmente** y responde:

1. **Sobrescritura**: ¿qué pasa si montas un bind mount en `/bin` del contenedor?

```bash
mkdir -p /tmp/fake-bin
docker run --rm -v /tmp/fake-bin:/bin ubuntu ls
```

¿Qué error da? ¿Por qué? (Pista: `ls` vive en `/bin`)

2. **Múltiples volúmenes**: ¿puedes montar varios directorios a la vez?

```bash
mkdir -p /tmp/vol-a /tmp/vol-b
echo "A" > /tmp/vol-a/a.txt
echo "B" > /tmp/vol-b/b.txt
docker run --rm \
    -v /tmp/vol-a:/data-a \
    -v /tmp/vol-b:/data-b \
    ubuntu bash -c 'cat /data-a/a.txt; cat /data-b/b.txt'
```

3. **Volumen sobre volumen**: ¿qué pasa si montas dos volúmenes en paths anidados?

```bash
mkdir -p /tmp/outer /tmp/inner
echo "outer" > /tmp/outer/test.txt
echo "inner" > /tmp/inner/test.txt
docker run --rm \
    -v /tmp/outer:/data \
    -v /tmp/inner:/data/sub \
    ubuntu bash -c 'cat /data/test.txt; cat /data/sub/test.txt'
```

¿Cuál es cuál? ¿El inner override funciona?

:::

---

## Volúmenes para desarrollo: el bind mount como herramienta de debug

El caso de uso más potente de bind mounts en desarrollo es **montar tu código fuente** para iterar sin reconstruir la imagen.

### El problema sin volúmenes

Cada cambio en tu código requiere reconstruir la imagen:

```bash
# Ciclo sin volúmenes (lento):
vim main.py                    # 1. editar código
docker build -t mi-app .       # 2. reconstruir imagen (segundos a minutos)
docker run --rm mi-app          # 3. ejecutar
# ¿Bug? Volver al paso 1
```

Si tu `Dockerfile` instala dependencias, el build puede tardar minutos. Repetir esto por cada cambio de una línea es insufrible.

### La solución: montar tu código

```bash
# Ciclo con volumen (rápido):
docker run --rm -v "$(pwd)":/app mi-app    # tu código entra por el volumen
# ¿Bug? Edita el archivo, vuelve a ejecutar — sin rebuild
```

El contenedor usa la imagen (con dependencias instaladas) pero tu código entra **por el volumen**, no por la imagen. Cuando editas un archivo en tu editor, el cambio es instantáneo dentro del contenedor.

### Ejemplo concreto: proyecto Python con dependencias

**PRIMERO, navega al directorio del laboratorio:**

```bash
cd exercises/lab3_dev_workflow/
```

Ahí encontrarás **3 archivos**. Léelos antes de continuar:

```bash
cat main.py           # Script que usa 'requests' para consultar tu IP pública
cat requirements.txt  # Dependencia: requests==2.31.0
cat Dockerfile        # Imagen que instala deps y copia código
```

**Lee el `Dockerfile` con cuidado** — tiene 2 etapas de `COPY`:

```
FROM python:3.11
WORKDIR /app
COPY requirements.txt .        ← primero copia SOLO las dependencias
RUN pip install -r requirements.txt  ← las instala (esto es lento)
COPY . .                        ← después copia tu código
CMD ["python", "main.py"]
```

¿Por qué este orden? Porque Docker cachea capas. Si solo cambias `main.py`, la capa de `pip install` se reutiliza. Pero **aún así tienes que hacer rebuild**.

Ahora, el flujo **sin** volumen:

```bash
# Build (instala requests — toma ~10 segundos)
docker build -t dev-app .

# Ejecutar
docker run --rm dev-app
# Tu IP pública: X.X.X.X
```

Ahora **abre `main.py` con tu editor** y cámbialo. Por ejemplo, cambia la URL de `https://httpbin.org/ip` a `https://httpbin.org/headers` y ajusta el print para mostrar headers.

Ejecuta **SIN** volumen:

```bash
docker run --rm dev-app
```

**¿Qué imprime?** Sigue mostrando la IP, no los headers. La imagen tiene el código VIEJO del último `docker build`.

Ahora ejecuta **CON** volumen:

```bash
docker run --rm -v "$(pwd)":/app dev-app
```

**¿Qué imprime ahora?** Muestra los headers — el volumen inyectó tu código NUEVO. **Sin rebuild.**

### ¿Qué pasa si la imagen tiene un `main.py` diferente al volumen?

```bash
# La imagen tiene el main.py VIEJO (del docker build original)
docker run --rm dev-app python -c "import subprocess; subprocess.run(['head', '-1', '/app/main.py'])"
# ... lo que sea que había cuando hiciste build

# Con volumen, el volumen GANA — ves el nuevo
docker run --rm -v "$(pwd)":/app dev-app python -c "import subprocess; subprocess.run(['head', '-1', '/app/main.py'])"
# import requests (la versión actual de tu host)
```

El bind mount **siempre sobrescribe** lo que hay en la imagen en ese path. Esta es exactamente la mecánica que lo hace útil para desarrollo.

### Advertencia: esto es SOLO para desarrollo

El bind mount de código fuente es una herramienta de **desarrollo**, NO de producción. En producción:

1. Tu código **DEBE** estar dentro de la imagen (`COPY . .` en el Dockerfile)
2. La imagen debe ser **AUTOCONTENIDA** — no depender de volúmenes para funcionar
3. El `docker build` final **SIEMPRE** se tiene que ejecutar antes de deploy

¿Por qué? Porque en producción la imagen se ejecuta en un servidor que **no tiene tu código fuente en disco**. El volumen de desarrollo es un atajo local — el build real empaqueta todo dentro de la imagen.

```
Desarrollo:
  imagen (dependencias) + volumen (tu código) → funciona localmente

Producción:
  imagen (dependencias + código) → funciona en cualquier servidor
```

El flujo correcto es:

```bash
# Desarrollo: iterar rápido con volúmenes
docker run --rm -v "$(pwd)":/app dev-app

# Cuando el código está listo: rebuild y test SIN volumen
docker build -t dev-app .
docker run --rm dev-app            # sin volumen — todo dentro de la imagen

# Si funciona sin volumen, está listo para deploy
```

:::exercise{title="Ciclo de desarrollo con volúmenes" difficulty="2"}

**ASEGURATE de estar en `exercises/lab3_dev_workflow/`.**

Haz todo manualmente:

1. Lee los 3 archivos (`main.py`, `requirements.txt`, `Dockerfile`). **Entiende qué hace cada uno.**

2. Haz el build inicial:

```bash
docker build -t dev-app .
```

3. Ejecuta **sin** volumen. Anota qué imprime.

```bash
docker run --rm dev-app
```

4. **Abre `main.py` con tu editor** y cambia algo (por ejemplo, cambia la URL o agrega un print). **NO toques `requirements.txt`.**

5. Ejecuta **sin** volumen de nuevo:

```bash
docker run --rm dev-app
```

¿Imprime tu cambio? ¿Por qué no?

6. Ejecuta **con** volumen:

```bash
docker run --rm -v "$(pwd)":/app dev-app
```

¿Ahora sí imprime lo nuevo? ¿Por qué?

7. Ejecuta **sin** volumen otra vez:

```bash
docker run --rm dev-app
```

¿Qué versión de `main.py` ejecuta? ¿La vieja o la nueva? ¿Por qué?

8. Haz rebuild y ejecuta sin volumen. ¿Ahora sí tiene el código nuevo?

```bash
docker build -t dev-app .
docker run --rm dev-app
```

:::

:::exercise{title="Qué vive dónde" difficulty="2"}

Este ejercicio verifica que entiendas qué le pasa a cada capa. **RESPONDE ANTES DE EJECUTAR** — y luego verifica.

**Navega al directorio:**

```bash
cd exercises/lab4_donde_vive/
```

Inspecciona los archivos:

```bash
cat app.py       # imprime "original"
cat Dockerfile   # FROM python:3.11, WORKDIR /app, COPY . ., CMD python app.py
```

**Construye la imagen:**

```bash
docker build -t donde-app .
```

**Ahora PREDICE qué imprime cada comando ANTES de ejecutarlo:**

1. `docker run --rm donde-app` → ¿qué imprime?

2. **Abre `app.py` con tu editor** y cámbialo a `print("modificado")`. Guarda. Ejecuta: `docker run --rm donde-app` → ¿qué imprime? (la imagen NO se reconstruyó)

3. `docker run --rm -v "$(pwd)":/app donde-app` → ¿qué imprime?

4. `docker run --rm donde-app` → ¿qué imprime? (sin volumen de nuevo)

5. `docker build -t donde-app . && docker run --rm donde-app` → ¿qué imprime?

**Respuestas**: 1=original, 2=original, 3=modificado, 4=original, 5=modificado.

Si acertaste las 5: **entendiste volúmenes**.

:::

:::prompt{title="Debuggear un proyecto con volúmenes" for="ChatGPT/Claude"}

Tengo un proyecto con este Dockerfile:

```
[pega tu Dockerfile]
```

Mi estructura de directorios es:

```
[pega la salida de tree o ls -R]
```

El error que obtengo al ejecutar es:

```
[pega el error]
```

Ayúdame a:
1. Diagnosticar si el problema es del código o de la imagen
2. Diseñar un comando `docker run -v` para debuggear montando mi código
3. Verificar qué archivos ve el contenedor vs cuáles tengo en mi host

:::
