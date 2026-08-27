# I/O y Encodings

Leer datos parece trivial hasta que el archivo tiene tildes convertidas en `Ã©`, o un CSV que pandas lee perfectamente en tu maquina y explota en produccion. Este capitulo explica por que ocurre eso a nivel de bits, y como resolverlo.

## Que es un encoding — el problema fundamental

Una computadora no almacena texto. Almacena **bytes**: secuencias de 8 bits, cada uno con un valor entre 0 y 255. El texto es una abstraccion que existe solo en la mente del programador y en las convenciones que definen como interpretar esos bytes.

Un **encoding** (codificacion de caracteres) es una tabla de correspondencia bidireccional:

```
byte(s)  ←→  caracter
```

Sin esta tabla, una secuencia de bytes es ambigua. El byte `0xE9` podria ser `é` (en latin-1), parte del caracter `é` (en utf-8, donde necesita dos bytes), o cualquier otra cosa dependiendo de la convencion usada al escribir el archivo.

El problema central es que **el archivo no te dice que encoding usa**. Esa informacion esta fuera del archivo, en los metadatos, la documentacion, o — con demasiada frecuencia — en ningun lado.

## ASCII: el origen

En 1963, el **American Standard Code for Information Interchange** (ASCII) establecio la primera codificacion ampliamente adoptada. Usa 7 bits, cubriendo 128 caracteres:

```
0–31:   caracteres de control (newline, tab, null, ...)
32–126: caracteres imprimibles (letras, digitos, puntuacion)
127:    DEL
```

ASCII es suficiente para el ingles. No tiene tildes, ñ, ni ningun caracter fuera del alfabeto ingles basico. Esto fue un problema desde el primer dia para cualquier idioma que no fuera ingles.

El 8vo bit (bit 7) quedo sin uso, y ahi empezo el caos.

## La era del caos: encodings de 8 bits

Durante las decadas de 1970–1990, distintos fabricantes y organismos usaron el bit extra (valores 128–255) para extender ASCII con los caracteres que necesitaban:

| Encoding | Nombre formal | Uso |
|---|---|---|
| `latin-1` | ISO-8859-1 | Europa occidental (frances, espanol, aleman, ...) |
| `latin-2` | ISO-8859-2 | Europa central y oriental |
| `cp1252` | Windows-1252 | Windows occidental — similar a latin-1 con diferencias en 128–159 |
| `cp1251` | Windows-1251 | Windows cirilico (ruso) |
| `koi8-r` | KOI8-R | Unix ruso |
| `shift-jis`| Shift JIS | Japones |

**El problema**: estos encodings son incompatibles entre si. El byte `0x80` es:
- `€` (euro) en cp1252
- Un caracter de control sin significado en latin-1
- `Ђ` (letra cirilica) en cp1251

Un archivo escrito en cp1252 leido como latin-1 produce texto corrompido. Esto es **mojibake**.

### latin-1 vs cp1252 — la trampa frecuente

Son casi identicos (mismos 256 caracteres para los primeros 128 y los ultimos 96), pero difieren en el rango 0x80–0x9F:

- latin-1: ese rango son caracteres de control sin representacion visible
- cp1252: ese rango incluye caracteres utiles como `€`, `'`, `'`, `"`, `"`, `–`, `—`

Cuando un archivo de Word o Excel generado en Windows tiene comillas tipograficas (`"texto"`) y lo lees como latin-1, esos caracteres se pierden o corrompen. La diferencia importa en textos reales.

## Unicode: la solucion universal

En 1991, el **Unicode Consortium** inicio el proyecto de asignar un numero unico — llamado **code point** — a cada caracter de todos los sistemas de escritura del mundo.

Un code point se escribe como `U+XXXX` en hexadecimal:

```
U+0041  →  A  (letra latina mayuscula A)
U+00E9  →  é  (letra e con acento agudo)
U+00F1  →  ñ  (ene con tilde)
U+20AC  →  €  (signo euro)
U+1F600 →  😀 (emoji cara sonriente)
U+4E2D  →  中 (caracter chino, "medio/China")
```

Unicode actualmente define mas de 149,000 caracteres en 154 sistemas de escritura. El espacio de code points va de U+0000 a U+10FFFF (1,114,112 posibles valores).

