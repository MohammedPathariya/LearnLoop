# backend/Dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY . .

RUN pip install --no-cache-dir -r requirements.txt

CMD ["gunicorn", "--bind", "0.0.0.0:5050", "--workers", "1", "--threads", "2", "--timeout", "120", "wsgi:app"]
