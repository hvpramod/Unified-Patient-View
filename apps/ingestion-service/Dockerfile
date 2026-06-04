FROM python:3.12-slim

WORKDIR /app
RUN pip install --no-cache-dir uv
COPY pyproject.toml .
COPY ../../packages/shared-models ./packages/shared-models
RUN uv pip install --system -e ./packages/shared-models -r pyproject.toml
COPY app ./app
EXPOSE 8001
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]