**Importante**: Unicode es el estandar de *que numero corresponde a cada caracter*. No especifica como almacenar esos numeros en bytes. Para eso existen los **Unicode Transfer Formats (UTF)**.

## UTF-8: como funciona internamente

UTF-8 es el encoding dominante en la web y en ciencia de datos. Es **variable-length**: usa entre 1 y 4 bytes segun el code point:

| Rango de code points | Bytes usados | Patron de bits |
|---|---|---|
| U+0000 – U+007F | 1 byte | `0xxxxxxx` |
| U+0080 – U+07FF | 2 bytes | `110xxxxx 10xxxxxx` |
| U+0800 – U+FFFF | 3 bytes | `1110xxxx 10xxxxxx 10xxxxxx` |
| U+10000 – U+10FFFF | 4 bytes | `11110xxx 10xxxxxx 10xxxxxx 10xxxxxx` |

Los `x` son los bits del code point, distribuidos en los bytes.

### Ejemplo concreto: la letra `é`

El code point de `é` es U+00E9 = decimal 233 = binario `11101001`.

Cae en el rango U+0080–U+07FF, por lo tanto usa **2 bytes**. El patron es `110xxxxx 10xxxxxx`.

```
U+00E9  =  0b 000 11101 001
                 ↑↑↑↑↑ ↑↑↑
Patron:  110 00011  10 101001
         ↓↓↓↓↓↓↓↓  ↓↓↓↓↓↓↓↓
Bytes:     0xC3        0xA9
```

Entonces `é` en UTF-8 son los bytes `0xC3 0xA9`.

En latin-1, `é` es el byte `0xE9` (un solo byte, el valor decimal del code point directamente, porque latin-1 mapea U+0000–U+00FF de forma directa).

### Compatibilidad hacia atras con ASCII

UTF-8 fue disenado deliberadamente para ser compatible con ASCII: los primeros 128 code points (U+0000–U+007F) se codifican con un solo byte identico al valor ASCII. Un archivo de texto ASCII puro es valido UTF-8 sin modificacion. Esta fue la decision de diseno clave para su adopcion masiva.

## Como ocurre el mojibake

Mojibake (del japones: 文字化け, "transformacion de caracteres") ocurre cuando un archivo escrito con un encoding es leido con otro.

### El ciclo encode-decode

En Python, el proceso de texto a bytes y viceversa es explicito:

```
str  ──[encode(encoding)]──►  bytes
bytes ──[decode(encoding)]──►  str
```

```python
texto = "México"
# Escribir (encode)
bytes_utf8   = texto.encode("utf-8")    # b'M\xc3\xa9xico'
bytes_latin1 = texto.encode("latin-1")  # b'M\xe9xico'

# Leer correcto
bytes_utf8.decode("utf-8")   # 'México' ✓
bytes_latin1.decode("latin-1")  # 'México' ✓

# Leer con encoding incorrecto → mojibake
bytes_latin1.decode("utf-8")  # UnicodeDecodeError: byte 0xe9 is not valid UTF-8
bytes_utf8.decode("latin-1")  # 'MÃ©xico' ✗  — no error, pero texto corrupto
```

El segundo caso es mas peligroso: latin-1 acepta cualquier byte (todos los 256 valores tienen asignacion), por lo que nunca lanza error. El mojibake pasa silenciosamente.

### Por que `0xC3 0xA9` → `Ã©`

Cuando lees UTF-8 como latin-1:
- `0xC3` en latin-1 es `Ã`
- `0xA9` en latin-1 es `©`

Por eso `é` (UTF-8) leido como latin-1 produce `Ã©`. Es exactamente lo que produce el codigo de arriba. Si ves este patron en tus datos, el archivo es UTF-8 siendo leido como latin-1 o ASCII.

Otros patrones comunes de mojibake:

| Caracter original | UTF-8 bytes | Leido como latin-1 |
|---|---|---|
| `é` (U+00E9) | `C3 A9` | `Ã©` |
| `ñ` (U+00F1) | `C3 B1` | `Ã±` |
| `á` (U+00E1) | `C3 A1` | `Ã¡` |
| `ó` (U+00F3) | `C3 B3` | `Ã³` |
| `'` (U+2019) | `E2 80 99` | `â€™` |
| `"` (U+201C) | `E2 80 9C` | `â€œ` |

