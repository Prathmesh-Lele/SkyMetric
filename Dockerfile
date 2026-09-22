# ---- Stage 1: Build frontend ----
FROM node:20-alpine AS frontend
WORKDIR /app
COPY skymetric-frontend/package.json skymetric-frontend/package-lock.json* ./
RUN npm ci || npm install
COPY skymetric-frontend/ .
RUN npm run build

# ---- Stage 2: Backend ----
FROM python:3.11-slim AS backend
WORKDIR /app

# System deps for Playwright
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl wget gnupg2 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright Chromium (optional — scraper falls back to fli/SerpApi/mock)
RUN playwright install chromium || true

COPY skymetric/ ./skymetric/

# Copy built frontend into backend static dir (optional)
COPY --from=frontend /app/.next ./static_frontend/.next
COPY --from=frontend /app/package.json ./static_frontend/

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
  CMD curl -f http://localhost:8000/api/v1/health || exit 1

CMD ["uvicorn", "skymetric.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
