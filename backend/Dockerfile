# --- Build stage ---
FROM python:3.11-slim AS builder

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# --- Final stage ---
FROM python:3.11-slim

WORKDIR /app

# Copy installed dependencies from builder stage
COPY --from=builder /root/.local /root/.local
COPY app /app/app

# Ensure local packages are in path
ENV PATH=/root/.local/bin:$PATH
ENV PYTHONUNBUFFERED=1

EXPOSE 8000

# Run as non-root user for security hardening
USER 65534:65534

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
