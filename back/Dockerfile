FROM python:3.9-slim

WORKDIR /app

# Install dependencies needed for psycopg2
RUN apt-get update && apt-get install -y \
    libpq-dev gcc python3-dev && \
    apt-get clean

COPY dfiles/requirements.txt .

COPY .env .

RUN pip install --no-cache-dir -r requirements.txt

RUN apt-get update && apt-get install vim -y

EXPOSE 8000

COPY ./srcs .

COPY wait-for-it.sh /app/wait-for-it.sh
RUN chmod +x /app/wait-for-it.sh

COPY script.sh /app/script.sh
RUN chmod +x /app/script.sh

# Wait for db, then make migrations

# Create superuser
COPY create_superuser.py .
ENV DJANGO_SUPERUSER_USERNAME=admin
ENV DJANGO_SUPERUSER_EMAIL=admin@example.com
ENV DJANGO_SUPERUSER_PASSWORD=adminpass
ENV PYTHONPATH=/app/pong_project

ENTRYPOINT ["/app/script.sh"]
