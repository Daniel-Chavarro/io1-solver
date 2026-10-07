FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim AS build
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev
COPY src ./src

FROM python:3.13-slim-bookworm
WORKDIR /app
COPY --from=build /app /app
ENV PATH="/app/.venv/bin:$PATH"
EXPOSE 8000
CMD ["uvicorn", "solver.main:app", "--host", "0.0.0.0", "--port", "8000"]
