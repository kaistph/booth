FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000 \
    KULTURA_DB_PATH=/data/kultura.db

WORKDIR /app
COPY . /app

EXPOSE 8000
CMD ["python", "server.py"]
