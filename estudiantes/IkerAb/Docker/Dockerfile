# Imagen base: ubuntu 22.04
FROM ubuntu:22.04

# Crear directorio de trabajo
WORKDIR /app

# Copiar el script al contenedor
COPY info.sh .

# Dar permisos de ejecución
RUN chmod +x info.sh

# Ejecutar el script al arrancar
CMD ["./info.sh"]
