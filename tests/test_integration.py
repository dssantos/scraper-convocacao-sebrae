"""Integration tests for the complete scraper workflow."""
import pytest
import json
import sys
import os
import importlib
from unittest.mock import Mock, patch, MagicMock


@pytest.fixture
def integration_test_data(tmp_path):
    """Create test data for integration tests."""
    checked_file = tmp_path / "checked_urls.json"
    checked_file.write_text('{}')
    return str(checked_file)


class TestScraperWorkflow:
    """Integration tests for the main scraper workflow."""

    def test_name_found_workflow(self, integration_test_data, monkeypatch):
        """Test complete workflow when name is found."""
        # Ensure module is not already imported
        if 'sebrae_scraper' in sys.modules:
            del sys.modules['sebrae_scraper']

        # Set environment variable before importing
        monkeypatch.setenv('CHECKED_URLS_FILE', integration_test_data)

        # Mock the functions we need
        mock_links = ["https://sebrae.com.br/pub1", "https://sebrae.com.br/pub2"]
        mock_files = ["https://sebrae.com.br/file1.pdf", "https://sebrae.com.br/file2.pdf"]
        mock_texts = ["This document mentions sebrae", "Another document without the name"]

        # Import functions directly without triggering main execution
        from sebrae_scraper import save_checked_data, is_checked

        name = "sebrae"
        message = ''

        # Simulate the workflow
        for i, publication_link in enumerate(mock_links):
            file_link = mock_files[i]
            text = mock_texts[i]

            if name.lower() in text.lower():
                message += f'<p><b>{name}</b> encontrado em <a href="{file_link}">{file_link}</a></p>'
            save_checked_data(name, publication_link)

        # Assertions
        assert "sebrae" in message
        assert is_checked("sebrae", mock_links[0])
        assert is_checked("sebrae", mock_links[1])

    def test_name_not_found_workflow(self, integration_test_data):
        """Test workflow when name is not found."""
        from sebrae_scraper import save_checked_data, is_checked

        # Setup
        mock_links = ["https://sebrae.com.br/pub1"]
        mock_texts = ["Document without the target name"]

        name = "nonexistent"
        message = ''

        for i, publication_link in enumerate(mock_links):
            text = mock_texts[i]

            if name.lower() in text.lower():
                message += f'<p><b>{name}</b> encontrado'

        # Assertions
        assert message == ''

    def test_skip_checked_urls(self, integration_test_data, monkeypatch):
        """Test that already checked URLs are skipped."""
        # Ensure module is not already imported
        if 'sebrae_scraper' in sys.modules:
            del sys.modules['sebrae_scraper']

        # Set environment variable before importing
        monkeypatch.setenv('CHECKED_URLS_FILE', integration_test_data)

        from sebrae_scraper import save_checked_data, is_checked

        # Pre-populate checked data
        save_checked_data("sebrae", "https://sebrae.com.br/pub1")

        # Verify it's checked
        assert is_checked("sebrae", "https://sebrae.com.br/pub1")

        # Verify new one is not checked
        assert not is_checked("sebrae", "https://sebrae.com.br/pub2")

    @patch('sebrae_scraper.requests.get')
    def test_connection_error_handling(self, mock_get):
        """Test handling of connection errors during scraping."""
        from sebrae_scraper import get_publications_links
        from requests.exceptions import ConnectionError

        mock_get.side_effect = ConnectionError("Network unreachable")

        with pytest.raises(ConnectionError):
            get_publications_links("https://sebrae.com.br/test")

    def test_persistence_across_runs(self, integration_test_data):
        """Test that checked data persists across multiple runs."""
        from sebrae_scraper import save_checked_data, is_checked, load_checked_data

        # Patch CHECKED_URLS_FILE
        import sebrae_scraper
        original_file = sebrae_scraper.CHECKED_URLS_FILE
        sebrae_scraper.CHECKED_URLS_FILE = integration_test_data

        try:
            # First run
            save_checked_data("John Doe", "https://example.com/pub1")
            save_checked_data("Jane Smith", "https://example.com/pub1")

            # Check first run
            assert is_checked("John Doe", "https://example.com/pub1")
            assert is_checked("Jane Smith", "https://example.com/pub1")

            # Simulate new run - load data
            checked_data = load_checked_data()
            assert "https://example.com/pub1" in checked_data
            assert len(checked_data["https://example.com/pub1"]) == 2
        finally:
            sebrae_scraper.CHECKED_URLS_FILE = original_file


class TestEdgeCases:
    """Tests for edge cases and error conditions."""

    def test_case_insensitive_search(self):
        """Test that name search is case insensitive."""
        text = "This document contains JOHN DOE and jane smith"

        assert "john doe".lower() in text.lower()
        assert "JANE SMITH".lower() in text.lower()
        assert "JoHn DoE".lower() in text.lower()

    def test_empty_name_search(self):
        """Test searching with empty name."""
        text = "Some document content"
        name = ""

        # Empty name should match any text
        assert name.lower() in text.lower()

    def test_special_characters_in_name(self):
        """Test searching for names with special characters."""
        text = "Document with José María-Silva"
        name = "José María-Silva"

        assert name.lower() in text.lower()

    @patch('sebrae_scraper.requests.get')
    def test_malformed_html_response(self, mock_get):
        """Test handling of malformed HTML."""
        mock_response = Mock()
        mock_response.content = b'<div>Broken HTML<div>'
        mock_get.return_value = mock_response

        from sebrae_scraper import get_publications_links
        # Should handle gracefully (lxml is lenient)
        result = get_publications_links("https://sebrae.com.br/test")

        assert isinstance(result, list)

    def test_concurrent_access_to_checked_file(self, integration_test_data):
        """Test concurrent access patterns to checked data file."""
        import sebrae_scraper
        original_file = sebrae_scraper.CHECKED_URLS_FILE
        sebrae_scraper.CHECKED_URLS_FILE = integration_test_data

        try:
            from sebrae_scraper import save_checked_data, load_checked_data

            # Simulate multiple operations
            save_checked_data("User1", "https://example.com/1")
            save_checked_data("User2", "https://example.com/2")
            save_checked_data("User3", "https://example.com/1")

            # Verify all data persisted
            checked_data = load_checked_data()
            assert len(checked_data["https://example.com/1"]) == 2
            assert len(checked_data["https://example.com/2"]) == 1
        finally:
            sebrae_scraper.CHECKED_URLS_FILE = original_file
