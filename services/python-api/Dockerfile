FROM python:3.11-slim

WORKDIR /app

COPY services/python-api/requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY services/python-api/app.py .

EXPOSE 8000

CMD ["python", "app.py"]
