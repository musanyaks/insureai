FROM python:3.11-slim

WORKDIR /app

# Deps layer — cached until pyproject.toml changes
COPY pyproject.toml ./
RUN mkdir -p src/insureai && touch src/insureai/__init__.py \
 && pip install --no-cache-dir .

# Code layer — fast: reinstalls only the package, not the deps
COPY src ./src
RUN pip install --no-cache-dir --no-deps .

EXPOSE 8000
CMD ["uvicorn", "insureai.api.main:app", "--host", "0.0.0.0", "--port", "8000"]