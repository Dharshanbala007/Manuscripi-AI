# API image for hosted deployments (Render). Local development doesn't use this.
FROM python:3.12-slim

# LibreOffice Writer converts the formatted DOCX to PDF. Liberation fonts are metric-compatible
# with Times New Roman / Arial, so the PDF paginates like the DOCX.
RUN apt-get update \
    && apt-get install -y --no-install-recommends libreoffice-writer fonts-liberation fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /srv
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app ./app

RUN useradd --create-home app
USER app

# Render injects PORT; 8000 is the fallback for a plain `docker run`.
ENV PORT=8000
CMD ["sh", "-c", "exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT}"]
