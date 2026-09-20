FROM python:3.11-slim-bookworm
ENV PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1 OMP_NUM_THREADS=2
RUN apt-get update && apt-get install -y --no-install-recommends libgomp1 ca-certificates && rm -rf /var/lib/apt/lists/*
RUN useradd --create-home --uid 1000 appuser
WORKDIR /home/appuser/again
COPY requirements.txt requirements.txt
RUN python -m pip install --no-cache-dir -r requirements.txt
COPY --chown=appuser:appuser app app
COPY --chown=appuser:appuser static static
COPY --chown=appuser:appuser data data
USER appuser
EXPOSE 7860
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "7860", "--no-access-log"]
