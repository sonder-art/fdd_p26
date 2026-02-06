# Metacaracteres: Los Símbolos Especiales

Los metacaracteres son símbolos que tienen un **significado especial** en regex. NO representan el caracter literal, sino una **instrucción**.

---

## La Regla de Oro: ¿A Qué Aplica?

> **Los cuantificadores (`*`, `+`, `?`, `{}`) SIEMPRE aplican a lo que está INMEDIATAMENTE A SU IZQUIERDA.**

Esta es la regla más importante. Memorízala.

```
a+     →  El + aplica a la "a"
ab+    →  El + aplica a la "b", NO a "ab"
(ab)+  →  El + aplica al grupo "(ab)"
[ab]+  →  El + aplica al conjunto "[ab]"
```

---

## 1. El Punto `.` - Cualquier Caracter

El punto coincide con **cualquier caracter** (excepto salto de línea).

```
.     →  Un caracter cualquiera
..    →  Dos caracteres cualesquiera
a.c   →  "a", luego cualquier caracter, luego "c"
```

### Ejemplos

| Patrón | Texto | ¿Coincide? |
|--------|-------|------------|
| `a.c` | "abc" | ✓ |
| `a.c` | "aXc" | ✓ |
| `a.c` | "a9c" | ✓ |
| `a.c` | "ac" | ✗ (falta un caracter) |
| `a.c` | "abbc" | ✗ (hay dos caracteres) |

### En Terminal

```bash
echo -e "abc\naXc\na9c\nac\nabbc" > punto.txt

grep "a.c" punto.txt
```

**Salida:**
```
abc
aXc
a9c
```

---

## 2. El Asterisco `*` - Cero o Más

El asterisco significa: **"lo que está a mi izquierda puede aparecer 0, 1, 2, 3... o infinitas veces"**.

```
a*    →  "", "a", "aa", "aaa", "aaaa"... (cero o más "a")
```

### ¡Cuidado! Cero También Cuenta

```
Patrón: ab*c
```

| Texto | ¿Coincide? | Explicación |
|-------|------------|-------------|
| "ac" | ✓ | cero "b" |
| "abc" | ✓ | una "b" |
| "abbc" | ✓ | dos "b" |
| "abbbbbc" | ✓ | muchas "b" |

### En Terminal

```bash
echo -e "ac\nabc\nabbc\nabbbbbc" > asterisco.txt

grep "ab*c" asterisco.txt
```

**Salida:**
```
ac
abc
abbc
abbbbbc
```

---

## 3. El Más `+` - Una o Más

El más significa: **"lo que está a mi izquierda debe aparecer AL MENOS una vez"**.

```
a+    →  "a", "aa", "aaa"... (una o más "a", pero NO cero)
```

### Diferencia con `*`

| Patrón | "ac" | "abc" | "abbc" |
|--------|------|-------|--------|
| `ab*c` | ✓ | ✓ | ✓ |
| `ab+c` | ✗ | ✓ | ✓ |

`ab+c` requiere **al menos una "b"**.

### En Terminal (Necesita -E o -P)

```bash
echo -e "ac\nabc\nabbc" > mas.txt

# Con grep extendido
grep -E "ab+c" mas.txt
```

**Salida:**
```
abc
abbc
```

Nota: "ac" NO aparece porque `+` requiere al menos una "b".

---

## 4. El Interrogante `?` - Cero o Uno

El interrogante significa: **"lo que está a mi izquierda es OPCIONAL (puede aparecer 0 o 1 vez)"**.

```
a?    →  "" o "a" (cero o una "a")
```

### Ejemplo: Hacer algo opcional

```
colou?r   →  "color" o "colour"
```

| Texto | ¿Coincide? |
|-------|------------|
| "color" | ✓ (cero "u") |
| "colour" | ✓ (una "u") |
| "colouur" | ✗ (dos "u") |

### En Terminal

```bash
echo -e "color\ncolour\ncolouur" > opcional.txt

grep -E "colou?r" opcional.txt
```

**Salida:**
```
color
colour
```

---

## 5. Resumen Visual: `*`, `+`, `?`

```
PATRÓN: ab*c     (cero o más "b")
        ↑
        aplica a "b"

ac      →  ✓  (0 b)
abc     →  ✓  (1 b)
abbc    →  ✓  (2 b)


PATRÓN: ab+c     (una o más "b")
        ↑
        aplica a "b"

ac      →  ✗  (0 b, necesita al menos 1)
abc     →  ✓  (1 b)
abbc    →  ✓  (2 b)


PATRÓN: ab?c     (cero o una "b")
        ↑
        aplica a "b"

ac      →  ✓  (0 b)
abc     →  ✓  (1 b)
abbc    →  ✗  (2 b, máximo es 1)
```

---

## 6. Anclas: `^` y `$`

Las anclas NO coinciden con caracteres, sino con **posiciones**.

### `^` - Inicio de Línea

```
^Hola    →  "Hola" SOLO si está al inicio de la línea
```

```bash
echo -e "Hola mundo\nmundo Hola\nHola" > anclas.txt

grep "^Hola" anclas.txt
```

**Salida:**
```
Hola mundo
Hola
```

"mundo Hola" NO aparece porque "Hola" no está al inicio.

### `$` - Fin de Línea

```
mundo$   →  "mundo" SOLO si está al final de la línea
```

```bash
grep "mundo$" anclas.txt
```

**Salida:**
```
Hola mundo
```

### Combinar Ambas

```
^Hola$   →  Líneas que son EXACTAMENTE "Hola"
```

```bash
grep "^Hola$" anclas.txt
```

**Salida:**
```
Hola
```

---

## 7. Escape `\` - Quitar Significado Especial

Si quieres buscar un metacaracter **literalmente**, usa `\` antes:

| Quiero buscar | Escribo |
|---------------|---------|
| Un punto `.` | `\.` |
| Un asterisco `*` | `\*` |
| Un signo de interrogación `?` | `\?` |
| Un dólar `$` | `\$` |

### Ejemplo

```bash
echo -e "precio: $100\nprecio: 100" > precios.txt

# Buscar literalmente "$100"
grep '\$100' precios.txt
```

**Salida:**
```
precio: $100
```

---

## Resumen de Metacaracteres Básicos

| Símbolo | Nombre | Significado | Ejemplo |
|---------|--------|-------------|---------|
| `.` | Punto | Cualquier caracter | `a.c` → "abc", "aXc" |
| `*` | Asterisco | Cero o más (del anterior) | `ab*c` → "ac", "abc", "abbc" |
| `+` | Más | Una o más (del anterior) | `ab+c` → "abc", "abbc" |
| `?` | Interrogante | Cero o una (del anterior) | `ab?c` → "ac", "abc" |
| `^` | Circunflejo | Inicio de línea | `^Hola` → "Hola..." |
| `$` | Dólar | Fin de línea | `...mundo$` |
| `\` | Escape | Quitar significado especial | `\.` → punto literal |

---

## Ejercicios

:::exercise{title="Entender cuantificadores" difficulty="2"}

Sin ejecutar, predice qué líneas coinciden:

**Archivo:**
```
a
aa
aaa
ab
aab
aaab
b
ba
```

**Patrones:**
1. `a+`
2. `a*b`
3. `^a+$`
4. `a?b`

Después verifica tus respuestas con `grep -E`.

:::

---

## Siguiente: Estructuras

Ahora veremos las estructuras: corchetes `[]`, paréntesis `()` y llaves `{}`. Aquí es donde muchos se confunden, así que iremos paso a paso.
