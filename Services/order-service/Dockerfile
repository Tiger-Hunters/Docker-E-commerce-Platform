FROM python:3.10-slim
WORKDIR /app
RUN pip install fastapi uvicorn requests
COPY . .
CMD ["python", "main.py"]