# Use the official Python image
FROM python:3.9-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set the working directory
WORKDIR /app

# Install Poetry
RUN pip install poetry

# Copy the dependency files
COPY pyproject.toml poetry.lock /app/

# Install dependencies
RUN poetry config virtualenvs.create false && poetry install --no-dev

# Copy the rest of the application code
COPY . .

# Expose the port the app runs on
EXPOSE 5000

# Command to run the application
CMD ["flask", "run", "--host=0.0.0.0"]
