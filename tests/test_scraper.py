"""Unit tests for scraping functions."""
import pytest
from unittest.mock import Mock, patch, mock_open
from requests.exceptions import MissingSchema, ConnectionError


@pytest.fixture
def mock_pdf_reader():
    """Mock PDF reader for testing."""
    reader = Mock()
    page1 = Mock()
    page1.extract_text.return_value = "This is a test PDF content with John Doe mentioned."
    page2 = Mock()
    page2.extract_text.return_value = "Additional content here."
    reader.pages = [page1, page2]
    return reader


class TestGetPublicationsLinks:
    """Tests for get_publications_links function."""

    @patch('sebrae_scraper.requests.get')
    def test_get_publication_links_success(self, mock_get, mock_html_response):
        """Test successfully extracting publication links."""
        mock_response = Mock()
        mock_response.content = mock_html_response.encode()
        mock_get.return_value = mock_response

        from sebrae_scraper import get_publications_links
        result = get_publications_links("https://sebrae.com.br/test")

        assert len(result) == 3
        assert all(link.startswith('https://sebrae.com.br') for link in result)
        assert '/publicacoes/1' in result[0]
        assert '/publicacoes/2' in result[1]
        assert '/publicacoes/3' in result[2]

    @patch('sebrae_scraper.requests.get')
    def test_get_publication_links_empty(self, mock_get):
        """Test handling page with no publication links."""
        mock_response = Mock()
        mock_response.content = b'<html><body>No links here</body></html>'
        mock_get.return_value = mock_response

        from sebrae_scraper import get_publications_links
        result = get_publications_links("https://sebrae.com.br/test")

        assert result == []

    @patch('sebrae_scraper.requests.get')
    def test_get_publication_links_request_error(self, mock_get):
        """Test handling request errors."""
        mock_get.side_effect = ConnectionError("Network error")

        from sebrae_scraper import get_publications_links
        with pytest.raises(ConnectionError):
            get_publications_links("https://sebrae.com.br/test")


class TestGetFileLink:
    """Tests for get_file_link function."""

    @patch('sebrae_scraper.requests.get')
    def test_get_file_link_success(self, mock_get, mock_download_page_response):
        """Test successfully extracting file link."""
        mock_response = Mock()
        mock_response.content = mock_download_page_response.encode()
        mock_get.return_value = mock_response

        from sebrae_scraper import get_file_link
        result = get_file_link("https://sebrae.com.br/publications/1")

        assert result == "https://sebrae.com.br/files/document.pdf"

    @patch('sebrae_scraper.requests.get')
    def test_get_file_link_missing_element(self, mock_get):
        """Test handling page with missing download element."""
        # First call returns page without element, second also fails
        mock_response = Mock()
        mock_response.content = b'<html><body>No download link here</body></html>'
        mock_get.return_value = mock_response

        from sebrae_scraper import get_file_link
        with pytest.raises(IndexError):
            get_file_link("https://sebrae.com.br/publications/1")


class TestDownloadFile:
    """Tests for download_file function."""

    @patch('sebrae_scraper.requests.get')
    @patch('builtins.open', new_callable=mock_open)
    def test_download_file_success(self, mock_file, mock_get):
        """Test successfully downloading a file."""
        mock_response = Mock()
        mock_response.content = b'PDF file content here'
        mock_get.return_value = mock_response

        from sebrae_scraper import download_file
        download_file("https://example.com/file.pdf")

        mock_get.assert_called_once()
        # Check that open was called with download.pdf (logging may also open files)
        mock_file.assert_any_call('download.pdf', 'wb')

    @patch('sebrae_scraper.requests.get')
    @patch('builtins.open', new_callable=mock_open)
    def test_download_file_missing_schema(self, mock_file, mock_get):
        """Test downloading file with missing schema (retry with https)."""
        # First call raises MissingSchema, second succeeds
        mock_response_success = Mock()
        mock_response_success.content = b'PDF file content'

        mock_get.side_effect = [
            MissingSchema("No schema"),
            mock_response_success
        ]

        from sebrae_scraper import download_file
        download_file("//example.com/file.pdf")

        assert mock_get.call_count == 2

    @patch('sebrae_scraper.requests.get')
    @patch('builtins.open', new_callable=mock_open)
    def test_download_file_streaming(self, mock_file, mock_get):
        """Test that file is downloaded with streaming."""
        mock_response = Mock()
        mock_response.content = b'PDF content'
        mock_get.return_value = mock_response

        from sebrae_scraper import download_file
        download_file("https://example.com/file.pdf")

        # Verify stream=True was used
        mock_get.assert_called_once_with("https://example.com/file.pdf", stream=True)


