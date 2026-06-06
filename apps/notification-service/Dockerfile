FROM python:3.12-slim
WORKDIR /app

COPY docker/pip.conf /etc/pip.conf

COPY apps/notification-service/pyproject.toml ./pyproject.toml
RUN python3 -c "import tomllib,sys;deps=tomllib.load(open('pyproject.toml','rb'))['project']['dependencies'];print('\n'.join(deps))" > /tmp/reqs.txt && pip install --no-cache-dir -r /tmp/reqs.txt

COPY apps/notification-service/app ./app

EXPOSE 8006
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8006"]
