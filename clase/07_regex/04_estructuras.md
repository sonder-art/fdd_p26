# Estructuras: [], (), {}

Esta es la sección más importante para evitar confusiones. Vamos a ver cada estructura por separado y luego cómo interactúan con los cuantificadores.

---

## Regla Fundamental

> **Lo que está DENTRO de una estructura tiene reglas diferentes a lo que está AFUERA.**

```
[abc]    →  Lo de DENTRO define el conjunto
[abc]+   →  El + está AFUERA, aplica al conjunto completo
```

---

# Corchetes `[]` - Conjunto de Caracteres

Los corchetes definen un **conjunto**: "cualquiera de estos caracteres".

## Concepto Básico

```
[abc]    →  UNA sola posición que puede ser "a", "b" o "c"
```

**Importante:** `[abc]` coincide con **UN solo caracter**, no con "abc".

| Patrón | Texto | ¿Coincide? |
|--------|-------|------------|
| `[abc]` | "a" | ✓ |
| `[abc]` | "b" | ✓ |
| `[abc]` | "d" | ✗ |
| `[abc]` | "abc" | ✓ (encuentra "a") |

### En Terminal

```bash
echo -e "a\nb\nc\nd\nabc" > conjunto.txt

grep "[abc]" conjunto.txt
```

**Salida:**
```
a
b
c
abc
```

---

## Rangos Dentro de Corchetes

Puedes usar `-` para definir rangos:

```
[a-z]     →  Cualquier letra minúscula (a hasta z)
[A-Z]     →  Cualquier letra mayúscula
[0-9]     →  Cualquier dígito
[a-zA-Z]  →  Cualquier letra (mayúscula o minúscula)
[a-z0-9]  →  Letra minúscula o dígito
```

### Ejemplo

```bash
echo -e "a\nZ\n5\n@" > rangos.txt

# Solo letras minúsculas
grep "[a-z]" rangos.txt
```

**Salida:**
```
a
```

---

## Negación: `[^...]` - Todo EXCEPTO

Cuando `^` está **dentro de los corchetes y al inicio**, significa "NO estos caracteres":

```
[^abc]    →  Cualquier caracter EXCEPTO a, b, c
[^0-9]    →  Cualquier caracter que NO sea dígito
```

### ¡CUIDADO! Dos significados de `^`

| Contexto | Símbolo | Significado |
|----------|---------|-------------|
| Fuera de `[]` | `^Hola` | Inicio de línea |
| Dentro de `[]` al inicio | `[^abc]` | Negación (NO estos) |
| Dentro de `[]` no al inicio | `[a^b]` | Literal (el caracter ^) |

### Ejemplo de Negación

```bash
echo -e "a\nb\nc\nd\n1\n2" > negacion.txt

# Todo EXCEPTO a, b, c
grep "[^abc]" negacion.txt
```

**Salida:**
```
d
1
2
```

---

## IMPORTANTE: Metacaracteres DENTRO de Corchetes

**Dentro de `[]`, la mayoría de metacaracteres PIERDEN su significado especial.**

| Dentro de `[]` | Significado |
|----------------|-------------|
| `[.]` | Un punto literal, NO "cualquier caracter" |
| `[*]` | Un asterisco literal |
| `[+]` | Un signo más literal |
| `[?]` | Un interrogante literal |

### Ejemplo

```bash
echo -e "a.b\na*b\na+b\naxb" > especiales.txt

# Buscar punto, asterisco o más LITERALES
grep "[.+*]" especiales.txt
```

**Salida:**
```
a.b
a*b
a+b
```

"axb" no aparece porque `x` no está en el conjunto `[.+*]`.

---

## Cuantificadores FUERA de Corchetes

Cuando pones un cuantificador DESPUÉS de `[]`, aplica al **conjunto completo**:

```
[abc]+    →  Una o más ocurrencias de (a, b, o c)
[0-9]*    →  Cero o más dígitos
[a-z]?    →  Cero o una letra minúscula
```

### Ejemplo Visual

```
PATRÓN: [abc]+

¿Qué significa?
- [abc]  = UN caracter que sea a, b, o c
- +      = una o más veces

Resultado: "a", "aa", "ab", "abc", "cba", "aaabbbccc"...
```

### En Terminal

```bash
echo -e "a\nab\nabc\nabcd\nxyz" > cuantificador_conjunto.txt

grep -E "^[abc]+$" cuantificador_conjunto.txt
```

**Salida:**
```
a
ab
abc
```

"abcd" no aparece porque `d` no está en `[abc]`.
"xyz" no aparece porque ninguna letra está en `[abc]`.

---

# Llaves `{}` - Repetición Exacta

Las llaves especifican **cuántas veces exactamente** se repite algo.

## Formas de Uso

```
{n}      →  Exactamente n veces
{n,}     →  Al menos n veces
{n,m}    →  Entre n y m veces
```

## Ejemplos

```
a{3}     →  Exactamente "aaa"
a{2,}    →  "aa", "aaa", "aaaa"... (2 o más)
a{2,4}   →  "aa", "aaa", "aaaa" (entre 2 y 4)
```

### En Terminal

```bash
echo -e "a\naa\naaa\naaaa\naaaaa" > repeticion.txt

# Exactamente 3 "a"
grep -E "^a{3}$" repeticion.txt
```

