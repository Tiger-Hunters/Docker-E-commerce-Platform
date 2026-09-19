FROM python:3.10-slim

WORKDIR /app

RUN pip install --no-cache-dir \
    fastapi \
    uvicorn \
    requests \
    sqlalchemy \
    psycopg2-binary \
    "passlib[bcrypt]" \
    PyJWT

COPY . .

CMD ["python", "main.py"]