FROM python:3.12-slim
WORKDIR /app

COPY docker/pip.conf /etc/pip.conf

COPY packages/shared-models ./packages/shared-models
RUN pip install --no-cache-dir ./packages/shared-models

COPY apps/conflict-detection/pyproject.toml ./pyproject.toml
RUN python3 -c "import tomllib,sys;deps=tomllib.load(open('pyproject.toml','rb'))['project']['dependencies'];print('\n'.join(deps))" > /tmp/reqs.txt && pip install --no-cache-dir -r /tmp/reqs.txt

COPY apps/conflict-detection/app ./app

EXPOSE 8003
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8003"]
