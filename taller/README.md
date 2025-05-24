# Weather Station Log System

## Descripción

Este prototipo gestiona logs de estaciones meteorológicas con los siguientes elementos:

- **Producers:** Simulan datos y los envían a RabbitMQ (mensajes persistentes), exponen métricas en `/metrics` (puerto 8000).
- **RabbitMQ:** Broker de mensajería, con dashboard en `localhost:15672`.
- **Consumers:** Procesan mensajes, validan y persisten en PostgreSQL, exponen métricas en `/metrics` (puerto 8001).
- **PostgreSQL:** Almacena logs en la tabla `weather_logs`.
- **Prometheus & Grafana:** Monitorean todo el sistema y los exporters de RabbitMQ y PostgreSQL.
- **Docker Compose:** Orquesta y persiste todos los servicios.

## Uso

1. Clona este repositorio.
2. Ejecuta:
   ```bash
   docker-compose up --build
   ```
3. Accede a los servicios:
   - RabbitMQ Dashboard: [http://localhost:15672](http://localhost:15672) (`guest/guest`)
   - Prometheus: [http://localhost:9090](http://localhost:9090)
   - Grafana: [http://localhost:3000](http://localhost:3000) (usuario: admin, contraseña: admin)
   - PostgreSQL: puerto `5432`, usuario: `weatheruser`, pass: `weatherpass`
4. Agrega Prometheus como datasource en Grafana (`http://prometheus:9090`).
5. Importa dashboards desde [Grafana.com](https://grafana.com/grafana/dashboards/):
   - RabbitMQ: Dashboard ID `10991`
   - PostgreSQL: Dashboard ID `9628`
   - Añade tus propias gráficas para las métricas de Producer y Consumer (`weather_messages_sent_total`, `weather_messages_processed_total`, etc).

## Extensiones sugeridas

- API REST para consulta de logs.
- Alertas en tiempo real.
- Escalado horizontal de consumidores.

## Buenas prácticas y consideraciones

- Mensajes y colas son persistentes.
- prefetch_count=1 para orden y fiabilidad.
- Reconexión automática a DB y broker.
- Logs y manejo de excepciones en cada componente.
- Instrumentación Prometheus en Python.


Estructura de archivos:
weather-station/
├── docker-compose.yml          # Configuración de servicios
├── producer/
│   ├── producer.py             # Script para enviar datos
│   ├── Dockerfile
│   └── requirements.txt
├── consumer/
│   ├── consumer.py             # Procesa datos y guarda en PostgreSQL
│   ├── db.py                   # Conexión a la base de datos
│   ├── Dockerfile
│   └── requirements.txt
├── db/
│   └── init.sql                # Esquema de la base de datos
└── monitoring/
    ├── prometheus.yml          # Configuración de Prometheus
    └── grafana/                # Dashboards de Grafana


Enviar datos de prueba

    docker-compose exec rabbitmq rabbitmqadmin publish exchange=amq.default routing_key=weather_queue payload='{"station_id":"test1", "temperature":25, "humidity":60}'
Verificar losg:
   docker-compose logs -f consumer
Notas Finales
   Datos persistentes: Los volúmenes de Docker (pg_data, rabbitmq_data) guardan información entre reinicios.

   Escalabilidad: Puedes añadir más consumidores modificando docker-compose.yml.


Solución en caso de problemas

1. RabbitMQ no muestra métricas
bash
# Verificar que el plugin esté habilitado
docker-compose exec rabbitmq rabbitmq-plugins list | grep prometheus

# Probar acceso manual
curl -u user:pass http://localhost:15672/api/metrics
2. PostgreSQL no guarda datos
bash
# Verificar conexión desde el consumidor
docker-compose exec consumer python -c "from db import get_connection; conn = get_connection(); print(conn.status)"
3. Prometheus no detecta RabbitMQ
Revisa monitoring/prometheus.yml:

yaml
- job_name: 'rabbitmq'
  metrics_path: '/api/metrics'
  static_configs:
    - targets: ['rabbitmq:15672']
  basic_auth:
    username: 'user'
    password: 'pass'

    