class TestExtractTextFromPdf:
    """Tests for extract_text_from_pdf function."""

    @patch('sebrae_scraper.PdfReader')
    def test_extract_text_success(self, mock_pdf_reader_class, mock_pdf_reader):
        """Test successfully extracting text from PDF."""
        mock_pdf_reader_class.return_value = mock_pdf_reader

        from sebrae_scraper import extract_text_from_pdf
        result = extract_text_from_pdf()

        assert "John Doe" in result
        assert "Additional content" in result
        assert result == "This is a test PDF content with John Doe mentioned. Additional content here."

    @patch('sebrae_scraper.PdfReader')
    def test_extract_text_empty_pdf(self, mock_pdf_reader_class):
        """Test extracting from PDF with no text."""
        mock_reader = Mock()
        mock_page = Mock()
        mock_page.extract_text.return_value = ""
        mock_reader.pages = [mock_page]
        mock_pdf_reader_class.return_value = mock_reader

        from sebrae_scraper import extract_text_from_pdf
        result = extract_text_from_pdf()

        assert result == ""

    @patch('sebrae_scraper.PdfReader')
    def test_extract_text_single_page(self, mock_pdf_reader_class):
        """Test extracting from single page PDF."""
        mock_reader = Mock()
        mock_page = Mock()
        mock_page.extract_text.return_value = "Single page content"
        mock_reader.pages = [mock_page]
        mock_pdf_reader_class.return_value = mock_reader

        from sebrae_scraper import extract_text_from_pdf
        result = extract_text_from_pdf()

        assert result == "Single page content"


class TestSendMail:
    """Tests for send_mail function."""

    @patch('sebrae_scraper.smtplib.SMTP_SSL')
    @patch('sebrae_scraper.config')
    def test_send_mail_success(self, mock_config, mock_smtp):
        """Test successfully sending email."""
        mock_config.side_effect = lambda key: f"test_{key.lower()}"

        mock_server = Mock()
        mock_smtp.return_value = mock_server

        from sebrae_scraper import send_mail
        send_mail("<html><body>Test email</body></html>")

        mock_server.login.assert_called_once()
        mock_server.send_message.assert_called_once()
        mock_server.close.assert_called_once()

    @patch('sebrae_scraper.smtplib.SMTP_SSL')
    @patch('sebrae_scraper.config')
    def test_send_mail_smtp_error(self, mock_config, mock_smtp):
        """Test handling SMTP errors."""
        mock_config.side_effect = lambda key: f"test_{key.lower()}"

        mock_server = Mock()
        mock_server.login.side_effect = Exception("SMTP Error")
        mock_smtp.return_value = mock_server

        from sebrae_scraper import send_mail
        with pytest.raises(Exception, match="SMTP Error"):
            send_mail("<html><body>Test email</body></html>")

    @patch('sebrae_scraper.smtplib.SMTP_SSL')
    @patch('sebrae_scraper.config')
    def test_send_mail_message_content(self, mock_config, mock_smtp):
        """Test email message content is properly set."""
        mock_config.side_effect = lambda key: f"test_{key.lower()}"

        mock_server = Mock()
        mock_smtp.return_value = mock_server

        test_html = "<html><body>Name found in PDF</body></html>"
        from sebrae_scraper import send_mail
        send_mail(test_html)

        # Verify send_message was called
        assert mock_server.send_message.called
        mock_server.close.assert_called_once()
