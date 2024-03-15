# Web Module

The `web` module is responsible for managing the interactions between the web scraping components, such as proxies, Docker containers, and WebDriver instances. It orchestrates the setup, usage, and teardown of these components to facilitate the web scraping process.

## Overview

The module consists of several key components:

- **ConnectionData**: Stores information about a web scraping connection, including its name, port, proxy, Docker container, and WebDriver instance.
- **WebController**: Orchestrates the web scraping process by managing the interaction between proxies, Docker containers, and WebDriver instances.
- **DockerManager**: Handles the lifecycle of Docker containers used for web scraping.
- **DriverManager**: Manages the creation and termination of WebDriver instances.
- **ProxyManager**: Manages a pool of proxies, including loading, validating, and rotating proxies as needed.

## ConnectionData

`ConnectionData` is a class that represents the data associated with a web scraping connection. It stores details such as the connection's name, port, proxy settings, Docker container, and WebDriver instance.

## WebController

`WebController` is the central component that manages the web scraping process. It initializes and connects all the necessary components, such as proxies, Docker containers, and WebDriver instances. It also provides methods to connect and disconnect all connections, make web requests, and rotate proxies as needed.

## DockerManager

`DockerManager` provides methods to create, start, stop, and remove Docker containers. It uses the Docker Python library to interact with the Docker daemon and manage the lifecycle of containers used for web scraping.

## DriverManager

`DriverManager` manages the creation and termination of WebDriver instances. It supports configurable options for the WebDriver, including proxy settings and retry mechanisms for creating the driver.

## ProxyManager

`ProxyManager` manages a pool of proxies for web scraping. It provides methods to load, format, validate, and manage a pool of proxies. It supports proxy validation and usage tracking to ensure that proxies are not overused.

## Error Handling

The module defines custom exceptions such as `UsageError` and `ProxyReloadError` for handling specific errors related to proxy usage and reloading.

## Extensibility

The `web` module is designed to be easily extensible. New components and functionality can be added as needed to support additional web scraping requirements.
