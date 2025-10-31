# syntax=docker/dockerfile:1

FROM python:3.11-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install runtime dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copy application code and default ruleset
COPY src ./src
COPY rules_nl.yaml ./rules_nl.yaml

# Set the default command to start the interactive CLI
ENTRYPOINT ["python", "-m", "src.cli"]
CMD ["run"]