**Salida:**
```
aaa
```

### Combinado con Conjuntos

```
[0-9]{3}     →  Exactamente 3 dígitos
[a-z]{2,5}   →  Entre 2 y 5 letras minúsculas
```

```bash
echo -e "12\n123\n1234\n12345\n123456" > digitos.txt

# Exactamente 3 dígitos
grep -E "^[0-9]{3}$" digitos.txt
```

**Salida:**
```
123
```

---

# Paréntesis `()` - Agrupación

Los paréntesis **agrupan** elementos para tratarlos como una unidad.

## ¿Para Qué Sirven?

1. **Aplicar cuantificadores a grupos**
2. **Crear alternativas**
3. **Capturar para uso posterior**

## Aplicar Cuantificadores a Grupos

Sin paréntesis:
```
ab+      →  "a" seguido de una o más "b" → "ab", "abb", "abbb"
```

Con paréntesis:
```
(ab)+    →  "ab" una o más veces → "ab", "abab", "ababab"
```

### Ejemplo Visual

```
PATRÓN: ab+
        ↑
        El + aplica SOLO a "b"

"ab"    → ✓
"abb"   → ✓
"abab"  → ✓ (encuentra "ab")


PATRÓN: (ab)+
         ↑
         El + aplica a TODO "(ab)"

"ab"    → ✓
"abb"   → ✗ (no termina con "ab" repetido)
"abab"  → ✓
```

### En Terminal

```bash
echo -e "ab\nabb\nabab\nababab" > grupos.txt

# Sin grupo: una o más "b"
grep -E "^ab+$" grupos.txt
```

**Salida:**
```
ab
abb
```

```bash
# Con grupo: "ab" una o más veces
grep -E "^(ab)+$" grupos.txt
```

**Salida:**
```
ab
abab
ababab
```

---

## Alternativas con `|` (OR)

El pipe `|` dentro de paréntesis significa "esto O aquello":

```
(gato|perro)    →  "gato" o "perro"
(jpg|png|gif)   →  "jpg" o "png" o "gif"
```

### Ejemplo

```bash
echo -e "gato\nperro\npájaro\ngatos\nperros" > mascotas.txt

grep -E "(gato|perro)" mascotas.txt
```

**Salida:**
```
gato
perro
gatos
perros
```

---

# Comparación: `[]` vs `()`

Esta es la confusión más común. Veamos la diferencia:

| Estructura | Significado | Ejemplo |
|------------|-------------|---------|
| `[abc]` | UN caracter: a, b, O c | `[abc]` en "cat" → "c" |
| `(abc)` | La secuencia "abc" exacta | `(abc)` en "cat" → no coincide |
| `[abc]+` | Uno o más de a, b, c | "abc", "aaa", "cba" |
| `(abc)+` | "abc" una o más veces | "abc", "abcabc" |

### Ejemplo Comparativo

```bash
echo -e "abc\ncba\naaa\nabcabc\naabbcc" > comparacion.txt

# [abc]+ → cualquier combinación de a, b, c
grep -E "^[abc]+$" comparacion.txt
```

**Salida:**
```
abc
cba
aaa
abcabc
aabbcc
```

```bash
# (abc)+ → secuencia "abc" repetida
grep -E "^(abc)+$" comparacion.txt
```

**Salida:**
```
abc
abcabc
```

---

# Resumen de Estructuras

| Estructura | Significado | Cuantificador Aplica A |
|------------|-------------|------------------------|
| `[abc]` | Conjunto: a, b, o c | Un caracter del conjunto |
| `[^abc]` | Negación: NO a, b, c | Un caracter que NO esté |
| `[a-z]` | Rango: a hasta z | Un caracter del rango |
| `{n}` | Repetir n veces | Lo de la izquierda |
| `{n,m}` | Repetir n a m veces | Lo de la izquierda |
| `(abc)` | Grupo: "abc" junto | Todo el grupo |
| `(a\|b)` | Alternativa: a O b | La opción que coincida |

---

# Tabla de Dónde Aplican los Símbolos

| Símbolo | Fuera de `[]` | Dentro de `[]` |
|---------|---------------|----------------|
| `.` | Cualquier caracter | Punto literal |
| `*` | Cero o más | Asterisco literal |
| `+` | Una o más | Más literal |
| `?` | Cero o una | Interrogante literal |
| `^` | Inicio de línea | Negación (si está al inicio) |
| `$` | Fin de línea | Dólar literal |
| `\|` | OR (alternativa) | Pipe literal |

---

## Ejercicios

:::exercise{title="Distinguir estructuras" difficulty="2"}

Predice qué coincide con cada patrón:

**Texto de prueba:**
```
ab
aabb
abab
abc
cab
12
123
1234
```

**Patrones:**
1. `[ab]+` vs `(ab)+`
2. `[0-9]{3}`
3. `[abc]{2}`
4. `^[0-9]+$`

:::

:::exercise{title="Construir patrones" difficulty="2"}

Escribe el regex para:

1. Exactamente 4 dígitos (como un PIN)
2. Una o más vocales
3. "hola" o "adios"
4. Cualquier caracter que NO sea vocal

:::

---

## Siguiente: Ejemplos Prácticos

Ahora veremos ejemplos prácticos combinando todo lo aprendido.