Ver `Ã` seguido de otro caracter es el sello del mojibake UTF-8→latin-1.

## BOM (Byte Order Mark)

El BOM es una secuencia de bytes al inicio de un archivo que indica el encoding y, en el caso de UTF-16/32, el orden de los bytes (big-endian o little-endian):

| Encoding | BOM (hex) |
|---|---|
| UTF-8 | `EF BB BF` |
| UTF-16 LE | `FF FE` |
| UTF-16 BE | `FE FF` |
| UTF-32 LE | `FF FE 00 00` |

El BOM de UTF-8 (`EF BB BF`) es el mas problematico en la practica. Microsoft Word y Excel a menudo generan archivos UTF-8 con BOM (llamados "utf-8-sig" en Python). Si tu parser no lo espera, el BOM aparece como tres caracteres invisibles al inicio del archivo que corrompen el nombre de la primera columna:

```python
# Archivo con BOM → primera columna tiene '\ufeff' invisible al inicio
df = pd.read_csv(archivo_con_bom, encoding="utf-8")
df.columns[0]  # '\ufeffnombre' en lugar de 'nombre'

# Solucion:
df = pd.read_csv(archivo_con_bom, encoding="utf-8-sig")
df.columns[0]  # 'nombre' ✓
```

## Deteccion automatica de encoding

Como el archivo no declara su encoding, a veces necesitas detectarlo. Las dos librerias principales son `chardet` y `charset-normalizer`:

```python
import chardet

with open("archivo.csv", "rb") as f:  # abrir en modo binario
    resultado = chardet.detect(f.read())

# {'encoding': 'ISO-8859-1', 'confidence': 0.73, 'language': ''}
```

**Limitaciones importantes**:
- La deteccion es estadistica, no determinista. Una confianza de 0.73 significa que puede estar equivocado.
- Archivos cortos o con pocos caracteres no-ASCII son dificiles de clasificar.
- latin-1 y cp1252 son casi indistinguibles estadisticamente.
- La deteccion es solo un punto de partida — siempre verifica que el resultado tiene sentido.

## Jerarquia de encodings para datos en Mexico/LATAM

En la practica, los datos que vas a encontrar en Mexico vienen de:

1. **APIs modernas, archivos exportados de Python/R** → UTF-8 (casi siempre)
2. **Excel/CSV de Windows** → cp1252 o UTF-8-BOM
3. **Sistemas legacy, bases de datos antiguas** → latin-1 o cp1252
4. **INEGI, SAT, gobierno federal** → latin-1 o cp1252 (frecuente)
5. **SAP, Oracle exportados** → a veces UTF-16 o encodings propietarios

La heuristica practica: si ves tildes y enes corruptas al leer como UTF-8, prueba `latin-1` primero. Si sigue mal, prueba `cp1252`.

## Buenas practicas

1. **Siempre guarda y transmite datos en UTF-8**. Es el estandar moderno y pandas, Python, y la web lo asumen por default.

2. **Al leer datos externos, especifica el encoding explicitamente** en lugar de depender de la deteccion automatica.

3. **Lee en modo binario (`"rb"`) para diagnosticar**. Los primeros bytes del archivo te dicen mucho antes de intentar decodificarlo.

4. **Verifica con caracteres no-ASCII**. Un archivo sin tildes o enes se lee igual en cualquier encoding compatible con ASCII. El problema aparece solo cuando hay caracteres fuera del rango 0–127.

5. **Usa `errors="replace"` solo para diagnostico**, no para produccion. Reemplaza caracteres invalidos con `?` pero oculta el problema real.

## El notebook

El notebook cubre todos estos conceptos con codigo ejecutable: ejemplos de mojibake a nivel de bytes, deteccion con chardet, lectura de CSVs con distintos encodings, y un ejercicio integrador.

[![Open in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/sonder-art/fdd_p26/blob/main/clase/13_pandas_io/code/01_io_y_encodings.ipynb)

:::exercise{title="Autopsia de un mojibake" difficulty="2"}
Abre cualquier CSV con datos en espanol que tengas guardado. Leelo primero con `encoding="utf-8"`, luego con `encoding="latin-1"`, luego con `encoding="cp1252"`. Compara los resultados en columnas con texto (nombres, ciudades, descripciones). Identifica cual encoding es el correcto y explica como lo determinaste.
:::
