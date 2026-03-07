"""Fixtures and configuration for pytest."""
import os
import tempfile
import json
import pytest
import sys
import importlib
from unittest.mock import Mock


@pytest.fixture(autouse=True)
def reset_sebrae_scraper_module():
    """Reset the sebrae_scraper module between tests to ensure isolation."""
    # Store original state
    original_module = sys.modules.get('sebrae_scraper')

    yield

    # Clean up after test
    if 'sebrae_scraper' in sys.modules:
        # If we imported during the test, remove it to force fresh import
        del sys.modules['sebrae_scraper']


@pytest.fixture
def temp_checked_file():
    """Create a temporary file for checked URLs data."""
    fd, path = tempfile.mkstemp(suffix='.json')
    os.close(fd)
    yield path
    os.unlink(path)


@pytest.fixture
def sample_checked_data():
    """Sample checked URLs data for testing."""
    return {
        "https://example.com/pub1": ["John Doe", "Jane Smith"],
        "https://example.com/pub2": ["John Doe"]
    }


@pytest.fixture
def mock_html_response():
    """Mock HTML response for publications page."""
    html_content = '''
    <html>
        <body>
            <div class="sb-integra-conteudo__arquivo">
                <a href="/publicacoes/1">Publication 1</a>
                <a href="/publicacoes/2">Publication 2</a>
                <a href="/publicacoes/3">Publication 3</a>
            </div>
        </body>
    </html>
    '''
    return html_content


@pytest.fixture
def mock_download_page_response():
    """Mock HTML response for download page."""
    html_content = '''
    <html>
        <body>
            <input id="urlDownload" value="https://sebrae.com.br/files/document.pdf" />
        </body>
    </html>
    '''
    return html_content


@pytest.fixture
def mock_pdf_content():
    """Mock minimal PDF content for testing."""
    # Create a minimal valid PDF header
    return b'%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n2 0 obj\n<<\n/Type /Pages\n/Kids [3 0 R]\n/Count 1\n>>\nendobj\n3 0 obj\n<<\n/Type /Page\n/Parent 2 0 R\n/MediaBox [0 0 612 792]\n>>\nendobj\nxref\n0 4\n0000000000 65535 f\n0000000009 00000 n\n0000000058 00000 n\n0000000115 00000 n\ntrailer\n<<\n/Size 4\n/Root 1 0 R\n>>\nstartxref\n0\n%%EOF'


@pytest.fixture
def mock_requests_session(mock_html_response, mock_download_page_response):
    """Mock requests session with predefined responses."""
    session = Mock()

    def mock_get(url, *args, **kwargs):
        response = Mock()
        if 'sebrae.com.br' in url and '/sites/' in url:
            response.content = mock_html_response.encode()
        elif '/publicacoes/' in url:
            response.content = mock_download_page_response.encode()
        elif 'document.pdf' in url:
            response.content = b'%PDF-1.4\n%Mock PDF content with John Doe inside\n%%EOF'
        return response

    return mock_get


@pytest.fixture
def env_vars(monkeypatch):
    """Set test environment variables."""
    monkeypatch.setenv('GOOGLE_EMAIL', 'test@example.com')
    monkeypatch.setenv('GOOGLE_APP_PASSWORD', 'test_password')
    monkeypatch.setenv('LOG_LEVEL', 'DEBUG')
