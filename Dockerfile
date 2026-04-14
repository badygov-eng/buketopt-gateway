# buketopt-gateway — слушает 8600 внутри контейнера
FROM python:3.12-slim-bookworm

WORKDIR /app
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app/src

COPY pyproject.toml README.md ./
COPY src ./src

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir .

EXPOSE 8600

CMD ["uvicorn", "gateway.app:app", "--host", "0.0.0.0", "--port", "8600"]
