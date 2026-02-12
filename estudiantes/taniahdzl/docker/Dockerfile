# Imagen base: ubuntu 22.04 (Capa 1)
FROM ubuntu:22.04

# Crear directorio de trabajo (Capa 2)
WORKDIR /app

# Copiar el script al contenedor (Capa 3)
COPY info.sh .

# Dar permisos de ejecución (Capa 4)
RUN chmod +x info.sh

# Ejecutar el script al arrancar (Capa 5)
CMD ["./info.sh"]