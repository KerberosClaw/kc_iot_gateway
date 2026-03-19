FROM python:3.12-slim-bookworm

WORKDIR /app

COPY pyproject.toml README.md ./
RUN pip install --no-cache-dir .

COPY . .

CMD ["python", "-m", "src"]
