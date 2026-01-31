# Use a slim Python 3.12 image as the base
FROM python:3.12-slim AS builder

# Set build-time environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PDM_CHECK_UPDATE=false

# Install PDM
RUN pip install --no-cache-dir pdm

# Set working directory
WORKDIR /project

# Copy dependency files
COPY pyproject.toml pdm.lock ./

# Install dependencies into a local .venv
RUN pdm install --check --prod --no-editable

# --- Runtime Stage ---
FROM python:3.12-slim

# Set runtime environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/project/.venv/bin:$PATH" \
    PYTHONPATH="/project"

# Set working directory
WORKDIR /project

# Copy virtual environment from builder stage
COPY --from=builder /project/.venv /project/.venv

# Copy the rest of the application code
COPY . .

# Expose the application port
EXPOSE 8000

# Command to run the application
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
