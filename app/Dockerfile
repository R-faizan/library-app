# ---------------------------------------------------------------------------
# Custom image for the Library Book Manager web application
# Build:  docker build -t library-web:1.0 .
# Run:    docker run -d --name web-test -p 8080:5000 library-web:1.0
# ---------------------------------------------------------------------------

# 1. Base image: small official Python image (Debian "slim" variant)
FROM python:3.12-slim

# 2. Metadata about the image
LABEL maintainer="<YOUR NAME> <YOUR REG NO>" \
      course="CSC418 DevOps for Cloud Computing" \
      app="library-web"

# 3. Python settings: no .pyc files, log output straight to the console
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=5000

# 4. Working directory inside the container
WORKDIR /app

# 5. Install dependencies FIRST (copy only requirements.txt) so this layer is
#    cached and not rebuilt every time the source code changes
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 6. Copy the application source code
COPY . .

# 7. Security: create a non-root user and give it the app + data folders
RUN useradd --create-home --uid 1001 appuser \
    && mkdir -p /data \
    && chown -R appuser:appuser /app /data
USER appuser

# 8. Document the port the app listens on
EXPOSE 5000

# 9. Docker checks the container's health by calling /health every 30s
HEALTHCHECK --interval=30s --timeout=5s --start-period=40s --retries=3 \
  CMD python -c "import urllib.request,sys; urllib.request.urlopen('http://localhost:5000/health', timeout=4)" || exit 1

# 10. Start the app with Gunicorn (production WSGI server), 2 worker processes
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "--access-logfile", "-", "app:app"]
