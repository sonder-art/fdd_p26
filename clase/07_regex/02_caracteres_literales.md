# Caracteres Literales

## ¿Qué es un Caracter Literal?

Un **caracter literal** es simplemente una letra, número o símbolo que representa **exactamente eso mismo**.

```
Patrón: a     →  Busca la letra "a"
Patrón: hola  →  Busca la palabra "hola"
Patrón: 123   →  Busca el número "123"
```

No hay magia aquí. Si escribes `gato`, regex busca exactamente la secuencia `g`, `a`, `t`, `o`.

---

## Ejemplos en Terminal

### Ejemplo 1: Buscar una palabra

```bash
# Crear archivo de prueba
echo -e "El gato duerme\nEl perro ladra\nEl gato come" > animales.txt

# Buscar "gato"
grep "gato" animales.txt
```

**Salida:**
```
El gato duerme
El gato come
```

### Ejemplo 2: Buscar parte de una palabra

```bash
echo -e "programador\nprograma\nprogramacion" > palabras.txt

# Buscar "programa"
grep "programa" palabras.txt
```

**Salida:**
```
programador    ← contiene "programa"
programa       ← es exactamente "programa"
programacion   ← contiene "programa"
```

**Importante:** `grep` encuentra coincidencias **parciales**. "programa" está dentro de "programador".

---

## Mayúsculas y Minúsculas IMPORTAN

Regex es **case-sensitive** (distingue mayúsculas de minúsculas) por defecto.

```bash
echo -e "Hola\nhola\nHOLA" > saludos.txt

grep "hola" saludos.txt
```

**Salida:**
```
hola
```

Solo encuentra "hola" en minúsculas, no "Hola" ni "HOLA".

### Ignorar Mayúsculas/Minúsculas

Usa la bandera `-i`:

```bash
grep -i "hola" saludos.txt
```

**Salida:**
```
Hola
hola
HOLA
```

---

## Espacios También Son Literales

Los espacios son caracteres como cualquier otro.

```bash
echo -e "hola mundo\nholamundo\nhola  mundo" > espacios.txt

grep "hola mundo" espacios.txt
```

**Salida:**
```
hola mundo
```

No encuentra "holamundo" (sin espacio) ni "hola  mundo" (dos espacios).

---

## ¿Qué Pasa Si Busco Algo Que No Existe?

Si el patrón no se encuentra, `grep` no muestra nada y termina silenciosamente.

```bash
grep "elefante" animales.txt
# No muestra nada - no hay elefantes en el archivo
```

---

## Caracteres Literales vs Metacaracteres

Hay ciertos caracteres que tienen **significado especial** en regex. A estos les llamamos **metacaracteres**:

```
.  *  +  ?  ^  $  [  ]  (  )  {  }  |  \
```

Si quieres buscar estos caracteres **literalmente**, debes "escaparlos" con `\`.

### Ejemplo: Buscar un Punto Literal

```bash
echo -e "hola.txt\nhola txt\nholatxt" > archivos.txt

# MAL: El punto tiene significado especial
grep "hola.txt" archivos.txt
# Esto encuentra más de lo que queremos...

# BIEN: Escapar el punto
grep "hola\.txt" archivos.txt
```

**Importante:** Veremos esto en detalle en la siguiente sección. Por ahora, recuerda que algunos caracteres son "especiales".

---

## Ejercicios Prácticos

:::exercise{title="Buscar literales" difficulty="1"}

1. Crea un archivo `frutas.txt` con:
   ```
   manzana
   pera
   manzana verde
   pera roja
   platano
   ```

2. Usa `grep` para encontrar:
   - Todas las líneas con "manzana"
   - Todas las líneas con "pera"
   - La línea exacta "manzana verde"

3. ¿Qué pasa si buscas "Manzana" con M mayúscula?

:::

---

## Resumen

| Concepto | Ejemplo | Encuentra |
|----------|---------|-----------|
| Literal simple | `gato` | "gato" exactamente |
| Parcial | `gato` en "los gatos" | Sí, encuentra |
| Case-sensitive | `Hola` ≠ `hola` | Son diferentes |
| Espacios | `hola mundo` | Exactamente con 1 espacio |
| Escapar especiales | `\.` | Un punto literal |

---

## Siguiente: Metacaracteres

Ahora que entiendes los caracteres literales, vamos a aprender los **metacaracteres** - los símbolos especiales que le dan superpoderes a regex.
