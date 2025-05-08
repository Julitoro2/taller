## Productor de datos meteorológicos

Este microservicio simula estaciones meteorológicas y envía datos a RabbitMQ.

### Funcionalidades
- Generación aleatoria de datos en formato JSON.
- Envío a un exchange RabbitMQ usando mensajes durables.
- Envío controlado masivo para pruebas.

### Uso
```bash
python producer.py
