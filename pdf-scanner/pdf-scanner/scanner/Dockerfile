FROM python:3.11-slim

# System deps: ClamAV, build tools, MuPDF tools are already provided via PyMuPDF (no mutool needed)
RUN apt-get update && apt-get install -y --no-install-recommends \
    clamav ca-certificates \
 && rm -rf /var/lib/apt/lists/*

# Python deps
WORKDIR /app
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# App files
COPY scanner.py /app/scanner.py
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

EXPOSE 8000
ENTRYPOINT ["/app/entrypoint.sh"]
