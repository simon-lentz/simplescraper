import pytest

from pathlib import Path
from unittest.mock import patch
from scraper.config.validator import (
    LoggingConfig,
    TargetConfig,
    DockerConfig,
    ProxyConfig,
    DriverConfig,
    load_config,
    check_network_connectivity,
    check_disk_space,
    check_cpu_usage,
    check_memory_usage,
    ConfigError,
)


# Mock the network connectivity check
def test_check_network_connectivity_success():
    with patch("requests.get") as mock_get:
        mock_get.return_value.status_code = 200
        assert check_network_connectivity("https://www.google.com")


def test_check_network_connectivity_failure():
    with patch("requests.get") as mock_get:
        mock_get.return_value.status_code = 404
        with pytest.raises(ValueError):
            check_network_connectivity("https://invalid.url")


# Mock the disk space check
def test_check_disk_space_success(tmp_path):
    with patch("shutil.disk_usage") as mock_disk_usage:
        mock_disk_usage.return_value = (100, 50, 50)
        assert check_disk_space(1, str(tmp_path))


def test_check_disk_space_failure(tmp_path):
    with patch("shutil.disk_usage") as mock_disk_usage:
        mock_disk_usage.return_value = (100, 99, 1)
        with pytest.raises(ValueError):
            check_disk_space(2, str(tmp_path))


# Mock the CPU usage check
def test_check_cpu_usage_success():
    with patch("psutil.cpu_percent") as mock_cpu_percent:
        mock_cpu_percent.return_value = 50
        assert check_cpu_usage(0.99)


def test_check_cpu_usage_failure():
    with patch("psutil.cpu_percent") as mock_cpu_percent:
        mock_cpu_percent.return_value = 100
        with pytest.raises(ValueError):
            check_cpu_usage()


# Mock the memory usage check
def test_check_memory_usage_success():
    with patch("psutil.virtual_memory") as mock_virtual_memory:
        mock_virtual_memory.return_value.available = 90
        mock_virtual_memory.return_value.total = 100
        assert check_memory_usage(0.99)


def test_check_memory_usage_failure():
    with patch("psutil.virtual_memory") as mock_virtual_memory:
        mock_virtual_memory.return_value.available = 1
        mock_virtual_memory.return_value.total = 100
        with pytest.raises(ValueError):
            check_memory_usage()


@pytest.mark.parametrize(
    "mod_config, expected_validity",
    [
        ({}, True),
        ({"log_directory": Path("./fail")}, False),
        ({"log_directory": Path("./files/proxies/example_pool.txt")}, False),
        ({"log_directory": Path("./files/does_not_exist/")}, False),
        ({"log_level": "DEBUG"}, True),
        ({"log_level": "INFO"}, True),
        ({"log_level": "WARNING"}, True),
        ({"log_level": "ERROR"}, True),
        ({"log_level": "CRITICAL"}, True),
        ({"log_level": "SWAG"}, False),
        ({"log_format": ""}, False),
        ({"log_max_size": "10MB"}, True),
        ({"log_max_size": "5G"}, True),
        ({"log_max_size": "100K"}, True),
        ({"log_max_size": "1TB"}, False),  # Not a valid unit
        ({"log_max_size": "10"}, False),  # Missing unit
        ({"log_max_size": "10MBB"}, False),  # Invalid unit
    ],
)  # Parametrized tests for LoggingConfig
def test_logging_config_validation(test_logging_config, mod_config, expected_validity):
    config = {**test_logging_config, **mod_config}
    if expected_validity:
        try:
            LoggingConfig(**config)
        except ValueError:
            pytest.fail("LoggingConfig raised ValueError unexpectedly!")
    else:
        with pytest.raises(ValueError):
            LoggingConfig(**config)


@pytest.mark.parametrize(
    "mod_config, expected_validity",
    [
        ({}, True),  # valid config
        ({"target_name": ""}, False),
        ({"target_domain": "testing.com"}, False),
        ({"target_domain": "http://testing.com"}, True),
    ],
)  # Parametrized tests for TargetConfig
def test_target_config_validation(test_target_config, mod_config, expected_validity):
    config = {**test_target_config, **mod_config}
    if expected_validity:
        try:
            TargetConfig(**config)
        except ValueError:
            pytest.fail("TargetConfig raised ValueError unexpectedly!")
    else:
        with pytest.raises(ValueError):
            TargetConfig(**config)


