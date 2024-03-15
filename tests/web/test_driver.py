import time
import pytest
from unittest.mock import patch
from selenium.common.exceptions import WebDriverException


def test_create_driver_success(mock_driver_manager, mock_connection_data, mock_driver):  # noqa:E501
    with patch('selenium.webdriver.Remote', return_value=mock_driver) as mock_remote:
        driver = mock_driver_manager.create_driver(mock_connection_data)
        assert driver == mock_driver
        mock_remote.assert_called_once()


def test_create_driver_failure(mock_driver_manager, mock_connection_data):
    with patch('selenium.webdriver.Remote', side_effect=WebDriverException("Failed to create driver")), \
         patch.object(time, 'sleep', return_value=None) as mock_sleep:  # noqa:E501:  # noqa:E501
        with pytest.raises(WebDriverException):
            mock_driver_manager.create_driver(mock_connection_data)
        assert mock_sleep.call_count == 2


def test_quit_driver_success(mock_driver_manager, mock_driver):
    mock_driver_manager.quit_driver(mock_driver)
    mock_driver.quit.assert_called_once()


def test_quit_driver_failure(mock_driver_manager, mock_driver):
    mock_driver.quit.side_effect = WebDriverException("Failed to quit driver")
    mock_driver_manager.quit_driver(mock_driver)
    mock_driver.quit.assert_called_once()


# Test proxy settings
def test_create_driver_with_proxy(mock_driver_manager, mock_connection_data, mock_driver):  # noqa:E501
    mock_driver_manager.proxy_server = True
    with patch('selenium.webdriver.Remote', return_value=mock_driver) as mock_remote:
        mock_driver_manager.create_driver(mock_connection_data)
        mock_remote.assert_called_once()
        opts = mock_remote.call_args[1]['options']
        assert f"--proxy-server={mock_connection_data.proxy}" in opts.arguments


# Test retry mechanism with mocked time.sleep to avoid delay
def test_create_driver_retry(mock_driver_manager, mock_connection_data, mock_driver):
    with patch('selenium.webdriver.Remote', side_effect=[WebDriverException("Failed to create driver"), mock_driver]), \
         patch.object(time, 'sleep', return_value=None) as mock_sleep:  # noqa:E501
        driver = mock_driver_manager.create_driver(mock_connection_data)
        assert driver is mock_driver
        assert mock_sleep.call_count == 1  # time.sleep was called once for retry


# Test driver options
def test_create_driver_options(mock_driver_manager, mock_connection_data, mock_driver):
    mock_driver_manager.driver_options = ["--headless", "--window-size=1920,1080"]
    with patch('selenium.webdriver.Remote', return_value=mock_driver) as mock_remote:
        mock_driver_manager.create_driver(mock_connection_data)
        mock_remote.assert_called_once()
        opts = mock_remote.call_args[1]['options']
        assert "--headless" in opts.arguments
        assert "--window-size=1920,1080" in opts.arguments


# Test timeout
def test_create_driver_timeout(mock_driver_manager, mock_connection_data):
    with patch('selenium.webdriver.Remote', side_effect=WebDriverException("Failed to create driver")), \
         patch.object(time, 'sleep', return_value=None) as mock_sleep:  # noqa:E501
        with pytest.raises(WebDriverException):
            mock_driver_manager.create_driver(mock_connection_data)
        assert mock_sleep.call_count == 2
        # Check that the warning and error messages were logged as expected
        with open(mock_driver_manager.logger.log_file, "r") as f:
            log_content = f.read()
            warning_count = log_content.count("Failed to create driver with proxy")
            error_count = log_content.count("Failed to create driver for target")
            assert warning_count == mock_driver_manager.max_attempts
            assert error_count == 1


# Test logging
def test_create_driver_logging(mock_driver_manager, mock_connection_data, mock_driver):
    with patch('selenium.webdriver.Remote', return_value=mock_driver):
        mock_driver_manager.create_driver(mock_connection_data)
        expected_calls = [
            f"WebDriver session created with session ID: {mock_driver.session_id}",  # noqa:E501
            f"WebDriver session created with capabilities: {mock_driver.capabilities}"  # noqa:E501
        ]
        # Check that the expected logging calls were made
        with open(mock_driver_manager.logger.log_file, "r") as f:
            log_content = f.read()
            assert all(expected_call in log_content for expected_call in expected_calls)  # noqa:E501
