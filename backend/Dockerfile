FROM python:3.10.12

WORKDIR /app

RUN pip install gunicorn==20.1.0

COPY requirements.txt .

RUN pip install -r requirements.txt --no-cache-dir

COPY Foodgram/ .

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "Foodgram.wsgi:application"]