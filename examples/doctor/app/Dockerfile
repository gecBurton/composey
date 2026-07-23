FROM python:3.12-slim
# psycopg2-binary and redis are pure-wheel installs; no system build deps needed.
RUN pip install --no-cache-dir flask boto3 psycopg2-binary redis
COPY app.py /app.py
CMD ["python", "/app.py"]
