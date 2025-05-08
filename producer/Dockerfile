# Usa una imagen base de Python
FROM python:3.13-slim

# Establece el directorio de trabajo dentro del contenedor
WORKDIR /app

# Copia los archivos del productor al contenedor
COPY *.py /app/
COPY requirements.txt /app/
COPY messages /app/messages

# Instala las dependencias
RUN pip install --no-cache-dir -r requirements.txt

# Ejecuta el script principal
CMD ["python", "producer.py"]
