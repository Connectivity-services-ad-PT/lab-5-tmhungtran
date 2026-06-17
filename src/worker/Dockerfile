FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN groupadd --system appuser \
    && useradd --system --gid appuser --home-dir /app appuser

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py config.py .
RUN chown -R appuser:appuser /app

USER appuser

CMD ["python", "main.py"]
