FROM python:3.12-slim

WORKDIR /app

RUN pip install gunicorn
COPY requirements.txt .

RUN pip install -r requirements.txt --no-cache-dir

COPY ./foodgram .

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "foodgram.wsgi"]