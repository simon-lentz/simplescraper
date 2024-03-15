# Configuration Module

The `config` module is responsible for managing the application's configuration settings. It defines the structure of the configuration, validates input, and provides default values for various components of the web scraping application.

## Overview

The configuration is defined using Pydantic models, which offer type checking, validation, and easy serialization/deserialization. The main configuration categories are:

- **LoggingConfig**: Settings related to logging, such as log level, format, and file location.
- **DockerConfig**: Configuration for Docker containers used in the application, including port mappings, image specifications, and resource limits.
- **ProxyConfig**: Settings for managing proxy servers, including input file location, test URL, and usage limits.
- **DriverConfig**: Configuration for the WebDriver, including host network, browser options, and retry settings.
- **TargetConfig**: Defines the target websites for scraping, including domain and link-following behavior.

## Usage

The configuration can be loaded from YAML, JSON, or TOML files using the `load_config` function. This function validates the configuration against the defined Pydantic models and applies default values where necessary.

## Validation

The configuration module performs several validation checks to ensure the application runs smoothly:

- **Network Connectivity**: Checks if the application can connect to the internet.
- **Disk Space**: Ensures there is sufficient disk space available for the application.
- **Resource Usage**: Monitors CPU and memory usage to prevent overloading the system.

## Structured Logging

The `logging.py` file within this module provides a `StructuredLogger` class that outputs logs in a structured JSON format. This makes it easier to analyze and query log data, especially in production environments.

## Error Handling

The module defines a `ConfigError` exception for handling configuration-related errors. This ensures that any issues with the configuration are caught early and reported clearly.

## Extensibility

The configuration module is designed to be easily extensible. New configuration sections can be added by defining additional Pydantic models and integrating them into the `load_config` function.
