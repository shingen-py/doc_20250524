FROM python:3.13

WORKDIR /code

COPY ./ ./

RUN pip install --no-cache-dir --upgrade -r requirements.txt

# サーバーを起動
CMD ["gunicorn", "main:app", "--workers", "1", "--worker-class", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000"]
