FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app

COPY requirements.txt .
# On augmente le timeout à 1000 secondes et on autorise 5 tentatives en cas d'échec réseau
RUN pip install --no-cache-dir --default-timeout=1000 --retries 5 -r requirements.txt

COPY . .