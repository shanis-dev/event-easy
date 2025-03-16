# Use the official Python image from the Docker Hub
FROM python:3.12.7-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    gcc \
    python3-dev \
    musl-dev \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt /app/
RUN pip install --upgrade pip
RUN pip install -r requirements.txt
RUN pip install gunicorn psycopg2-binary

# Copy the Django project
COPY . /app/

# Create directories for static and media files
RUN mkdir -p /app/staticfiles /app/media

# Expose the port the app runs on
EXPOSE 8000

# Create a non-root user
RUN adduser --disabled-password --no-create-home django

# Give proper permissions
RUN chown -R django:django /app
USER django

# Run the application
CMD ["gunicorn", "kabyka_psmo.wsgi:application", "--bind", "0.0.0.0:8000"]