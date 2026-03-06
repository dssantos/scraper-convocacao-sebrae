FROM python:3.12-slim

# Install system dependencies for lxml
RUN apt-get update && apt-get install -y \
    libxml2 \
    libxslt1.1 \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -m -u 1000 scraperuser

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY sebrae_scraper.py .

# Create data directory for persistent storage
RUN mkdir -p /app/data && chown -R scraperuser:scraperuser /app

# Switch to non-root user
USER scraperuser

# Default command
CMD ["python", "sebrae_scraper.py"]
