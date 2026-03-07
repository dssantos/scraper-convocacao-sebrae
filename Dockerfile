FROM python:3.12-slim

# Install system dependencies for lxml
RUN apt-get update && apt-get install -y \
    libxml2 \
    libxslt1.1 \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY sebrae_scraper.py .
COPY tests/ ./tests/
COPY pytest.ini .

# Create data directory and empty checked_urls.json file
RUN mkdir -p /app/data && echo '{}' > /app/data/checked_urls.json

# Default command
CMD ["python", "sebrae_scraper.py"]
