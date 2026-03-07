"""Unit tests for utility functions."""
import os
import json
import pytest
from unittest.mock import patch, mock_open


@pytest.fixture
def mock_checked_file(tmp_path):
    """Create a mock checked file path."""
    return str(tmp_path / "checked_urls.json")


class TestLoadCheckedData:
    """Tests for load_checked_data function."""

    def test_load_existing_file(self, mock_checked_file, sample_checked_data):
        """Test loading data from existing file."""
        # Create test file
        with open(mock_checked_file, 'w') as f:
            json.dump(sample_checked_data, f)

        with patch('sebrae_scraper.CHECKED_URLS_FILE', mock_checked_file):
            from sebrae_scraper import load_checked_data
            result = load_checked_data()

        assert result == sample_checked_data

    def test_load_nonexistent_file(self, mock_checked_file):
        """Test loading when file doesn't exist."""
        with patch('sebrae_scraper.CHECKED_URLS_FILE', mock_checked_file):
            from sebrae_scraper import load_checked_data
            result = load_checked_data()

        assert result == {}

    def test_load_empty_file(self, mock_checked_file):
        """Test loading from empty JSON file."""
        with open(mock_checked_file, 'w') as f:
            json.dump({}, f)

        with patch('sebrae_scraper.CHECKED_URLS_FILE', mock_checked_file):
            from sebrae_scraper import load_checked_data
            result = load_checked_data()

        assert result == {}


class TestSaveCheckedData:
    """Tests for save_checked_data function."""

    def test_save_new_url_and_name(self, mock_checked_file):
        """Test saving new URL and name combination."""
        url = "https://example.com/new"
        name = "Alice Johnson"

        with patch('sebrae_scraper.CHECKED_URLS_FILE', mock_checked_file):
            from sebrae_scraper import save_checked_data
            save_checked_data(name, url)

        with open(mock_checked_file, 'r') as f:
            result = json.load(f)

        assert url in result
        assert name in result[url]
        assert len(result[url]) == 1

    def test_save_existing_url_new_name(self, mock_checked_file, sample_checked_data):
        """Test adding new name to existing URL."""
        # Create file with sample data
        with open(mock_checked_file, 'w') as f:
            json.dump(sample_checked_data, f)

        url = "https://example.com/pub1"
        new_name = "Bob Wilson"

        with patch('sebrae_scraper.CHECKED_URLS_FILE', mock_checked_file):
            from sebrae_scraper import save_checked_data
            save_checked_data(new_name, url)

        with open(mock_checked_file, 'r') as f:
            result = json.load(f)

        assert new_name in result[url]
        assert "John Doe" in result[url]  # Original name still there
        assert len(result[url]) == 3

    def test_save_duplicate_name_url(self, mock_checked_file, sample_checked_data):
        """Test saving duplicate name+URL combination."""
        # Create file with sample data
        with open(mock_checked_file, 'w') as f:
            json.dump(sample_checked_data, f)

        url = "https://example.com/pub1"
        name = "John Doe"  # Already exists

        with patch('sebrae_scraper.CHECKED_URLS_FILE', mock_checked_file):
            from sebrae_scraper import save_checked_data
            save_checked_data(name, url)

        with open(mock_checked_file, 'r') as f:
            result = json.load(f)

        # Should not duplicate
        assert result[url].count(name) == 1
        assert len(result[url]) == 2


class TestIsChecked:
    """Tests for is_checked function."""

    def test_checked_exists(self, mock_checked_file, sample_checked_data):
        """Test checking existing name+URL combination."""
        with open(mock_checked_file, 'w') as f:
            json.dump(sample_checked_data, f)

        with patch('sebrae_scraper.CHECKED_URLS_FILE', mock_checked_file):
            from sebrae_scraper import is_checked
            result = is_checked("John Doe", "https://example.com/pub1")

        assert result is True

    def test_checked_different_name(self, mock_checked_file, sample_checked_data):
        """Test checking non-existent name for existing URL."""
        with open(mock_checked_file, 'w') as f:
            json.dump(sample_checked_data, f)

        with patch('sebrae_scraper.CHECKED_URLS_FILE', mock_checked_file):
            from sebrae_scraper import is_checked
            result = is_checked("Alice Johnson", "https://example.com/pub1")

        assert result is False

    def test_checked_different_url(self, mock_checked_file, sample_checked_data):
        """Test checking name for non-existent URL."""
        with open(mock_checked_file, 'w') as f:
            json.dump(sample_checked_data, f)

        with patch('sebrae_scraper.CHECKED_URLS_FILE', mock_checked_file):
            from sebrae_scraper import is_checked
            result = is_checked("John Doe", "https://example.com/unknown")

        assert result is False

    def test_checked_empty_file(self, mock_checked_file):
        """Test checking against empty data file."""
        with open(mock_checked_file, 'w') as f:
            json.dump({}, f)

        with patch('sebrae_scraper.CHECKED_URLS_FILE', mock_checked_file):
            from sebrae_scraper import is_checked
            result = is_checked("John Doe", "https://example.com/pub1")

        assert result is False

    def test_checked_no_file(self, mock_checked_file):
        """Test checking when file doesn't exist."""
        with patch('sebrae_scraper.CHECKED_URLS_FILE', mock_checked_file):
            from sebrae_scraper import is_checked
            result = is_checked("John Doe", "https://example.com/pub1")

        assert result is False
