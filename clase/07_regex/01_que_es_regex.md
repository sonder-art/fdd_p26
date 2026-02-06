# ¿Qué es Regex?

## Definición Simple

**Regex** (expresiones regulares) son **patrones de búsqueda** escritos con un lenguaje especial. Es como darle instrucciones muy precisas a tu computadora sobre qué texto quieres encontrar.

Imagina que tienes un libro de 1000 páginas y quieres encontrar:
- Todos los números de teléfono
- Todas las direcciones de email
- Todas las fechas en formato DD/MM/AAAA

Hacerlo a mano sería imposible. Con regex, escribes **un patrón** y la computadora encuentra **todas las coincidencias** automáticamente.

---

## Analogía: Regex como una Receta de Búsqueda

Piensa en regex como dar instrucciones a un robot que lee texto:

| Instrucción humana | Regex |
|-------------------|-------|
| "Busca la letra a" | `a` |
| "Busca cualquier número" | `[0-9]` |
| "Busca una o más letras" | `[a-z]+` |
| "Busca algo que empiece con Hola" | `^Hola` |

El robot lee tu patrón y luego recorre el texto **de izquierda a derecha**, caracter por caracter, buscando coincidencias.

---

## ¿Cómo Lee Regex? (Izquierda a Derecha)

Esta es la regla más importante para entender regex:

> **Regex se lee y se aplica de IZQUIERDA a DERECHA, caracter por caracter.**

### Ejemplo Visual

Texto: `"Hola mundo"`

Patrón: `Hola`

```
Texto:   H  o  l  a     m  u  n  d  o
         ↓  ↓  ↓  ↓
Patrón:  H  o  l  a
         ✓  ✓  ✓  ✓  → ¡Coincidencia encontrada!
```

El regex compara:
1. ¿`H` del texto coincide con `H` del patrón? ✓
2. ¿`o` del texto coincide con `o` del patrón? ✓
3. ¿`l` del texto coincide con `l` del patrón? ✓
4. ¿`a` del texto coincide con `a` del patrón? ✓

¡Todas coinciden! Se encontró "Hola".

---

## El Motor de Regex: Paso a Paso

Cuando escribes un regex, internamente pasa esto:

```
Texto: "gato perro gato"
Patrón: "gato"

Posición 0: g-a-t-o → ¿coincide con "gato"? ✓ MATCH en posición 0-3
Posición 1: a-t-o-  → ¿coincide con "gato"? ✗
Posición 2: t-o- -p → ¿coincide con "gato"? ✗
...
Posición 11: g-a-t-o → ¿coincide con "gato"? ✓ MATCH en posición 11-14
```

El motor prueba el patrón en **cada posición** del texto hasta encontrar todas las coincidencias.

---

## ¿Para Qué Sirve Regex?

### 1. Búsqueda Avanzada
Encontrar patrones específicos en grandes cantidades de texto.

```bash
# Encontrar todas las líneas que contienen "error" en un log
grep "error" archivo.log
```

### 2. Validación de Datos
Verificar que un texto tenga el formato correcto.

```bash
# ¿Es un email válido?
# ¿Tiene formato usuario@dominio.com?
```

### 3. Extracción de Información
Sacar datos específicos de un texto.

```bash
# Extraer todos los números de un archivo
grep -o "[0-9]+" archivo.txt
```

### 4. Buscar y Reemplazar
Cambiar patrones de texto de forma masiva.

```bash
# Reemplazar todas las fechas DD/MM/AAAA por AAAA-MM-DD
```

---

## Regex en la Terminal: `grep`

El comando principal para usar regex en la terminal es `grep`:

```bash
grep "patrón" archivo.txt
```

`grep` busca el patrón y **muestra las líneas completas** donde lo encuentra.

### Ejemplo Básico

```bash
# Crear un archivo de prueba
echo -e "Hola mundo\nAdios mundo\nHola amigo" > prueba.txt

# Buscar líneas que contengan "Hola"
grep "Hola" prueba.txt
```

**Salida:**
```
Hola mundo
Hola amigo
```

---

## Historia Rápida (Para Contexto)

| Década | Evento |
|--------|--------|
| 1940s | Stephen Kleene desarrolla la teoría matemática |
| 1960s | Ken Thompson lo implementa en el editor `ed` de UNIX |
| 1970s | Se crea `grep` (**G**lobal **R**egular **E**xpression **P**rint) |
| 1980s | Perl populariza regex en programación |
| Hoy | Está en todos los lenguajes: Python, JavaScript, etc. |

---

## Resumen

| Concepto | Descripción |
|----------|-------------|
| Regex | Patrón de búsqueda escrito con sintaxis especial |
| Lectura | Siempre de izquierda a derecha |
| `grep` | Comando de terminal para buscar con regex |
| Uso | Buscar, validar, extraer, reemplazar texto |

---

## Siguiente: Caracteres Literales

En la siguiente sección aprenderás a escribir tus primeros patrones usando **caracteres literales** - la forma más básica de regex.
