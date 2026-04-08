FROM python:3.12-slim

ENV PYTHONPATH=/app/fastapi_app

WORKDIR /app

RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc

COPY requirements.txt /app/

RUN pip install --upgrade pip && pip install -r requirements.txt

COPY . /app

RUN chmod +x entrypoint.sh
