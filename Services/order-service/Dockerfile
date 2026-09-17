FROM python:3.10-slim
WORKDIR /app
RUN pip install fastapi uvicorn requests sqlalchemy psycopg2-binary
COPY . .
CMD ["python", "main.py"]