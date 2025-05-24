FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
COPY consumer/consumer.py .

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8001
CMD ["python", "consumer.py"]
