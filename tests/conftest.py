import pytest
from unittest.mock import patch, MagicMock
from docker.models.containers import Container
from selenium.webdriver.remote.webdriver import WebDriver

from scraper.config.logging import StructuredLogger
from scraper.web.connection import ConnectionData
from scraper.web.docker import DockerManager
from scraper.web.proxy import ProxyManager
from scraper.web.driver import DriverManager
from scraper.web.controller import WebController
from scraper.config.validator import (
    LoggingConfig,
    DockerConfig,
    DriverConfig,
    ProxyConfig,
)


# logging related fixtures
@pytest.fixture
def test_logging_config(tmp_path):
    return {
        "log_directory": tmp_path,
        "log_level": "INFO",
        "log_format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        "log_max_size": "10MB",
    }


@pytest.fixture
def mock_logging_config(test_logging_config):
    return LoggingConfig(**test_logging_config)


@pytest.fixture
def mock_structured_logger(mock_logging_config):
    return StructuredLogger(
        target_type="test",
        cfg=mock_logging_config,
    )


# docker related fixtures
@pytest.fixture
def mock_container():
    return MagicMock(spec=Container)


@pytest.fixture
def test_docker_config():
    return {
        "ports": [1234, 5678],
        "container_shm_size": "1g",
        "container_image": "test/image:latest",
        "remove_on_cleanup": True,
        "environment": {"TZ": "candyland"},
        "network_mode": "bridge",
        "resource_limits": {"cpu_quota": "0.5", "memory_limit": "1g"},
    }


@pytest.fixture
def mock_docker_config(test_docker_config):
    return DockerConfig(**test_docker_config)


@pytest.fixture
def mock_docker_manager(mock_structured_logger, mock_docker_config):
    return DockerManager(mock_structured_logger, mock_docker_config)


@pytest.fixture
def test_proxy_config(tmp_path):
    input_file = tmp_path / "test_pool.txt"
    input_file.write_text("127.0.0.2:8080\n")  # Write a sample proxy to the file
    return {
        "input_file": input_file,
        "test_url": "https://example.com/",
        "usage_limit": 100,
        "validation": False,  # must be disabled for testing
        "proxy_type": "HTTP",
        "authentication": None,
    }


@pytest.fixture
def mock_proxy_config(test_proxy_config):
    return ProxyConfig(**test_proxy_config)


@pytest.fixture
def mock_proxy_manager(mock_structured_logger, mock_proxy_config):
    with patch("scraper.web.proxy.requests.get") as mock_get:
        mock_get.return_value = MagicMock(status_code=200)
        return ProxyManager(mock_structured_logger, mock_proxy_config)


# driver related fixtures
@pytest.fixture
def mock_driver():
    driver = MagicMock(spec=WebDriver)
    driver.session_id = "test_session_id"
    driver.capabilities = {"browserName": "firefox"}
    # Mock the `quit` method to do nothing
    driver.quit = MagicMock(return_value=None)
    # Mock the `get` method to do nothing
    driver.get = MagicMock(return_value=None)
    return driver


@pytest.fixture
def test_driver_config():
    return {
        "host_network": "http://127.0.0.1",
        "option_args": ["--option-arg value"],
        "proxy": True,
        "retry_attempts": 3,
        "retry_interval": 2,
        "user_agent": None,
    }


@pytest.fixture
def mock_driver_config(test_driver_config):
    return DriverConfig(**test_driver_config)


@pytest.fixture
def mock_driver_manager(mock_structured_logger, mock_driver_config):
    return DriverManager(mock_structured_logger, mock_driver_config)


# webcontroller related fixtures
@pytest.fixture
def mock_web_controller(
    mock_structured_logger,
    mock_connection_data,  # noqa:E501
    mock_docker_config,
    mock_proxy_config,
    mock_driver_config,
):  # noqa:E501
    controller = WebController(
        logger=mock_structured_logger,
        connections={
            "test": mock_connection_data,
        },
    )
    controller.init_docker_manager(mock_docker_config)
    controller.init_proxy_manager(mock_proxy_config)
    controller.init_driver_manager(mock_driver_config)
    return controller


########################################################################
########################################################################
# misc. helper fixtures
@pytest.fixture
def test_target_config():
    return {"target_name": "test", "target_domain": "https://testing.com/"}


@pytest.fixture
def mock_init_connection_data():
    return ConnectionData(
        name="init test",
        port="4444",
    )


@pytest.fixture
def mock_connection_data(mock_container, mock_driver):
    return ConnectionData(
        name="test",
        port="8080",
        proxy="127.0.0.1:8080",
        container=mock_container,
        driver=mock_driver,
    )
