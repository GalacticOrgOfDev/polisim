"""
Integration Tests for CBO Data Scraper

Phase 5.2: Comprehensive testing of data integration features
- Retry logic with exponential backoff
- Data validation checks
- Historical data tracking
- Change detection
- Cache fallback
"""

import pytest
import json
import time
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
import requests

from core.cbo_scraper import CBODataScraper


class TestRetryLogic:
    """Test retry logic with exponential backoff."""
    
    def test_successful_fetch_first_attempt(self):
        """Test successful fetch on first attempt."""
        scraper = CBODataScraper()
        
        with patch('requests.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.content = b"<html>GDP 30.5 trillion</html>"
            mock_response.raise_for_status = Mock()
            mock_get.return_value = mock_response
            
            response = scraper._request_with_retry("http://test.com", "test data")
            
            assert response is not None
            assert mock_get.call_count == 1
    
    def test_retry_on_timeout(self):
        """Test retry logic on timeout."""
        scraper = CBODataScraper()
        scraper.MAX_RETRIES = 3
        scraper.RETRY_DELAY = 0.1  # Fast for testing
        
        with patch('requests.get') as mock_get:
            mock_get.side_effect = requests.exceptions.Timeout()
            
            start_time = time.time()
            response = scraper._request_with_retry("http://test.com", "test data")
            elapsed = time.time() - start_time
            
            assert response is None
            assert mock_get.call_count == 3
            # Should have delays: 0.1s, 0.2s = 0.3s minimum
            assert elapsed >= 0.3
    
    def test_retry_on_connection_error(self):
        """Test retry logic on connection error."""
        scraper = CBODataScraper()
        scraper.MAX_RETRIES = 2
        scraper.RETRY_DELAY = 0.1
        
        with patch('requests.get') as mock_get:
            mock_get.side_effect = requests.exceptions.ConnectionError()
            
            response = scraper._request_with_retry("http://test.com", "test data")
            
            assert response is None
            assert mock_get.call_count == 2
    
    def test_no_retry_on_404(self):
        """Test that 404 errors don't retry."""
        scraper = CBODataScraper()
        
        with patch('requests.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 404
            mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(response=mock_response)
            mock_get.return_value = mock_response
            
            response = scraper._request_with_retry("http://test.com", "test data")
            
            assert response is None
            assert mock_get.call_count == 1  # No retries on 404
    
    def test_success_after_failures(self):
        """Test successful fetch after initial failures."""
        scraper = CBODataScraper()
        scraper.RETRY_DELAY = 0.1
        
        with patch('requests.get') as mock_get:
            # First two calls fail, third succeeds
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.content = b"<html>Test</html>"
            mock_response.raise_for_status = Mock()
            
            mock_get.side_effect = [
                requests.exceptions.Timeout(),
                requests.exceptions.ConnectionError(),
                mock_response
            ]
            
            response = scraper._request_with_retry("http://test.com", "test data")
            
            assert response is not None
            assert mock_get.call_count == 3


class TestDataValidation:
    """Test data validation checks."""
    
    def test_valid_data_passes(self):
        """Test that valid data passes validation."""
        scraper = CBODataScraper()
        
        data = {
            'gdp': 30.0,
            'debt': 35.0,
            'deficit': 1.5,
            'revenues': {'income_tax': 2.5, 'payroll_tax': 1.5},
            'spending': {'healthcare': 1.5, 'defense': 0.8, 'social_security': 1.2, 'other': 2.0},
        }
        
        is_valid, errors = scraper._validate_data(data)
        
        assert is_valid
        assert len(errors) == 0
    
    def test_invalid_gdp_fails(self):
        """Test that invalid GDP fails validation."""
        scraper = CBODataScraper()
        
        data = {
            'gdp': 100.0,  # Too high
            'debt': 35.0,
            'deficit': 1.5,
            'revenues': {},
            'spending': {},
        }
        
        is_valid, errors = scraper._validate_data(data)
        
        assert not is_valid
        assert len(errors) > 0
        assert 'GDP' in errors[0]
    
    def test_invalid_debt_fails(self):
        """Test that invalid debt fails validation."""
        scraper = CBODataScraper()
        
        data = {
            'gdp': 30.0,
            'debt': 100.0,  # Too high
            'deficit': 1.5,
            'revenues': {},
            'spending': {},
        }
        
        is_valid, errors = scraper._validate_data(data)
        
        assert not is_valid
        assert any('debt' in e.lower() for e in errors)
    
    def test_invalid_revenue_fails(self):
        """Test that invalid total revenue fails validation."""
        scraper = CBODataScraper()
        
        data = {
            'gdp': 30.0,
            'debt': 35.0,
            'deficit': 1.5,
            'revenues': {'income_tax': 100.0},  # Way too high
            'spending': {},
        }
        
        is_valid, errors = scraper._validate_data(data)
        
        assert not is_valid
        assert any('revenue' in e.lower() for e in errors)


class TestHistoricalData:
    """Test historical data tracking."""
    
    def test_history_entry_saved(self, tmp_path):
        """Test that data is saved to history."""
        # Use temporary path for history file
        history_file = tmp_path / "cbo_data_history.json"
        
        with patch.object(CBODataScraper, 'HISTORY_FILE', history_file):
            scraper = CBODataScraper()
            
            data = {
                'gdp': 30.0,
                'debt': 35.0,
                'deficit': 1.5,
                'revenues': {},
                'spending': {},
            }
            
            scraper._save_history_entry(data)
            
            # Check file was created
            assert history_file.exists()
            
            # Check data was saved
            with open(history_file, 'r') as f:
                history = json.load(f)
            
            assert len(history) == 1
            assert 'timestamp' in history[0]
            assert 'data' in history[0]
            assert 'hash' in history[0]
            assert history[0]['data']['gdp'] == 30.0
    
    def test_history_keeps_last_365_days(self, tmp_path):
        """Test that history only keeps last 365 days."""
        history_file = tmp_path / "cbo_data_history.json"
        
        with patch.object(CBODataScraper, 'HISTORY_FILE', history_file):
            scraper = CBODataScraper()
            
            # Add old entry (400 days ago)
            old_date = datetime.now() - timedelta(days=400)
            old_entry = {
                'timestamp': old_date.isoformat(),
                'data': {'gdp': 28.0},
                'hash': 'abc123'
            }
            scraper.history.append(old_entry)
            
            # Add recent entry
            recent_data = {'gdp': 30.0, 'debt': 35.0}
            scraper._save_history_entry(recent_data)
            
            # Check old entry was removed
            assert len(scraper.history) == 1
            assert scraper.history[0]['data']['gdp'] == 30.0
    
    def test_hash_generation(self):
        """Test data hash generation for change detection."""
        scraper = CBODataScraper()
        
        data1 = {'gdp': 30.0, 'debt': 35.0}
        data2 = {'gdp': 30.0, 'debt': 35.0}
        data3 = {'gdp': 31.0, 'debt': 35.0}
        
        hash1 = scraper._hash_data(data1)
        hash2 = scraper._hash_data(data2)
        hash3 = scraper._hash_data(data3)
        
        # Same data should have same hash
        assert hash1 == hash2
        
        # Different data should have different hash
        assert hash1 != hash3


class TestChangeDetection:
    """Test change detection."""
    
    def test_detect_gdp_change(self):
        """Test GDP change detection (>5%)."""
        scraper = CBODataScraper()
        
        # Add old entry
        old_entry = {
            'timestamp': datetime.now().isoformat(),
            'data': {'gdp': 30.0, 'debt': 35.0, 'deficit': 1.5},
            'hash': 'abc'
        }
        scraper.history.append(old_entry)
        
        # New data with 10% GDP increase
        new_data = {'gdp': 33.0, 'debt': 35.0, 'deficit': 1.5}
        
        changes = scraper._detect_changes(new_data)
        
        assert len(changes) > 0
        assert any('GDP' in change for change in changes)
        assert any('10.0%' in change for change in changes)
    
    def test_detect_debt_change(self):
        """Test debt change detection (>$1T)."""
        scraper = CBODataScraper()
        
        old_entry = {
            'timestamp': datetime.now().isoformat(),
            'data': {'gdp': 30.0, 'debt': 35.0, 'deficit': 1.5},
            'hash': 'abc'
        }
        scraper.history.append(old_entry)
        
        # New data with $2T debt increase
        new_data = {'gdp': 30.0, 'debt': 37.0, 'deficit': 1.5}
        
        changes = scraper._detect_changes(new_data)
        
        assert len(changes) > 0
        assert any('debt' in change.lower() for change in changes)
    
    def test_detect_deficit_change(self):
        """Test deficit change detection (>$500B)."""
        scraper = CBODataScraper()
        
        old_entry = {
            'timestamp': datetime.now().isoformat(),
            'data': {'gdp': 30.0, 'debt': 35.0, 'deficit': 1.5},
            'hash': 'abc'
        }
        scraper.history.append(old_entry)
        
        # New data with $700B deficit increase
        new_data = {'gdp': 30.0, 'debt': 35.0, 'deficit': 2.2}
        
        changes = scraper._detect_changes(new_data)
        
        assert len(changes) > 0
        assert any('deficit' in change.lower() for change in changes)
    
    def test_no_changes_detected(self):
        """Test no changes when data is stable."""
        scraper = CBODataScraper()
        
        old_entry = {
            'timestamp': datetime.now().isoformat(),
            'data': {'gdp': 30.0, 'debt': 35.0, 'deficit': 1.5},
            'hash': 'abc'
        }
        scraper.history.append(old_entry)
        
        # Same data
        new_data = {'gdp': 30.0, 'debt': 35.0, 'deficit': 1.5}
        
        changes = scraper._detect_changes(new_data)
        
        assert len(changes) == 0


class TestCacheFallback:
    """Test cache fallback mechanisms."""
    
    def test_uses_cache_on_network_failure(self, tmp_path):
        """Test that cache is used when network fails."""
        cache_file = tmp_path / "cbo_data_cache.json"
        
        # Create cache file
        cache_data = {
            'gdp': 28.0,
            'debt': 33.0,
            'revenues': {'income_tax': 2.0},
            'spending': {'healthcare': 1.5},
        }
        with open(cache_file, 'w') as f:
            json.dump(cache_data, f)
        
        with patch.object(CBODataScraper, 'CACHE_FILE', cache_file):
            scraper = CBODataScraper(use_cache=True)
            
            # Mock all network requests to fail
            with patch.object(scraper, '_get_gdp_data', side_effect=Exception("Network error")):
                # Should fall back to cache
                assert scraper.cached_data['gdp'] == 28.0
    
    def test_validation_failure_uses_cache(self, tmp_path):
        """Test that invalid data triggers cache fallback."""
        cache_file = tmp_path / "cbo_data_cache.json"
        history_file = tmp_path / "cbo_data_history.json"
        
        cache_data = {
            'gdp': 30.0,
            'debt': 35.0,
            'deficit': 1.5,
            'revenues': {'income_tax': 2.5},
            'spending': {'healthcare': 2.0},
            'interest_rate': 4.0,
            'last_updated': '2024-01-01',
            'data_source': 'Cache',
        }
        with open(cache_file, 'w') as f:
            json.dump(cache_data, f)
        
        with patch.object(CBODataScraper, 'CACHE_FILE', cache_file):
            with patch.object(CBODataScraper, 'HISTORY_FILE', history_file):
                scraper = CBODataScraper(use_cache=True)
                
                # Mock scraper methods to return invalid data
                with patch.object(scraper, '_get_gdp_data', return_value=999.0):  # Invalid
                    with patch.object(scraper, '_get_revenue_data', return_value={}):
                        with patch.object(scraper, '_get_spending_data', return_value={}):
                            with patch.object(scraper, '_get_national_debt', return_value=35.0):
                                with patch.object(scraper, '_get_interest_rate', return_value=4.0):
                                    data = scraper.get_current_us_budget_data()
                                    
                                    # Should return cached data due to validation failure
                                    assert data['gdp'] == 30.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
