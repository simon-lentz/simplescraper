import re
import yaml
import json
import toml
import docker
import shutil
import psutil
import requests

from pathlib import Path
from typing import Dict, List, Optional
from requests.exceptions import ConnectionError
from docker.errors import APIError, ImageNotFound
from pydantic import (
    BaseModel, ConfigDict, ValidationError, field_validator, Field,
)

opts = ConfigDict(
    extra="forbid",
    validate_assignment=True,
    str_to_lower=True,
    str_strip_whitespace=True,
    str_min_length=1,
)


class LoggingConfig(BaseModel):
    """
    Pydantic model for logging configuration.
    """

    model_config = opts

    log_directory: Path
    log_level: str
    log_format: str
    log_max_size: str = Field(..., pattern=r"^\d+[KMGBkmgb][Bb]?$")

    @field_validator("log_level")
    @classmethod
    def check_valid_log_level(cls, v: str) -> str:
        level = v.upper()
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if level in valid_levels:
            return level
        else:
            raise ValueError(
                f"Log level '{v}' is not supported. Valid levels are: {', '.join(valid_levels)}"  # noqa:E501
            )  # noqa:E501

    @field_validator("log_directory")
    @classmethod
    def check_directory_exists(cls, v: Path) -> Path:
        if v.exists() and v.is_dir():
            return v
        else:
            raise ValueError(f"Log file directory '{v}' not found")


class DockerConfig(BaseModel):
    """
    Pydantic model for Docker configuration.
    """

    model_config = opts

    ports: List[int]
    container_shm_size: str = Field(..., pattern=r"^\d+[KMGBkmgb][Bb]?$")
    container_image: str
    remove_on_cleanup: bool = True
    environment: Optional[Dict[str, str]] = None
    network_mode: str = "bridge"
    resource_limits: Optional[Dict[str, str]] = None

    @field_validator("ports")
    @classmethod
    def check_ports(cls, v):
        if len(v) == 0:
            raise ValueError("Must specify at least one port value")
        for port in v:
            if not (0 <= port <= 65535):
                raise ValueError("Port value out of valid range")
        return v

    @classmethod
    def validate_docker_environment(cls, container_image: str):
        client = docker.from_env()
        try:
            if not client.ping():
                raise ValueError("Docker daemon is not running")
            client.images.get(container_image)
        except ImageNotFound:
            raise ValueError(f"Docker image '{container_image}' not found")
        except APIError:
            raise ValueError("Docker daemon is not running")

    @field_validator("resource_limits")
    @classmethod
    def check_resource_limits(cls, v: Dict[str, str]) -> Dict[str, str]:
        cpu_quota = v.get("cpu_quota")
        memory_limit = v.get("memory_limit")
        if cpu_quota is not None:
            try:
                cpu_quota = float(cpu_quota)
                if not 0 <= cpu_quota <= 1:
                    raise ValueError("CPU quota must be between 0 and 1")
            except ValueError:
                raise ValueError("CPU quota must be a valid number between 0 and 1")
        if memory_limit is not None:
            if not re.match(r"^\d+[KMGBkmgb][Bb]?$", memory_limit.upper()):
                raise ValueError("Invalid memory limit format")
        return v

    @field_validator("environment")
    @classmethod
    def check_environment(cls, v: Dict[str, str]) -> Dict[str, str]:
        if not isinstance(v, dict):
            raise ValueError("Environment must be a dictionary")
        for key, value in v.items():
            if not isinstance(key, str) or not isinstance(value, str):
                raise ValueError("Environment keys and values must be strings")
        return v

    @field_validator("network_mode")
    @classmethod
    def check_network(cls, v: str) -> str:
        allowed = [
            "bridge",
            "host",
            "none",
        ]  # Add more custom networks if needed
        if v not in allowed:
            raise ValueError(
                f"Network mode '{v}' is not supported. Allowed modes are: {', '.join(allowed)}"  # noqa:E501
            )
        return v


class ProxyConfig(BaseModel):
    """
    Pydantic model for proxy configuration.
    """

    model_config = opts

    input_file: Path
    test_url: str = Field(..., pattern=r"^https?://")
    usage_limit: int = Field(..., gt=0)
    validation: bool = True
    proxy_type: str = Field(..., pattern=r"^(HTTP|HTTPS|SOCKS4|SOCKS5)$")
    authentication: Optional[Dict[str, str]] = None

    @field_validator("input_file")
    @classmethod
    def check_file_exists(cls, v: Path) -> Path:
        if v.exists() and v.is_file():
            return v
        else:
            raise ValueError(f"Proxy pool input file '{v}' not found")

    @field_validator("authentication")
    @classmethod
    def check_authentication(
        cls, v: Optional[Dict[str, str]]
    ) -> Optional[Dict[str, str]]:
        if v is not None:
            if "username" not in v or "password" not in v:
                raise ValueError(
                    "Authentication must include both 'username' and 'password' keys"
                )
        return v


