import random
import json
import time
from datetime import datetime

def generate_weather_data():
    return {
        "station_id": f"station_{random.randint(1, 5)}",
        "timestamp": datetime.utcnow().isoformat(),
        "temperature": round(random.uniform(-10, 45), 2),
        "humidity": round(random.uniform(10, 100), 2),
        "wind_speed": round(random.uniform(0, 20), 2)
    }

def generate_bulk_data(n):
    return [generate_weather_data() for _ in range(n)]
