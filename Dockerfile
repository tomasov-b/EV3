FROM python:3.11-slim

WORKDIR /app

COPY requerimientos.txt .
RUN pip install --no-cache-dir -r requerimientos.txt

COPY app.py .

EXPOSE 5000

CMD ["python", "app.py"]