import time

from typing import Optional
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.common.exceptions import WebDriverException

from scraper.config.validator import DriverConfig
from scraper.config.logging import StructuredLogger


class DriverManager:
    """
    Manages WebDriver instances for web scraping.

    This class provides methods to create and quit WebDriver instances. It supports
    configurable options for the WebDriver, including proxy settings and retry
    mechanisms for creating the driver.

    Attributes:
        logger (StructuredLogger): Logger for logging messages.
        host_network (str): The network address where the WebDriver server is hosted.
        driver_options (List[str]): List of options to configure the WebDriver.
        proxy_server (bool): Flag indicating whether to use a proxy server.
        max_attempts (int): Maximum number of attempts to create a WebDriver.
        retry_interval (int): Time interval (in seconds) between retry attempts.
        user_agent (str): Value for user agent configuration.
    """

    def __init__(self, logger: StructuredLogger, cfg: DriverConfig) -> None:
        self.logger = logger
        self.host_network = cfg.host_network
        self.driver_options = cfg.option_args
        self.proxy_server = cfg.proxy
        self.max_attempts = cfg.retry_attempts
        self.retry_interval = cfg.retry_interval
        self.user_agent = cfg.user_agent

    def create_driver(self, connection) -> Optional[WebDriver]:
        """
        Creates a WebDriver instance with the specified options and proxy settings.

        Args:
            connection (ConnectionData): Connection data containing the name, port, and proxy for the driver.

        Returns:
            Optional[WebDriver]: The created WebDriver instance, or None if creation failed.

        Raises:
            WebDriverException: If the WebDriver fails to be created after the specified number of attempts.
        """  # noqa:E501
        connection_name = connection.name
        connection_port = connection.port
        proxy = connection.proxy
        opts = Options()
        for option in self.driver_options:
            opts.add_argument(option)
        if self.proxy_server:
            opts.add_argument(f"--proxy-server={proxy}")
        if self.user_agent:
            opts.add_argument(f"--user-agent={self.user_agent}")
        for attempt in range(self.max_attempts):
            try:
                driver = webdriver.Remote(
                    command_executor=f"{self.host_network}:{connection_port}/wd/hub",
                    options=opts,
                )
                self.logger.info(
                    f"WebDriver session created with session ID: {driver.session_id}"
                )  # noqa:E501
                self.logger.info(
                    f"WebDriver session created with capabilities: {driver.capabilities}"  # noqa:E501
                )  # noqa:E501
                return driver
            except Exception as e:
                self.logger.warning(
                    f"Attempt {attempt + 1} - Failed to create driver with proxy '{proxy}': {e}",  # noqa:E501
                    exc_info=True,
                )  # noqa:E501
                if attempt < self.max_attempts - 1:
                    time.sleep(self.retry_interval)
                else:
                    error_msg = f"Failed to create driver for target '{connection_name}' on port '{connection_port}' after {self.max_attempts} attempts"  # noqa:E501
                    self.logger.error(error_msg)  # noqa:E501
                    raise WebDriverException(error_msg)

    def quit_driver(self, driver: WebDriver) -> None:
        """
        Quits the WebDriver instance, closing all associated windows.

        Args:
            driver (WebDriver): The WebDriver instance to quit.

        Raises:
            WebDriverException: If an error occurs while quitting the WebDriver.
        """
        try:
            driver.quit()
            self.logger.info("WebDriver session terminated successfully.")
        except WebDriverException as e:
            self.logger.error(
                f"Error occurred while terminating WebDriver session: {e}",
                exc_info=True,
            )  # noqa:E501
