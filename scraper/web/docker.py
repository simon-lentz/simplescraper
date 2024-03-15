import docker

from typing import Optional
from docker.models.containers import Container
from docker.errors import ContainerError, APIError, NotFound

from scraper.config.logging import StructuredLogger
from scraper.config.validator import DockerConfig

from .connection import ConnectionData


class DockerManager:
    """
    Manages Docker containers for web scraping.

    This class provides methods to create, ping, and stop Docker containers used
    for web scraping. It utilizes the docker Python library to interact with the
    Docker daemon and manage container lifecycle.

    Attributes:
        logger (StructuredLogger): Logger for logging messages.
        ports (List[int]): List of ports on which the Docker containers are exposed.
        shm (str): Shared memory size for the Docker containers.
        image (str): Docker image to use for the containers.
        network_mode (str): Network mode to use with Docker
        environment (Dict[str, str]): Docker environment kwargs
        remove_on_cleanup (bool): If true containers are stopped and removed, otherwise stopped.
        client (docker.DockerClient): Docker client for interacting with the Docker daemon.
    """  # noqa:E501

    def __init__(self, logger: StructuredLogger, cfg: DockerConfig) -> None:
        """
        Initializes a DockerManager instance.

        Args:
            logger (StructuredLogger): Logger for logging messages.
            cfg (DockerConfig): Configuration for Docker-related settings.
        """
        self.logger = logger
        self.shm = cfg.container_shm_size
        self.image = cfg.container_image
        self.network_mode = cfg.network_mode
        self.environment = cfg.environment  # todo
        self.remove_on_cleanup = cfg.remove_on_cleanup
        self.client = docker.from_env()

    def create_container(self, connection: ConnectionData) -> Optional[Container]:
        """
        Creates and starts a Docker container.

        Args:
            connection (ConnectionData): Connection data containing the name and port for the container.

        Returns:
            Optional[Container]: The created Docker container, or None if creation failed.

        Raises:
            RuntimeError: If the Docker daemon is not running or the container fails to start.
        """  # noqa:E501
        name = connection.name
        port = connection.port
        try:
            container = self.client.containers.run(
                self.image,
                name=name,
                ports={"4444/tcp": port},
                detach=True,
                network_mode=self.network_mode,
                shm_size=self.shm,
                environment=self.environment,
            )
            assert isinstance(container, Container)
            self.logger.info(f"'{name}' browser started on port '{port}'")
            return container
        except (ContainerError, APIError) as e:
            self.logger.error(f"'{name}' browser failed to start: {e}")
            raise

    def cleanup(self, container: Container) -> None:
        """Stops and optionally removes a Docker container."""
        self._stop_container(container)
        if self.remove_on_cleanup:
            self._remove_container(container)

    def _stop_container(self, container: Container) -> None:
        """Stops a Docker container."""
        try:
            container.stop(timeout=10)
            self.logger.info(
                f"Stopped container '{container.name}' (ID: {container.id})."
            )  # noqa:E501
        except (ContainerError, APIError) as e:
            self.logger.error(f"Failed to stop container '{container.name}': {e}")
            raise e

    def _remove_container(self, container: Container) -> None:
        """Removes a Docker container."""
        try:
            container.remove()
            self.logger.info(f"Removed container '{container.name}' (ID: {container.id}).")  # noqa:E501
        except NotFound:
            self.logger.warning(f"Container '{container.name}' does not exist or has already been removed.")  # noqa:E501
        except (ContainerError, APIError) as e:
            self.logger.error(f"Failed to remove container '{container.name}': {e}")
            raise e
