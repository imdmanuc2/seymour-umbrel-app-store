FROM python:3.12-alpine

WORKDIR /app

RUN pip install flask

COPY app.py /app/app.py
COPY templates /app/templates

EXPOSE 8080

CMD ["python", "app.py"]
