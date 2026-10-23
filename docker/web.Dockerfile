FROM python:3.13-slim-bookworm@sha256:e32be0e55814a08977501ca863271d9bd02443710db8f2afaf8372e2c4508530 AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1
WORKDIR /app
COPY requirements.lock ./
RUN python -m pip install --no-cache-dir --require-hashes -r requirements.lock \
    && groupadd --gid 10001 wedding \
    && useradd --uid 10001 --gid wedding --no-create-home wedding
COPY manage.py pyproject.toml ./
COPY config ./config
COPY apps ./apps
COPY templates ./templates
COPY static ./static
COPY docker/entrypoint.py ./docker/entrypoint.py
RUN APP_ENV=local \
    DJANGO_SECRET_KEY=static-build-placeholder-with-no-runtime-authority-or-customer-data \
    DATABASE_PASSWORD=static-build-placeholder \
    python manage.py collectstatic --noinput --verbosity 0
USER 10001:10001
EXPOSE 8000
ENTRYPOINT ["python", "docker/entrypoint.py"]
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "2", "--threads", "2", "--timeout", "30", "--worker-tmp-dir", "/tmp", "--no-control-socket", "--error-logfile", "-"]

FROM runtime AS development
USER root
COPY requirements-dev.lock ./
RUN python -m pip install --no-cache-dir --require-hashes -r requirements-dev.lock
COPY tests ./tests
USER 10001:10001
CMD ["python", "-m", "pytest", "-p", "no:cacheprovider"]
