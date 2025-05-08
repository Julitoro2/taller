import pika
import json
import time
from config import *
from data_generator import generate_weather_data

credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASS)
params = pika.ConnectionParameters(host=RABBITMQ_HOST, port=RABBITMQ_PORT, credentials=credentials)
connection = pika.BlockingConnection(params)
channel = connection.channel()

channel.exchange_declare(exchange=EXCHANGE_NAME, exchange_type='direct', durable=True)

def publish_message(message: dict):
    channel.basic_publish(
        exchange=EXCHANGE_NAME,
        routing_key=ROUTING_KEY,
        body=json.dumps(message),
        properties=pika.BasicProperties(delivery_mode=2)  # Make message persistent
    )

if __name__ == "__main__":
    while True:
        msg = generate_weather_data()
        publish_message(msg)
        print("Sent:", msg)
        time.sleep(2)
