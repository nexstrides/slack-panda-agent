FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY *.py .
RUN mkdir -p /data

ENV HISTORY_DB_PATH=/data/history.db

EXPOSE 8000

CMD ["python", "app.py"]
