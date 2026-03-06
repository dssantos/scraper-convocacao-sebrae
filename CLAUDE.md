# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Environment Setup

```bash
# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## Running the Scraper

### Local (Python)
```bash
python sebrae_scraper.py
```

### Docker
```bash
# Build and run
docker-compose build
docker-compose run --rm sebrae-scraper

# Run directly
docker-compose up
```

The script searches for a name in SEBRAE publication PDFs and sends an email notification when found.

## Required Environment Variables

Create a `.env` file with:

```
GOOGLE_EMAIL=your_email@gmail.com
GOOGLE_APP_PASSWORD=your_app_password
```

## Code Architecture

The scraper follows this flow:

1. **URL Tracking**: `load_checked_data()`, `save_checked_data()`, `is_checked()` manage the `checked_urls.json` file to avoid re-processing the same (name, URL) combinations.

2. **Link Extraction**: `get_publications_links()` scrapes the main SEBRAE page for publication links using XPath: `//div[contains(@class, "sb-integra-conteudo__arquivo")]//a/@href`

3. **PDF Link Extraction**: `get_file_link()` extracts the actual PDF download URL from publication pages by finding the input field with id `urlDownload`.

4. **Download & Extract**: `download_file()` saves PDFs to `download.pdf` (handles relative URLs), and `extract_text_from_pdf()` uses pypdf to extract all text.

5. **Search & Notify**: Main loop checks if search term exists in PDF text (case-insensitive), builds HTML message, and `send_mail()` sends notification via Gmail SMTP.

**Important**: The search name and target URL are hardcoded at the bottom of `sebrae_scraper.py` (lines 97-98). Modify these values to change the search parameters.

## Dependencies

- **requests==2.32.3**: HTTP library for web scraping
- **lxml==5.3**: HTML/XML parsing with XPath
- **pypdf==5.1**: PDF text extraction
- **python-decouple==3.8**: Configuration management from environment variables

## Docker

### Image Details
- Base: `python:3.12-slim`
- System dependencies: `libxml2`, `libxslt1.1` (for lxml)
- Non-root user: `scraperuser` (uid 1000)
- Working directory: `/app`

### Volume Mounts
- `./checked_urls.json:/app/checked_urls.json` - Persists checked URLs between runs

### Scheduling
For periodic execution, use host cron:
```bash
# Run every 6 hours
0 */6 * * * cd /path/to/scraper-convocacao-sebrae && docker compose run --rm sebrae-scraper
```
