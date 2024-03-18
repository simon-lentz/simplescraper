from typing import Dict

from scraper.config.logging import StructuredLogger
from scraper.config.validator import ProxyConfig, DockerConfig, DriverConfig

from .docker import DockerManager
from .driver import DriverManager
from .connection import ConnectionData
from .proxy import ProxyManager, UsageError


class WebController:
    """
    Manages the web scraping process by orchestrating the interaction between
    proxies, Docker containers, and WebDriver instances.

    Attributes:
        logger (StructuredLogger): Logger for logging messages.
        docker_manager (DockerManager): Manager for handling Docker containers.
        driver_manager (DriverManager): Manager for handling WebDriver instances.
        proxy_manager (ProxyManager): Manager for handling proxy servers.
        connections (Dict[str, ConnectionData]): Dictionary mapping target names to their ConnectionData.
    """  # noqa:E501

    def __init__(self, logger: StructuredLogger, connections: Dict[str, ConnectionData]) -> None:  # noqa:E501
        self.logger = logger
        self.docker_manager = None
        self.driver_manager = None
        self.proxy_manager = None
        self.connections = connections

    def _connect_container(self, connection: ConnectionData) -> None:
        """
        Connects a Docker container for the given connection.

        Args:
            connection (ConnectionData): The connection data for which to connect the container.
        """  # noqa:E501
        if not self.docker_manager:
            raise RuntimeError("DockerManager not found.")
        try:
            container = self.docker_manager.create_container(connection)
            if container:
                connection.set_container(container)
            else:
                raise RuntimeError(f"Failed to set container for '{connection.name}'")
        except Exception as e:
            self.logger.error(f"Failed to connect container for '{connection.name}': {e}", exc_info=True)  # noqa:E501

    def _connect_driver(self, connection: ConnectionData) -> None:
        """
        Connects a WebDriver for the given connection.

        Args:
            connection (ConnectionData): The connection data for which to connect the WebDriver.  # noqa:E501
        """
        if not self.driver_manager:
            raise RuntimeError("DriverManager not found.")
        try:
            driver = self.driver_manager.create_driver(connection)
            if driver:
                connection.set_driver(driver)
            else:
                raise RuntimeError(f"Failed to set driver for '{connection.name}'")
        except Exception as e:
            self.logger.error(f"Failed to connect driver for '{connection.name}': {e}", exc_info=True)  # noqa:E501

    def init_docker_manager(self, cfg: DockerConfig) -> None:
        """
        Initializes the DockerManager with the given configuration.

        Args:
            cfg (DockerConfig): The Docker configuration.
        """
        self.docker_manager = DockerManager(self.logger, cfg)

    def init_driver_manager(self, cfg: DriverConfig) -> None:
        """
        Initializes the DriverManager with the given configuration.

        Args:
            cfg (DriverConfig): The WebDriver configuration.
        """
        self.driver_manager = DriverManager(self.logger, cfg)

    def init_proxy_manager(self, cfg: ProxyConfig) -> None:
        """
        Initializes the ProxyManager with the given configuration.

        Args:
            cfg (ProxyConfig): The proxy configuration.
        """
        self.proxy_manager = ProxyManager(self.logger, cfg)

    def get_connection(self, target_name: str) -> ConnectionData:
        """
        Retrieves the ConnectionData for the given target name.

        Args:
            target_name (str): The name of the target.

        Returns:
            ConnectionData: The connection data associated with the target name.

        Raises:
            ValueError: If no connection is found for the target name.
        """
        connection = self.connections.get(target_name)
        if connection:
            return connection
        else:
            raise ValueError(f"No connection found for target {target_name}")

    def connect(self) -> None:
        """
        Connects all connections by setting up their proxies, containers, and drivers.
        """
        if not (self.proxy_manager and self.docker_manager and self.driver_manager):
            raise RuntimeError("Connection managers not initialized properly.")
        for target, connection in self.connections.items():
            try:
                proxy = self.proxy_manager.get_proxy()
                connection.set_proxy(proxy)
                self._connect_container(connection)
                self._connect_driver(connection)
            except Exception as e:
                self.logger.critical(f"Failed to connect for target '{target}': {e}", exc_info=True)  # noqa:E501
                return

    def disconnect(self) -> None:
        """
        Disconnects all connections by quitting their drivers, stopping and
        optionally removing their containers, and releasing their proxies.
        """  # noqa:E501
        if not (self.proxy_manager and self.docker_manager and self.driver_manager):
            raise RuntimeError("Managers not found")
        for _, connection in self.connections.items():
            try:
                if connection.driver:
                    self.driver_manager.quit_driver(connection.driver)
                if connection.container:
                    self.docker_manager.cleanup(connection.container)
                if connection.proxy:
                    self.proxy_manager.release_proxy(connection.proxy)
            except Exception as e:
                self.logger.warning(f"Failed to disconnect: {e}", exc_info=True)

    def make_request(self, target_name: str, url: str) -> None:
        """
        Makes a web request to the given URL using the WebDriver of the specified target.

        Args:
            target_name (str): The name of the target connection to use.
            url (str): The URL to request.

        Raises:
            RuntimeError: If no connection is found for the target name.
        """  # noqa:E501
        if not self.proxy_manager:
            raise RuntimeError("Unable to access ProxyManager")
        connection = self.get_connection(target_name)
        driver = connection.driver
        if driver:
            try:
                driver.get(url)
                if connection.proxy:
                    self.proxy_manager.increment_usage(connection.proxy)
            except UsageError:
                self.rotate_proxy(connection)
                self.make_request(target_name, url)
            except Exception as e:
                self.logger.error(f"Request to '{url}' for '{target_name}' failed: {e}", exc_info=True)  # noqa:E501
        else:
            raise RuntimeError(f"No WebDriver found for connection '{target_name}'")

    def rotate_proxy(self, connection: ConnectionData) -> None:
        """
        Rotates the proxy for the given connection and updates the WebDriver.

        Args:
            connection (ConnectionData): The connection for which to rotate the proxy.

        Raises:
            RuntimeError: If the new proxy or driver cannot be set.
        """
        if not (self.proxy_manager and self.driver_manager):
            raise RuntimeError("ProxyManager or DriverManager not found.")
        try:
            new_proxy = self.proxy_manager.get_proxy()
            connection.set_proxy(new_proxy)
            if connection.driver:
                self.driver_manager.quit_driver(connection.driver)
            new_driver = self.driver_manager.create_driver(connection)
            if new_driver:
                connection.set_driver(new_driver)
                self.logger.info(f"'{connection.name}' rotated proxy")
            else:
                raise RuntimeError(f"Failed to reload driver for '{connection.name}'")
        except Exception as e:
            self.logger.critical(f"Failed to rotate proxy for connection '{connection.name}': {e}", exc_info=True)  # noqa:E501


def setup_controller(logger: StructuredLogger, cfg) -> WebController:
    """
    Sets up the WebController with the specified configuration.

    Args:
        logger (StructuredLogger): The logger to use for the controller.
        cfg: The configuration for the controller and its connections.

    Returns:
        WebController: The initialized WebController instance.

    Raises:
        ValueError: If the number of target names does not match the number of ports.
    """
    connections = {}
    for target in cfg["target"]:
        port = cfg["docker"].ports.pop(0)  # Assume ports are assigned in order
        connections[target.name] = ConnectionData(target.name, port)
    controller = WebController(logger, connections)
    controller.init_proxy_manager(cfg["proxy"])
    controller.init_docker_manager(cfg["docker"])
    controller.init_driver_manager(cfg["driver"])
    return controller
