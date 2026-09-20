FROM python:3.11-slim

WORKDIR /code

# Sin dependencias de sistema: httpx es 100% Python, igual que pymysql en
# ms-clientes, así que no hace falta apt-get (evita depender de mirrors de
# Debian, que fue justo el problema que tuvo ms-clientes al inicio).
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ./app ./app

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
