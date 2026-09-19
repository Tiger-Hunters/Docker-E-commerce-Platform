FROM python:3.10-slim
WORKDIR /app
RUN pip install --no-cache-dir fastapi uvicorn requests redis sqlalchemy psycopg2-binary PyJWT
COPY . .
CMD ["python", "main.py"]