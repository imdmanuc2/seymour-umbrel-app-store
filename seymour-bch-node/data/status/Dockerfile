FROM python:3.12-alpine

WORKDIR /app

COPY app.py /app/app.py
COPY provisioning.py /app/provisioning.py
COPY index.html /app/index.html
COPY templates /app/templates

EXPOSE 8080

CMD ["python", "/app/app.py"]