@pytest.mark.parametrize(
    "mod_config, expected_validity",
    [
        ({}, True),
        ({"ports": [-1]}, False),
        ({"ports": []}, False),
        ({"ports": [0]}, True),
        ({"ports": [65560]}, False),
        ({"ports": [65535]}, True),
        ({"container_shm_size": "1GB"}, True),
        ({"container_shm_size": "1024K"}, True),
        ({"container_shm_size": "2G"}, True),
        ({"container_shm_size": "2GB"}, True),
        ({"container_shm_size": "2000MB"}, True),
        ({"container_shm_size": "1T"}, False),
        ({"container_image": ""}, False),
        ({"remove_on_cleanup": True}, True),
        ({"remove_on_cleanup": False}, True),
        ({"environment": {"TZ": "America/New_York"}}, True),
        ({"environment": {"INVALID": 123}}, False),
        ({"network_mode": "host"}, True),
        ({"network_mode": "invalid"}, False),
        ({"resource_limits": {"cpu_quota": "0.5", "memory_limit": "1g"}}, True),
        ({"resource_limits": {"cpu_quota": "1.1", "memory_limit": "1g"}}, False),
        ({"resource_limits": {"cpu_quota": "0.5", "memory_limit": "2tb"}}, False),
    ],
)
def test_docker_config_validation(test_docker_config, mod_config, expected_validity):
    config = {**test_docker_config, **mod_config}
    if expected_validity:
        try:
            DockerConfig(**config)
        except ValueError:
            pytest.fail("DockerConfig raised ValueError unexpectedly!")
    else:
        with pytest.raises(ValueError):
            DockerConfig(**config)


@pytest.mark.parametrize(
    "mod_config, expected_validity",
    [
        ({}, True),
        ({"input_file": Path("./fail.txt")}, False),
        ({"input_file": Path("./files/proxies/test.txt")}, False),
        ({"input_file": Path("./files/proxies/")}, False),
        ({"input_file": Path("./files/proxies/test")}, False),
        ({"test_url": "example.com"}, False),
        ({"usage_limit": -5}, False),
        ({"usage_limit": 0}, False),
        ({"validation": False}, True),
        ({"proxy_type": "SOCKS4"}, True),
        ({"proxy_type": "INVALID"}, False),
        ({"authentication": {"username": "user", "password": "pass"}}, True),
        ({"authentication": {"username": "user"}}, False),
        ({"authentication": {"password": "pass"}}, False),
    ],
)
def test_proxy_config_validation(test_proxy_config, mod_config, expected_validity):
    config = {**test_proxy_config, **mod_config}
    if expected_validity:
        try:
            ProxyConfig(**config)
        except ValueError:
            pytest.fail("ProxyConfig raised ValueError unexpectedly!")
    else:
        with pytest.raises(ValueError):
            ProxyConfig(**config)


@pytest.mark.parametrize(
    "mod_config, expected_validity",
    [
        ({}, True),
        ({"host_network": ""}, False),
        ({"option_args": []}, True),
        ({"option_args": [""]}, False),
        ({"proxy": False}, True),
        ({"retry_attempts": -1}, False),
        ({"retry_attempts": 0}, False),
        ({"retry_attempts": 1}, True),
        ({"retry_interval": -1}, False),
        ({"retry_interval": 0}, False),
        ({"retry_interval": 1}, True),
        ({"user_agent": None}, True),
        ({"user_agent": ""}, False),
        ({"user_agent": "Mozilla/5.0"}, True),
    ],
)
def test_driver_config_validation(test_driver_config, mod_config, expected_validity):
    config = {**test_driver_config, **mod_config}
    if expected_validity:
        try:
            DriverConfig(**config)
        except ValueError:
            pytest.fail("DriverConfig raised ValueError unexpectedly!")
    else:
        with pytest.raises(ValueError):
            DriverConfig(**config)


def test_load_config_invalid_yaml(tmp_path):
    config_file = tmp_path / "invalid_config.yaml"
    config_file.write_text("invalid: yaml: content")
    with pytest.raises(ConfigError) as exc_info:
        load_config(config_file)
    assert "Error parsing configuration" in str(exc_info.value)


def test_load_config_invalid_json(tmp_path):
    config_file = tmp_path / "invalid_config.json"
    config_file.write_text("invalid: json: content")
    with pytest.raises(ConfigError) as exc_info:
        load_config(config_file)
    assert "Error parsing configuration" in str(exc_info.value)


def test_load_config_invalid_toml(tmp_path):
    config_file = tmp_path / "invalid_config.toml"
    config_file.write_text("invalid = yaml: content")
    with pytest.raises(ConfigError) as exc_info:
        load_config(config_file)
    assert "Error parsing configuration" in str(exc_info.value)
