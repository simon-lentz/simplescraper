import pytest
from unittest.mock import patch, MagicMock
from selenium.common.exceptions import WebDriverException

from scraper.web.proxy import ProxyReloadError


def test_init_managers(mock_web_controller):  # noqa:E501
    assert mock_web_controller.docker_manager is not None
    assert mock_web_controller.driver_manager is not None
    assert mock_web_controller.proxy_manager is not None


def test_get_connection_success(mock_web_controller):
    connection = mock_web_controller.get_connection("test")
    assert connection.name == "test"


def test_get_connection_failure(mock_web_controller):
    with pytest.raises(ValueError):
        mock_web_controller.get_connection("nonexistent")


def test_connect_success(mock_web_controller, mock_connection_data):
    with patch.object(mock_web_controller.proxy_manager, "get_proxy", return_value="127.0.0.3:8080"), \
         patch.object(mock_web_controller.docker_manager, "create_container", return_value=mock_connection_data.container), \
         patch.object(mock_web_controller.driver_manager, "create_driver", return_value=mock_connection_data.driver):  # noqa:E501
        mock_web_controller.connect()
        assert mock_connection_data.proxy == "127.0.0.3:8080"
        assert mock_connection_data.container is not None
        assert mock_connection_data.driver is not None


def test_connect_failure(mock_web_controller):
    with patch.object(mock_web_controller.proxy_manager, "get_proxy", side_effect=ProxyReloadError):  # noqa:E501
        mock_web_controller.proxy_manager.proxy_pool = {}
        mock_web_controller.connect()
        # Check that the error message was logged
        with open(mock_web_controller.logger.log_file, "r") as f:
            log_contents = f.read()
            assert "ProxyReloadError" in log_contents


def test_disconnect_success(mock_web_controller):
    mock_web_controller.disconnect()
    # Check that the release_proxy method was called
    with open(mock_web_controller.logger.log_file, "r") as f:
        log_contents = f.read()
        assert "release_proxy" in log_contents


def test_disconnect_failure(mock_web_controller):
    # Simulate a scenario where one of the managers is missing
    mock_web_controller.driver_manager = None
    with pytest.raises(RuntimeError):
        mock_web_controller.disconnect()


def test_make_request_success(mock_web_controller):
    mock_web_controller.make_request("test", "https://example.com")
    # Check that the increment_usage method was called
    with open(mock_web_controller.logger.log_file, "r") as f:
        log_contents = f.read()
        assert "increment_usage" in log_contents


def test_make_request_failure(mock_web_controller, mock_connection_data):
    mock_connection_data.driver.get.side_effect = WebDriverException("Driver error")
    mock_web_controller.make_request("test", "https://example.com")
    # Check that the error message was logged
    with open(mock_web_controller.logger.log_file, "r") as f:
        log_contents = f.read()
        assert "Driver error" in log_contents


def test_rotate_proxy_success(mock_web_controller, mock_connection_data):
    new_proxy = "127.0.0.2:8080"
    with patch.object(mock_web_controller.proxy_manager, "get_proxy", return_value=new_proxy), \
         patch.object(mock_web_controller.driver_manager, "create_driver", return_value=MagicMock()):  # noqa:E501
        mock_web_controller.rotate_proxy(mock_connection_data)
        assert mock_connection_data.proxy == new_proxy
        # Ensure the old driver was quit and a new driver was created
        mock_connection_data.driver.quit.assert_called_once()
        assert mock_connection_data.driver.get.call_count == 0  # ensure not used after quit  # noqa:E501


def test_rotate_proxy_failure(mock_web_controller, mock_connection_data):
    with patch.object(mock_web_controller.proxy_manager, "get_proxy", side_effect=ProxyReloadError):  # noqa:E501
        mock_web_controller.rotate_proxy(mock_connection_data)
        # Check that the error message was logged
        with open(mock_web_controller.logger.log_file, "r") as f:
            log_contents = f.read()
            assert "ProxyReloadError" in log_contents
