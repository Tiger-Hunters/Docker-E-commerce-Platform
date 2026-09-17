FROM python:3.10-slim
WORKDIR /app
RUN pip install fastapi uvicorn requests redis sqlalchemy psycopg2-binary
COPY . .
CMD ["python", "main.py"]