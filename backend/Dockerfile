# ==========================================
# Stage 1: Builder
# ==========================================
FROM python:3.11-slim AS builder

# Install uv from PyPI (often much faster than downloading the GHCR Docker image)
RUN pip install uv

# Set env vars for uv to compile bytecode for faster startup
ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy

WORKDIR /app

# Copy ONLY the lockfile and pyproject.toml first to cache dependencies!
COPY pyproject.toml uv.lock ./

# Install dependencies into a virtual environment
RUN uv sync --frozen --no-dev --no-install-project

# ==========================================
# Stage 2: Runtime
# ==========================================
FROM python:3.11-slim

WORKDIR /app



# Copy the pre-built virtual environment from the builder stage
COPY --from=builder /app/.venv /app/.venv

# Put the virtual environment on the system PATH
ENV PATH="/app/.venv/bin:$PATH"

# Now copy your application code (changing this will NOT trigger re-downloads!)
COPY pyproject.toml alembic.ini ./
COPY alembic/ ./alembic/
COPY src/ ./src/

# Install the project itself without re-installing dependencies
RUN pip install --no-deps -e .

EXPOSE 8000

# Run using the python executable directly from the PATH
CMD ["sh", "-c", "alembic upgrade head && uvicorn src.main:app --host 0.0.0.0 --port 8000"]
