# Importación de librerías necesarias
import pika  # Cliente RabbitMQ para Python
import json  # Para codificar mensajes en formato JSON
import os  # Para acceder a variables de entorno
import time  # Para operaciones de tiempo (sleep, timestamp)
import random  # Para generar datos simulados aleatorios
import logging  # Para registrar eventos
import threading  # Para ejecutar el servidor de métricas en segundo plano
from prometheus_client import start_http_server, Counter, Gauge  # Métricas Prometheus

# Configuración de variables de entorno con valores por defecto
RABBITMQ_HOST = os.getenv('RABBITMQ_HOST', 'rabbitmq')
EXCHANGE = 'weather_exchange'
ROUTING_KEY = 'weather.log'
SLEEP_TIME = 2  # Tiempo entre envíos de mensajes (en segundos)

# Configuración del logger
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')

# Definición de métricas Prometheus
messages_sent = Counter('weather_messages_sent_total', 'Total de mensajes enviados')
errors = Counter('weather_producer_errors_total', 'Errores en el producer')
temperature_gauge = Gauge('weather_producer_last_temperature', 'Última temperatura enviada')

def fake_weather_data():
    """
    Genera un conjunto de datos meteorológicos falsos para pruebas.
    Devuelve un diccionario con:
    - station_id: ID de la estación
    - temperature: temperatura simulada (-20 a 45 °C)
    - humidity: humedad simulada (0 a 100 %)
    - pressure: presión simulada (950 a 1050 hPa)
    - timestamp: marca de tiempo actual
    """
    return {
        "station_id": f"station_{random.randint(1, 5)}",
        "temperature": round(random.uniform(-20, 45), 2),
        "humidity": round(random.uniform(0, 100), 2),
        "pressure": round(random.uniform(950, 1050), 2),
        "timestamp": int(time.time())
    }

def metrics_server():
    """
    Inicia el servidor HTTP de Prometheus para exponer las métricas del productor.
    """
    start_http_server(8000)

def main():
    """
    Función principal del productor:
    - Se conecta a RabbitMQ.
    - Declara el exchange.
    - En un bucle infinito:
        - Genera datos meteorológicos simulados.
        - Los convierte a JSON.
        - Publica los mensajes en RabbitMQ.
        - Actualiza las métricas Prometheus.
        - Espera un intervalo antes de repetir.
    """
    # Configuración de conexión con RabbitMQ
    params = pika.ConnectionParameters(
        host=RABBITMQ_HOST,
        heartbeat=60,
        connection_attempts=5,
        retry_delay=5,
    )
    connection = pika.BlockingConnection(params)
    channel = connection.channel()
    channel.exchange_declare(exchange=EXCHANGE, exchange_type='direct', durable=True)

    while True:
        try:
            # Generar datos falsos
            data = fake_weather_data()
            message = json.dumps(data)

            # Actualizar métrica de temperatura
            temperature_gauge.set(data['temperature'])

            # Publicar el mensaje en RabbitMQ
            channel.basic_publish(
                exchange=EXCHANGE,
                routing_key=ROUTING_KEY,
                body=message,
                properties=pika.BasicProperties(
                    delivery_mode=2,  # Mensaje persistente
                    content_type='application/json'
                )
            )
            messages_sent.inc()
            logging.info(f"Sent: {message}")
            time.sleep(SLEEP_TIME)
        except Exception as e:
            errors.inc()
            logging.error(f"Error sending message: {e}")
            time.sleep(SLEEP_TIME)

# Punto de entrada del script
if __name__ == '__main__':
    threading.Thread(target=metrics_server, daemon=True).start()  # Inicia servidor Prometheus
    main()  # Ejecuta el productor
