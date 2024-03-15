import re
import pytest
from unittest.mock import MagicMock, patch
from scraper.web.proxy import UsageError, ProxyReloadError


def test_create_pool(mock_proxy_manager):
    assert isinstance(mock_proxy_manager.proxy_pool, dict)
    assert all(isinstance(key, str) and isinstance(value, tuple) for key, value in mock_proxy_manager.proxy_pool.items())  # noqa:E501


def test_get_proxy_success(mock_proxy_manager):
    proxy = mock_proxy_manager.get_proxy()
    assert proxy in mock_proxy_manager.proxy_pool
    usage, in_use = mock_proxy_manager.proxy_pool[proxy]
    assert usage == 1 and in_use


def test_get_proxy_failure(mock_proxy_manager):
    # Exhaust all proxies
    for _ in range(len(mock_proxy_manager.proxy_pool)):
        mock_proxy_manager.get_proxy()
    with pytest.raises(Exception):
        mock_proxy_manager.get_proxy()


def test_increment_usage_success(mock_proxy_manager):
    proxy = mock_proxy_manager.get_proxy()
    mock_proxy_manager.increment_usage(proxy)
    usage, _ = mock_proxy_manager.proxy_pool[proxy]
    assert usage == 2


def test_increment_usage_failure(mock_proxy_manager):
    proxy = mock_proxy_manager.get_proxy()
    # Exhaust usage limit
    for _ in range(mock_proxy_manager.usage_limit - 1):
        mock_proxy_manager.increment_usage(proxy)
    with pytest.raises(UsageError):
        mock_proxy_manager.increment_usage(proxy)


def test_release_proxy(mock_proxy_manager):
    proxy = mock_proxy_manager.get_proxy()
    mock_proxy_manager.release_proxy(proxy)
    _, in_use = mock_proxy_manager.proxy_pool[proxy]
    assert not in_use


def test_delete_proxy(mock_proxy_manager):
    proxy = mock_proxy_manager.get_proxy()
    mock_proxy_manager.delete_proxy(proxy)
    assert proxy not in mock_proxy_manager.proxy_pool


# Test validation with mocked network requests
@patch('scraper.web.proxy.requests.get')
def test_validate_proxies_success(mock_get, mock_proxy_manager):
    mock_get.return_value = MagicMock(status_code=200)
    validated_proxies = mock_proxy_manager._validate_proxies()
    assert len(validated_proxies) == len(mock_proxy_manager._format_pool())


@patch('scraper.web.proxy.requests.get')
def test_validate_proxies_failure(mock_get, mock_proxy_manager):
    mock_get.side_effect = Exception("Failed to connect")
    with pytest.raises(ValueError):
        mock_proxy_manager._validate_proxies()


# Test formatting
def test_format_pool_success(mock_proxy_manager):
    formatted_proxies = mock_proxy_manager._format_pool()
    assert all(re.match(r'^\d+\.\d+\.\d+\.\d+:\d+$', proxy) for proxy in formatted_proxies)  # noqa:E501


def test_format_pool_failure(mock_proxy_manager):
    with patch('scraper.web.proxy.ProxyManager._load_proxies', return_value=["invalid_proxy"]):  # noqa:E501
        with pytest.raises(ValueError):
            mock_proxy_manager._format_pool()


# Test proxy reload success
def test_proxy_reload_success(mock_proxy_manager):
    # Simulate exhausting the initial proxy pool
    for _ in range(len(mock_proxy_manager.proxy_pool)):
        mock_proxy_manager.get_proxy()

    # Mock the behavior of loading and validating new proxies
    new_proxies = ["1.2.3.4:8080", "5.6.7.8:8080"]
    with patch('scraper.web.proxy.ProxyManager._load_proxies', return_value=new_proxies), \
         patch('scraper.web.proxy.ProxyManager._validate_proxies', return_value=new_proxies):  # noqa:E501
        reloaded_proxy = mock_proxy_manager.get_proxy()

    assert reloaded_proxy in new_proxies
    assert len(mock_proxy_manager.proxy_pool) - 1 == len(new_proxies)


# Test proxy reload failure with no new proxies available
def test_proxy_reload_failure_no_new_proxies(mock_proxy_manager):
    # Simulate exhausting the initial proxy pool
    for _ in range(len(mock_proxy_manager.proxy_pool)):
        mock_proxy_manager.get_proxy()

    with patch('scraper.web.proxy.ProxyManager._load_proxies', return_value=[]), \
         pytest.raises(ProxyReloadError, match="No new proxies available for reloading the pool"):  # noqa:E501
        mock_proxy_manager.get_proxy()


@patch('scraper.web.proxy.requests.get')
def test_proxy_reload_with_validation(mock_get, mock_proxy_manager):
    mock_proxy_manager.validation = True
    for _ in range(len(mock_proxy_manager.proxy_pool)):
        mock_proxy_manager.get_proxy()
    new_proxies = ["11.22.33.44:4080", "invalid_proxy"]
    mock_get.side_effect = [MagicMock(status_code=200), Exception("Failed to connect")]  # noqa:E501
    with patch('scraper.web.proxy.ProxyManager._load_proxies', return_value=new_proxies):  # noqa:E501
        _ = mock_proxy_manager.get_proxy()
    assert len(mock_proxy_manager.proxy_pool) == 2
