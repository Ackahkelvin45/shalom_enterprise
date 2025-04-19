# Use an official Python runtime as a parent image
FROM python:3.13-bullseye

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Set work directory
WORKDIR /shalom_enterprise

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . .

# Collect static files
RUN python manage.py collectstatic --noinput

# Use JSON format for CMD as recommended
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]