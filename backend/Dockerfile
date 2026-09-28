FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# The ONNX encoder's weights live here. Kept as an environment variable rather
# than a fastembed default because the default is a temp directory that does
# not survive a container restart, which on a free tier means re-downloading
# ~90MB and rebuilding the index on every cold start.
ENV EMBEDDING_CACHE_DIR=/app/.model_cache

# Pinned here as well as in the application so the model warmed into the image
# below is the model the running container asks for. The platform can still
# override it, but a mismatch is then a deliberate act rather than an accident.
ENV EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2

COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Pre-warm the embedding model into the image layer.
#
# Without this the download happens inside application startup: the first
# request after a cold start waits on a network fetch before the index can be
# built, and a download failure is discovered in production rather than here.
# Baking it in also means a restart reuses the cached weights.
RUN python -c "\
from fastembed import TextEmbedding; \
import os; \
model = TextEmbedding( \
    model_name=os.getenv('EMBEDDING_MODEL', 'sentence-transformers/all-MiniLM-L6-v2'), \
    cache_dir=os.environ['EMBEDDING_CACHE_DIR'], \
); \
vectors = list(model.embed(['warm up'])); \
print('embedding model ready:', len(vectors[0]), 'dimensions')"

COPY . .

EXPOSE 8000

CMD ["sh","-c","python -m uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
