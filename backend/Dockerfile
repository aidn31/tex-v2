FROM python:3.12-slim

RUN apt-get update && apt-get install -y \
    ffmpeg \
    libpango-1.0-0 \
    libpangoft2-1.0-0 \
    libffi-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# CMD is NOT set here — specified per Cloud Run service
# tex-api:             CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
# tex-worker-film:     CMD ["celery", "-A", "tasks.celery_app", "worker", "-Q", "film_processing", "--concurrency=1"]
# tex-worker-report:   CMD ["celery", "-A", "tasks.celery_app", "worker", "-Q", "report_generation", "--concurrency=1"]
# tex-worker-section:  CMD ["celery", "-A", "tasks.celery_app", "worker", "-Q", "section_generation", "--concurrency=4"]
# tex-worker-notify:   CMD ["celery", "-A", "tasks.celery_app", "worker", "-Q", "notifications", "--concurrency=2"]
