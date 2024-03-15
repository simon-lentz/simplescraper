from typing import Optional
from docker.models.containers import Container
from selenium.webdriver.remote.webdriver import WebDriver


class ConnectionData:
    """
    Represents the data associated with a web scraping connection.

    This class stores information about a connection, including its name, port,
    proxy, Docker container, and WebDriver.

    Attributes:
        name (str): The name of the connection.
        port (str): The port on which the connection is established.
        proxy (Optional[str]): The proxy used by the connection.
        container (Optional[Container]): The Docker container associated with the connection.
        driver (Optional[WebDriver]): The WebDriver instance used by the connection.
    """  # noqa:E501

    def __init__(self, name: str, port: str, proxy: Optional[str] = None,
                 container: Optional[Container] = None, driver: Optional[WebDriver] = None):  # noqa:E501
        self.name = name
        self.port = port
        self.proxy = proxy
        self.container = container
        self.driver = driver

    def set_container(self, container: Container):
        """
        Sets the Docker container for the connection.

        Args:
            container (Container): The Docker container to associate with the connection.
        """  # noqa:E501
        if isinstance(container, Container):
            self.container = container
        else:
            raise TypeError(f"Expected 'Container', got '{type(container).__name__}'")

    def get_container(self) -> Container:
        """
        Retrieves the Docker container associated with the connection.

        Returns:
            Container: The Docker container associated with the connection.

        Raises:
            ValueError: If the container has not been set.
        """
        if isinstance(self.container, Container):
            return self.container
        else:
            raise ValueError(f"Container not set for connection '{self.name}'")

    def set_driver(self, driver: WebDriver):
        """
        Sets the WebDriver for the connection.

        Args:
            driver (WebDriver): The WebDriver instance to associate with the connection.
        """
        if isinstance(driver, WebDriver):
            self.driver = driver
        else:
            raise TypeError(f"Expected 'WebDriver', got '{type(driver).__name__}'")

    def get_driver(self) -> WebDriver:
        """
        Retrieves the WebDriver associated with the connection.

        Returns:
            WebDriver: The WebDriver instance associated with the connection.

        Raises:
            ValueError: If the driver has not been set.
        """
        if isinstance(self.driver, WebDriver):
            return self.driver
        else:
            raise ValueError(f"Driver not set for connection '{self.name}'")

    def set_proxy(self, proxy: str):
        """
        Sets the proxy for the connection.

        Args:
            proxy (str): The proxy to use for the connection.
        """
        if not isinstance(proxy, str):
            raise ValueError(f"Invalid proxy '{proxy}'")
        self.proxy = proxy

    def get_proxy(self) -> str:
        """
        Retrieves the proxy associated with the connection.

        Returns:
            str: The proxy used by the connection.

        Raises:
            ValueError: If the proxy has not been set.
        """
        if self.proxy is not None:
            return self.proxy
        else:
            raise ValueError(f"Proxy not set for connection '{self.name}'")
