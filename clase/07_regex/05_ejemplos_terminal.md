# Ejemplos Prácticos en Terminal

Ahora combinemos todo lo aprendido con ejemplos reales usando `grep`.

---

## Repaso: Banderas de grep

| Bandera | Significado |
|---------|-------------|
| `-E` | Regex extendido (permite `+`, `?`, `{}`, `\|`) |
| `-i` | Ignorar mayúsculas/minúsculas |
| `-o` | Mostrar SOLO la parte que coincide |
| `-n` | Mostrar número de línea |
| `-v` | Invertir (mostrar líneas que NO coinciden) |
| `-c` | Contar coincidencias |
| `-P` | Regex de Perl (para `\d`, `\w`, etc.) |

---

## Ejemplo 1: Buscar Números

### Crear archivo de prueba

```bash
cat << 'EOF' > datos.txt
Juan tiene 25 años
Maria tiene 30 años
El precio es $100
Código: ABC123
Teléfono: 555-1234
Sin números aquí
EOF
```

### Encontrar líneas con números

```bash
grep "[0-9]" datos.txt
```

**Salida:**
```
Juan tiene 25 años
Maria tiene 30 años
El precio es $100
Código: ABC123
Teléfono: 555-1234
```

### Extraer SOLO los números

```bash
grep -oE "[0-9]+" datos.txt
```

**Salida:**
```
25
30
100
123
555
1234
```

---

## Ejemplo 2: Validar Formatos

### Archivo de emails

```bash
cat << 'EOF' > emails.txt
juan@gmail.com
maria@empresa.mx
invalido@
@sinusuario.com
test@dominio.co
no-es-email
user.name@sub.domain.org
EOF
```

### Patrón básico de email

```bash
grep -E "^[a-zA-Z0-9.]+@[a-zA-Z0-9.]+\.[a-zA-Z]+$" emails.txt
```

**Salida:**
```
juan@gmail.com
maria@empresa.mx
test@dominio.co
user.name@sub.domain.org
```

### Desglose del patrón

```
^[a-zA-Z0-9.]+  →  Inicio: uno o más caracteres alfanuméricos o punto
@               →  Arroba literal
[a-zA-Z0-9.]+   →  Uno o más caracteres para el dominio
\.              →  Punto literal (escapado)
[a-zA-Z]+$      →  Extensión: una o más letras al final
```

---

## Ejemplo 3: Buscar al Inicio y Final

### Archivo de log

```bash
cat << 'EOF' > log.txt
ERROR: Conexión fallida
INFO: Usuario conectado
ERROR: Timeout
WARNING: Memoria baja
INFO: Proceso completado
ERROR: Archivo no encontrado
EOF
```

### Líneas que empiezan con ERROR

```bash
grep "^ERROR" log.txt
```

**Salida:**
```
ERROR: Conexión fallida
ERROR: Timeout
ERROR: Archivo no encontrado
```

### Líneas que terminan con "ado"

```bash
grep "ado$" log.txt
```

**Salida:**
```
INFO: Usuario conectado
INFO: Proceso completado
```

---

## Ejemplo 4: Alternativas

### Buscar múltiples palabras

```bash
grep -E "(ERROR|WARNING)" log.txt
```

**Salida:**
```
ERROR: Conexión fallida
ERROR: Timeout
WARNING: Memoria baja
ERROR: Archivo no encontrado
```

### Buscar extensiones de archivo

```bash
cat << 'EOF' > archivos.txt
documento.pdf
imagen.jpg
foto.png
video.mp4
script.py
imagen.gif
documento.docx
EOF

grep -E "\.(jpg|png|gif)$" archivos.txt
```

**Salida:**
```
imagen.jpg
foto.png
imagen.gif
```

---

## Ejemplo 5: Repeticiones Exactas

### Códigos postales (5 dígitos)

```bash
cat << 'EOF' > direcciones.txt
Ciudad de México, 01000
Guadalajara, 44100
Monterrey, 64000
Código inválido: 123
Otro inválido: 123456
Puebla, 72000
EOF

grep -E "[0-9]{5}" direcciones.txt
```

**Salida:**
```
Ciudad de México, 01000
Guadalajara, 44100
Monterrey, 64000
Otro inválido: 123456
Puebla, 72000
```

### Solo exactamente 5 dígitos (no 6)

```bash
grep -oE "\b[0-9]{5}\b" direcciones.txt
```

**Salida:**
```
01000
44100
64000
72000
```

(`\b` es "word boundary" - límite de palabra)

---

## Ejemplo 6: Negación

### Encontrar líneas SIN números

```bash
grep -v "[0-9]" datos.txt
```

**Salida:**
```
Sin números aquí
```

### Caracteres que NO son letras

```bash
echo "Hola! ¿Cómo estás? 123" | grep -oE "[^a-zA-ZáéíóúÁÉÍÓÚ ]"
```

