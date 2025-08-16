FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# System dependencies (for optional wheels build)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
 && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md /app/
COPY app /app/app

RUN pip install --no-cache-dir --upgrade pip \
 && pip install --no-cache-dir -e .

EXPOSE 8000

# Default Redis URL for docker-compose network
ENV WINEAR_REDIS_URL=redis://redis:6379/0

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]