class DriverConfig(BaseModel):
    """
    Pydantic model for WebDriver configuration.
    """

    model_config = opts

    host_network: str
    option_args: Optional[List[str]] = ["--headless", "--width=1920", "--height=1080"]
    proxy: bool = True
    retry_attempts: int = Field(default=3, gt=0)
    retry_interval: int = Field(default=0.5, gt=0)
    user_agent: Optional[str] = None

    @field_validator("host_network")
    @classmethod
    def check_host_network(cls, v: str) -> str:
        if not v:
            raise ValueError("Host network cannot be empty")
        return v


# allow empty string for TargetConfig
target_opts = ConfigDict(
    extra="forbid",
    validate_assignment=True,
)


class Extraction(BaseModel):
    model_config = target_opts
    type: str
    selector: str


class Interaction(BaseModel):
    model_config = target_opts
    type: str
    selector: str


class TargetConfig(BaseModel):
    model_config = target_opts

    name: str
    domain: str
    input_file: Optional[Path] = None
    startup: Optional[List[Interaction]] = None
    interactions: Optional[List[Interaction]] = None
    extractions: Optional[List[Extraction]] = None


class ConfigError(Exception):
    """Custom exception for configuration-related errors."""


def check_network_connectivity(test_url: str) -> bool:
    try:
        response = requests.get(test_url, timeout=5)
        if response.status_code != 200:
            raise ValueError(
                f"Network connectivity issue detected. Status code: {response.status_code}"  # noqa:E501
            )  # noqa:E501
        return True
    except ConnectionError:
        raise ValueError(
            f"Network connectivity issue detected. Unable to reach {test_url}"
        )  # noqa:E501


def check_disk_space(required_space: int | float, path: str = "/") -> bool:
    total, used, free = shutil.disk_usage(path)
    if free < required_space:
        required_space_mb = required_space / (1024 * 1024)
        free_space_mb = free / (1024 * 1024)
        raise ValueError(
            f"Insufficient disk space. Required: {required_space_mb:.2f} MB, "
            f"Free: {free_space_mb:.2f} MB, Path: {path}"
        )
    return True


def check_cpu_usage(threshold: float = 0.9) -> bool:
    current_usage = psutil.cpu_percent() / 100
    if current_usage > threshold:
        raise ValueError(
            f"CPU usage is too high. Current: {current_usage * 100}%, Threshold: {threshold * 100}%"  # noqa:E501
        )  # noqa:E501
    return True


def check_memory_usage(threshold: float = 0.9) -> bool:
    memory = psutil.virtual_memory()
    current_usage = 1 - (memory.available / memory.total)
    if current_usage > threshold:
        raise ValueError(
            f"Memory usage is too high. Current: {current_usage * 100}%, Threshold: {threshold * 100}%"  # noqa:E501
        )  # noqa:E501
    return True


def load_config(filename: Path) -> Dict:
    """
    Loads and validates the configuration from a file.
    The file can be in YAML, JSON, or TOML format.
    """
    try:
        with open(filename, "r") as file:
            if filename.suffix == ".yaml":
                config_data = yaml.safe_load(file)
            elif filename.suffix == ".json":
                config_data = json.load(file)
            elif filename.suffix == ".toml":
                config_data = toml.load(file)
            else:
                raise ConfigError(f"Unsupported file format: {filename.suffix}")
    except FileNotFoundError as e:
        raise ConfigError(f"Configuration file not found: {filename}") from e
    except (yaml.YAMLError, json.JSONDecodeError, toml.TomlDecodeError) as e:
        raise ConfigError(f"Error parsing configuration: {e}") from e

    try:
        config = {
            "docker": DockerConfig(**config_data.get("Docker", {})),
            "logging": LoggingConfig(**config_data.get("Logging", {})),
            "proxy": ProxyConfig(**config_data.get("Proxy", {})),
            "driver": DriverConfig(**config_data.get("Driver", {})),
            "target": [
                TargetConfig(**target_config)
                for target_config in config_data.get("Target", [])
            ],
        }
        DockerConfig.validate_docker_environment(config["docker"].container_image)
        if not check_network_connectivity("https://www.google.com"):
            raise ValueError("Network connectivity issue detected")
        if not check_disk_space(1 * 1024 * 1024 * 1024):
            raise ValueError("Insufficient disk space")
        if not check_cpu_usage():
            raise ValueError("CPU usage is too high")
        if not check_memory_usage():
            raise ValueError("Memory usage is too high")
        return config
    except ValidationError as e:
        raise ConfigError(f"Failed to validate config: {e}")