**Salida:**
```
!
¿
?
1
2
3
```

---

## Ejemplo 7: Patrones Comunes

### Números de teléfono (formato XXX-XXXX)

```bash
cat << 'EOF' > telefonos.txt
Casa: 555-1234
Oficina: 555-5678
Móvil: 5551234567
Incompleto: 55-123
Correcto: 123-4567
EOF

grep -E "[0-9]{3}-[0-9]{4}" telefonos.txt
```

**Salida:**
```
Casa: 555-1234
Oficina: 555-5678
Correcto: 123-4567
```

### Fechas formato DD/MM/AAAA

```bash
cat << 'EOF' > fechas.txt
Fecha: 25/12/2024
Inválido: 5/1/24
Correcto: 01/01/2025
Mal formato: 2024-12-25
También válido: 31/12/2023
EOF

grep -E "[0-9]{2}/[0-9]{2}/[0-9]{4}" fechas.txt
```

**Salida:**
```
Fecha: 25/12/2024
Correcto: 01/01/2025
También válido: 31/12/2023
```

---

## Ejemplo 8: Combinar con Otros Comandos

### Contar errores en un log

```bash
grep -c "^ERROR" log.txt
```

**Salida:**
```
3
```

### Ver contexto (líneas antes/después)

```bash
# 2 líneas después de cada ERROR
grep -A 2 "^ERROR" log.txt
```

### Pipeline: buscar y procesar

```bash
# Extraer todos los emails y ordenarlos
grep -oE "[a-zA-Z0-9.]+@[a-zA-Z0-9.]+\.[a-zA-Z]+" archivo.txt | sort | uniq
```

---

## Casos Especiales (Edge Cases)

### Buscar un punto literal

```bash
# MAL: . significa "cualquier caracter"
grep "archivo.txt" lista.txt

# BIEN: escapar el punto
grep "archivo\.txt" lista.txt
```

### Buscar al inicio CON caracteres especiales

```bash
# Buscar líneas que empiecen con $
grep "^\$" archivo.txt

# Buscar líneas que empiecen con [
grep "^\[" archivo.txt
```

### Buscar corchetes literales

```bash
# Escapar los corchetes
grep "\[ERROR\]" log.txt
```

---

## Errores Comunes

### 1. Olvidar -E para regex extendido

```bash
# FALLA: + no funciona sin -E
grep "a+" archivo.txt

# BIEN: usar -E
grep -E "a+" archivo.txt

# ALTERNATIVA: escapar
grep "a\+" archivo.txt
```

### 2. Confundir [] con ()

```bash
# [abc] = UN caracter: a, b, o c
# (abc) = la secuencia "abc"

echo "abc" | grep -E "[abc]"   # Coincide (encuentra "a")
echo "abc" | grep -E "(abc)"   # Coincide (encuentra "abc")
echo "cab" | grep -E "[abc]"   # Coincide (encuentra "c")
echo "cab" | grep -E "(abc)"   # NO coincide
```

### 3. ^ dentro vs fuera de []

```bash
# ^abc = línea que empieza con "abc"
# [^abc] = cualquier caracter EXCEPTO a, b, c

echo "xyz" | grep "^abc"      # NO coincide
echo "xyz" | grep "[^abc]"    # Coincide (x, y, z no son a, b, c)
```

---

## Ejercicios Prácticos

:::exercise{title="Extraer información de logs" difficulty="2"}

Crea un archivo `server.log`:
```
2024-01-15 10:30:00 INFO User login: admin
2024-01-15 10:31:00 ERROR Database connection failed
2024-01-15 10:32:00 INFO Request from 192.168.1.100
2024-01-15 10:33:00 WARNING Memory usage: 85%
2024-01-15 10:34:00 ERROR Timeout after 30s
2024-01-15 10:35:00 INFO User logout: admin
```

1. Extrae todas las líneas de ERROR
2. Extrae solo las direcciones IP
3. Extrae solo las fechas
4. Cuenta cuántos errores hay

:::

:::exercise{title="Validar datos" difficulty="3"}

Crea un archivo con varios formatos y escribe regex para:

1. Números de teléfono: `(XXX) XXX-XXXX`
2. Códigos postales mexicanos: `XXXXX`
3. URLs que empiecen con https
4. Contraseñas con al menos una mayúscula, una minúscula y un número

:::

---

## Resumen de Patrones Útiles

| Patrón | Descripción |
|--------|-------------|
| `[0-9]+` | Uno o más dígitos |
| `[a-zA-Z]+` | Una o más letras |
| `^palabra` | Línea que empieza con "palabra" |
| `palabra$` | Línea que termina con "palabra" |
| `\.[a-z]+$` | Extensión de archivo |
| `[0-9]{3}-[0-9]{4}` | Teléfono XXX-XXXX |
| `(opcion1\|opcion2)` | Una u otra opción |
