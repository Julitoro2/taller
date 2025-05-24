# Importación de librerías necesarias
import pika  # Cliente RabbitMQ para Python
import json  # Para manejar datos en formato JSON
import os  # Para acceder a variables de entorno
import psycopg2  # Cliente para PostgreSQL
import logging  # Para registrar eventos y errores
import time  # Para operaciones de espera/reintento
import threading  # Para ejecutar el servidor de métricas en paralelo
from prometheus_client import start_http_server, Counter  # Métricas Prometheus

# Configuración de variables de entorno con valores por defecto
RABBITMQ_HOST = os.getenv('RABBITMQ_HOST', 'rabbitmq')
POSTGRES_HOST = os.getenv('POSTGRES_HOST', 'db')
POSTGRES_DB = os.getenv('POSTGRES_DB', 'weather')
POSTGRES_USER = os.getenv('POSTGRES_USER', 'weatheruser')
POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD', 'weatherpass')
QUEUE_NAME = 'weather_logs'
EXCHANGE = 'weather_exchange'
ROUTING_KEY = 'weather.log'

# Configuración del logger
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')

# Definición de métricas Prometheus
messages_processed = Counter('weather_messages_processed_total', 'Mensajes procesados')
errors = Counter('weather_consumer_errors_total', 'Errores en el consumer')

def connect_db():
    """
    Intenta conectarse a la base de datos PostgreSQL indefinidamente hasta tener éxito.
    Incrementa el contador de errores si falla la conexión.
    """
    while True:
        try:
            conn = psycopg2.connect(
                dbname=POSTGRES_DB,
                user=POSTGRES_USER,
                password=POSTGRES_PASSWORD,
                host=POSTGRES_HOST
            )
            conn.autocommit = True
            logging.info("Connected to PostgreSQL")
            return conn
        except Exception as e:
            errors.inc()
            logging.error(f"DB connection failed: {e}")
            time.sleep(5)

def validate_message(msg):
    """
    Valida los rangos de los datos meteorológicos recibidos.
    Retorna una tupla (True/False, mensaje de error).
    """
    try:
        assert -50 <= msg['temperature'] <= 60
        assert 0 <= msg['humidity'] <= 100
        assert 900 <= msg['pressure'] <= 1100
        return True, ""
    except AssertionError as e:
        return False, f"Validation error: {e}"
    except Exception as e:
        return False, f"Invalid format: {e}"

def persist_log(cur, msg):
    """
    Inserta un registro meteorológico válido en la base de datos.
    """
    cur.execute("""
        INSERT INTO weather_logs (station_id, temperature, humidity, pressure, timestamp)
        VALUES (%s, %s, %s, %s, to_timestamp(%s))
        """,
        (msg['station_id'], msg['temperature'], msg['humidity'], msg['pressure'], msg['timestamp'])
    )

def metrics_server():
    """
    Inicia el servidor HTTP de Prometheus para exponer las métricas.
    """
    start_http_server(8001)

def main():
    """
    Función principal del consumidor:
    - Inicia el servidor de métricas en un hilo aparte.
    - Establece conexión con PostgreSQL y prepara la tabla.
    - Se conecta a RabbitMQ y configura la cola y el exchange.
    - Escucha y procesa mensajes continuamente.
    """
    # Inicia servidor de métricas
    threading.Thread(target=metrics_server, daemon=True).start()

    # Conexión a la base de datos y creación de la tabla si no existe
    db_conn = connect_db()
    cur = db_conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS weather_logs (
            id SERIAL PRIMARY KEY,
            station_id VARCHAR(50),
            temperature REAL,
            humidity REAL,
            pressure REAL,
            timestamp TIMESTAMP
        )
    """)
    db_conn.commit()

    # Conexión a RabbitMQ
    params = pika.ConnectionParameters(
        host=RABBITMQ_HOST,
        heartbeat=60,
        connection_attempts=5,
        retry_delay=5,
    )
    connection = pika.BlockingConnection(params)
    channel = connection.channel()
    channel.exchange_declare(exchange=EXCHANGE, exchange_type='direct', durable=True)
    channel.queue_declare(queue=QUEUE_NAME, durable=True)
    channel.queue_bind(queue=QUEUE_NAME, exchange=EXCHANGE, routing_key=ROUTING_KEY)
    channel.basic_qos(prefetch_count=1)

    # Función de callback para procesar los mensajes recibidos
    def callback(ch, method, properties, body):
        try:
            msg = json.loads(body)
            valid, error = validate_message(msg)
            if valid:
                persist_log(cur, msg)
                messages_processed.inc()
                logging.info(f"Processed and saved: {msg}")
            else:
                errors.inc()
                logging.error(f"Invalid message: {msg} | {error}")
            ch.basic_ack(delivery_tag=method.delivery_tag)
        except Exception as e:
            errors.inc()
            logging.error(f"Processing error: {e}")
            ch.basic_ack(delivery_tag=method.delivery_tag)

    # Inicio del consumidor
    channel.basic_consume(queue=QUEUE_NAME, on_message_callback=callback)
    logging.info("Consumer started. Waiting for messages...")
    channel.start_consuming()

# Punto de entrada del script
if __name__ == '__main__':
    main()
