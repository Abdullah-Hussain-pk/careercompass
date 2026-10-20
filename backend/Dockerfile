FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Run migrations and start server
CMD ["sh", "-c", "alembic upgrade head && python -m app.data.seed && uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"]
