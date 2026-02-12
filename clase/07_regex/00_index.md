# Módulo 7: Expresiones Regulares (Regex)

{% from "components/pdf.njk" import render as pdf %}

{{ pdf('/07_regex/07 Regex.pdf', 'Presentación: Expresiones Regulares') }}


[📊 Expresiones Regulares](https://docs.google.com/presentation/d/17eFdahNv3JNyM3qiHT8-jc7OSwNsi7dHpjk4pz3zsKw/edit?usp=sharing)

---

## Contenido

1. **[¿Qué es Regex?](./01_que_es_regex.md)**
   - Definición y analogía
   - Cómo lee regex (izquierda a derecha)
   - Para qué sirve
   - Historia breve

2. **[Caracteres Literales](./02_caracteres_literales.md)**
   - Búsqueda exacta
   - Mayúsculas vs minúsculas
   - Espacios y caracteres especiales

3. **[Metacaracteres](./03_metacaracteres.md)**
   - `.` (punto) - cualquier caracter
   - `*`, `+`, `?` - cuantificadores
   - `^`, `$` - anclas
   - **La regla de oro: aplican a la IZQUIERDA**

4. **[Estructuras: [], (), {}](./04_estructuras.md)**
   - `[]` - conjuntos de caracteres
   - `()` - grupos
   - `{}` - repetición exacta
   - **Diferencia entre dentro y fuera**
   - Negación con `[^...]`

5. **[Ejemplos en Terminal](./05_ejemplos_terminal.md)**
   - Comandos `grep` con banderas
   - Patrones útiles
   - Edge cases y errores comunes

---

:::homework{id="7.0" title="Instalar Docker y Podman" due="2026-02-10" points="0"}

**Objetivo:** Tener Docker y Podman instalados y funcionando **SIN usar sudo**.

### 1. Instalar Docker

1. **Instalación:**
   - [https://docs.docker.com/engine/install/](https://docs.docker.com/engine/install/)
   - Busca tu distribución (Ubuntu, Debian, Fedora, etc.) y sigue las instrucciones

2. **Post-instalación (MUY IMPORTANTE):**
   - [https://docs.docker.com/engine/install/linux-postinstall/](https://docs.docker.com/engine/install/linux-postinstall/)
   - Sigue los pasos para **"Manage Docker as a non-root user"**
   - Esto te permite usar Docker **sin sudo**

3. **Verificar instalación:**
   ```bash
   docker --version
   docker run hello-world   # SIN sudo
   ```

### 2. Instalar Podman

1. **Instalación:**
   - [https://podman.io/getting-started/installation](https://podman.io/getting-started/installation)
   - Busca tu distribución y sigue las instrucciones

2. **Post-instalación:**
   - Busca cómo configurar Podman para correr **sin sudo** (rootless)
   - Pista: Podman está diseñado para correr rootless por defecto, pero verifica que funcione

3. **Verificar instalación:**
   ```bash
   podman --version
   podman run hello-world   # SIN sudo
   ```

### Entrega

**Debes poder ejecutar esto SIN sudo:**
```bash
docker run hello-world
podman run hello-world
```

Si te pide `sudo`, no completaste la post-instalación correctamente.

**Nota:** Esta tarea no tiene puntos pero es **requisito** para las siguientes clases.

:::

---

:::homework{id="7.1" title="RegexGolf - Niveles básicos" due="2026-02-10" points="20"}

**URL:** [https://alf.nu/RegexGolf?world=regex&level=r00](https://alf.nu/RegexGolf?world=regex&level=r00)

### Objetivo:
Completar los siguientes niveles de RegexGolf:
- **Warmup**
- **Anchors**
- **It never ends**
- **Backrefs**

### Sobre usar LLMs (ChatGPT, Claude, etc.)

**De preferencia NO uses LLMs.** Pero si decides usarlos:

1. **NO pidas la respuesta directamente** ❌
   - MAL: "Dame el regex para el nivel Warmup de RegexGolf"
   - MAL: "Regex que matchee foo, bar, baz pero no abc, def"

2. **SÍ puedes usarlo para aprender conceptos** ✓
   - BIEN: "Explícame qué hace el metacaracter `^` en regex"
   - BIEN: "¿Cuál es la diferencia entre `*` y `+` en expresiones regulares?"
   - BIEN: "Tengo este regex `a.*b` y no entiendo por qué matchea todo, explícame"

3. **La idea es PENSAR y llegar al regex tú mismo:**
   - Analiza qué tienen en común los strings que quieres matchear
   - Piensa qué patrón los distingue de los que NO quieres matchear
   - Escribe el regex paso a paso, probando en [regex101.com](https://regex101.com/)
   - Si usas un LLM, explícale qué quieres lograr y pídele que te guíe, no que te dé la respuesta

### Entrega:

1. **En GitHub (via PR):**
   - Crear archivo: `estudiantes/{tu_usuario}/regex/regex_golf.txt`
   - Abrir un Pull Request con tu solución

2. **Contenido del archivo `regex_golf.txt`:**

```
=== NIVEL: [nombre del nivel] ===
Regex usado: [tu regex]
Explicación: [qué hace cada parte del regex]
Proceso de pensamiento: [cómo llegaste a ese regex]

[repetir para cada nivel]
```

3. **Evidencia fotográfica:**
   - Captura de pantalla mostrando que completaste cada nivel
   - Incluir las capturas en tu PR o en el directorio

4. **En Canvas:**
   - Subir el link del PR
   - Subir el link del directorio en GitHub (`estudiantes/{tu_usuario}/regex/`)
   - **Ambos links son requeridos**

### REGLA: Explica tu regex Y tu proceso
No solo pongas el regex, explica qué hace y cómo llegaste a él. Por ejemplo:
```
Regex usado: ^foo
Explicación: ^ ancla al inicio de la línea, foo busca literalmente "foo"
Proceso: Vi que todos los strings que quiero matchear empiezan con "foo", 
         así que usé ^ para anclar al inicio.
```

:::

---

:::homework{id="7.2" title="Bandit OverTheWire - Niveles 6-10" due="2026-02-17" points="20"}

**URL:** [https://overthewire.org/wargames/bandit/](https://overthewire.org/wargames/bandit/)

### Objetivo:
Completar los niveles del **6 al 10** de Bandit (tener la contraseña para entrar al nivel 11).

### REGLA PRINCIPAL: NO USES LLMs (ChatGPT, Claude, Gemini, etc.)

Esta tarea es para que aprendas a buscar información **a la antigua**. Queremos que:

1. **Pienses** qué necesitas hacer
2. **Busques** cómo funciona el comando (no la solución)
3. **Experimentes** en la terminal

### Recursos permitidos:

| Recurso | Para qué usarlo |
|---------|-----------------|
| `man comando` | Manual del sistema en tu terminal |
| `comando --help` | Ayuda rápida |
| **Google** | Buscar "how to [cosa] in linux", NO "bandit level X solution" |
| **Stack Overflow** | Buscar cómo funcionan comandos |
| **explainshell.com** | Entender partes de un comando |
| **tldr.sh** | Ejemplos prácticos de comandos |
| **Las pistas de Bandit** | Cada nivel dice "Commands you may need" |

### NO permitido:

- ChatGPT, Claude, Gemini, Copilot, o cualquier LLM
- Buscar "bandit level 7 solution", "bandit walkthrough", etc.
- Copiar soluciones de otros

### Ejemplo de búsqueda correcta:

**MAL:** "bandit level 7 solution" ❌

**BIEN:** "linux how to search for a string in a file" ✓

**MAL:** "overthewire bandit walkthrough" ❌

**BIEN:** "man grep" en tu terminal ✓

### Entrega:

1. **En GitHub (via PR):**
   - Crear archivo: `estudiantes/{tu_usuario}/bandit/bandit2.txt`
   - Abrir un Pull Request con tu solución

2. **Contenido del archivo `bandit2.txt`:**

```
=== NIVEL X ===
1. ¿Qué necesito hacer? (en tus palabras)
2. ¿Qué comando(s) creo que necesito?
3. ¿Dónde busqué información? (link o man page)
4. Comandos que ejecuté:
   $ comando1
   $ comando2
5. ¿Funcionó? Si no, ¿qué ajusté?

[repetir para niveles 6-10]
```

**Screenshot** mostrando que entraste al nivel 11.

**Tu nombre y clave** en el archivo.

3. **En Canvas:**
   - Subir el link del PR
   - Subir el link del directorio en GitHub (`estudiantes/{tu_usuario}/bandit/`)
   - **Ambos links son requeridos**

> **Nota:** La siguiente clase algunos pasarán a explicar cómo resolvieron un nivel. Debes poder explicar tu proceso de pensamiento, no solo los comandos.

:::

---

## Recursos

- [Regex101](https://regex101.com/) - Probar y debugear regex
- [RegexGolf](https://alf.nu/RegexGolf) - Practicar regex de forma divertida
- [RegExr](https://regexr.com/) - Otra herramienta para probar regex
- [Cheatsheet de Regex](https://quickref.me/regex) - Referencia rápida
