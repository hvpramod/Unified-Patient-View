FROM python:3.12-slim
WORKDIR /app

COPY docker/pip.conf /etc/pip.conf

# Install shared models
COPY packages/shared-models ./packages/shared-models
RUN pip install --no-cache-dir ./packages/shared-models

# Install service dependencies (parsed from pyproject.toml — no package build needed)
COPY apps/ingestion-service/pyproject.toml ./pyproject.toml
RUN python3 -c "import tomllib,sys;deps=tomllib.load(open('pyproject.toml','rb'))['project']['dependencies'];print('\n'.join(deps))" > /tmp/reqs.txt && pip install --no-cache-dir -r /tmp/reqs.txt

COPY apps/ingestion-service/app ./app

EXPOSE 8001
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]
