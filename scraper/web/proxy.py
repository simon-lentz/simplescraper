import re
import requests
import concurrent.futures
from typing import List, Dict, Tuple, Optional

from scraper.config.logging import StructuredLogger
from scraper.config.validator import ProxyConfig


class UsageError(Exception):
    """
    Custom exception raised when usage exceeds usage limit
    """


class ProxyReloadError(Exception):
    """
    Custom exception raised when reloading the pool fails
    """


class ProxyManager:
    """
    Manages a pool of proxies for web scraping.

    This class provides methods to load, format, validate, and manage a pool of proxies.
    It supports proxy validation and usage tracking to ensure that proxies are not overused.

    Attributes:
        logger (StructuredLogger): Logger for logging messages.
        input_file (Path): Path to the file containing the list of proxies.
        test_url (str): URL used to test the proxies.
        usage_limit (int): Maximum number of uses for each proxy.
        validation (bool): Flag indicating whether to validate proxies.
        proxy_type (str): Connection protocol to use with proxy
        authentication (Dict[str, str]): authentication details passed to proxies if provided
        proxy_pool (Dict[str, Tuple[int, bool]]): Dictionary mapping proxies to their usage count and availability.
    """  # noqa:E501

    def __init__(self, logger: StructuredLogger, cfg: ProxyConfig) -> None:
        self.logger = logger
        self.input_file = cfg.input_file
        self.test_url = cfg.test_url
        self.usage_limit = cfg.usage_limit
        self.validation = cfg.validation
        self.proxy_type = cfg.proxy_type.lower()  # new field
        self.authentication = cfg.authentication  # new field
        self.proxy_pool: Dict[str, Tuple[int, bool]] = {}
        self._create_pool()

    def _create_pool(self) -> None:
        """Creates the proxy pool from the input file."""
        proxy_list = (
            self._validate_proxies() if self.validation else self._format_pool()
        )  # noqa:E501
        self.proxy_pool = {proxy: (0, False) for proxy in proxy_list}

    def _load_proxies(self) -> List[str]:
        """Loads the list of proxies from the input file."""
        if not self.input_file.exists():
            error_message = f"Input file '{self.input_file}' not found"
            self.logger.error(error_message)
            raise FileNotFoundError(error_message)
        with open(self.input_file, "r") as file:
            return [line.strip() for line in file if line.strip()]

    def _format_pool(self, new_proxies: Optional[List[str]] = None) -> List[str]:
        """Formats the raw proxies to ensure they are in the correct format."""
        raw_proxies = new_proxies if new_proxies is not None else self._load_proxies()
        proxy_pattern = re.compile(
            r"^((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?):\d+$",  # noqa:E501
            flags=re.ASCII,
        )

        formatted_proxies = []
        for proxy in raw_proxies:
            if proxy_pattern.match(proxy):
                if self.authentication:
                    username = self.authentication.get("username")
                    password = self.authentication.get("password")
                    formatted_proxy = f"{username}:{password}@{proxy}"
                else:
                    formatted_proxy = proxy
                formatted_proxies.append(formatted_proxy)

        if formatted_proxies:
            self.logger.info(f"Extracted {len(formatted_proxies)} formatted proxies")
            return formatted_proxies
        else:
            error_message = "Input contained no properly formatted proxies"
            self.logger.error(error_message)
            raise ValueError(error_message)

    def _test_proxy(self, proxy: str) -> bool:
        """Tests a proxy by attempting to access a test URL."""
        if self.proxy_type == "http":
            proxy_url = f"http://{proxy}"
        elif self.proxy_type == "https":
            proxy_url = f"https://{proxy}"
        else:  # SOCKS4/SOCKS5
            proxy_url = f"socks5://{proxy}"

        # Add authentication to the proxy URL if provided
        if self.authentication:
            username = self.authentication.get("username")
            password = self.authentication.get("password")
            proxy_url = f"{username}:{password}@{proxy_url}"

        proxies = {"http": proxy_url, "https": proxy_url}
        try:
            response = requests.get(self.test_url, proxies=proxies, timeout=5)
            return response.status_code == 200
        except Exception as e:
            raise e

    def _validate_proxies(self, new_proxies: Optional[List[str]] = None) -> List[str]:
        """Validates the proxies by testing their ability to access a test URL."""
        proxy_pool = new_proxies if new_proxies is not None else self._format_pool()
        functional_proxies = []
        validation_errors = []  # List to collect validation errors
        num_workers = min(10, len(proxy_pool))
        with concurrent.futures.ThreadPoolExecutor(max_workers=num_workers) as executor:
            futures = {
                executor.submit(self._test_proxy, proxy): proxy for proxy in proxy_pool
            }  # noqa:E501
            try:
                timeout = len(futures) * 10
                for future in concurrent.futures.as_completed(futures, timeout=timeout):
                    proxy = futures[future]
                    try:
                        if future.result():
                            functional_proxies.append(proxy)
                    except Exception as e:
                        validation_errors.append(str(e))
            except TimeoutError:
                self.logger.error(
                    "Proxy validation timed out before all proxies could be tested"
                )  # noqa:E501
                unfinished_proxies = [
                    proxy for future, proxy in futures.items() if not future.done()
                ]  # noqa:E501
                validation_errors.append(
                    f"Unfinished proxy validations: {unfinished_proxies}"
                )  # noqa:E501

        if validation_errors:
            self.logger.warning(
                "Proxy validation errors:\n" + "\n".join(validation_errors)
            )  # noqa:E501

        if functional_proxies:
            self.logger.info(
                f"Validated {len(functional_proxies)} out of {len(proxy_pool)} proxies"
            )  # noqa:E501
            return functional_proxies
        else:
            error_message = "Validation Failed, No Viable Proxies"
            self.logger.error(error_message)
            raise ValueError(error_message)

    def _reload_and_get_proxy(self) -> str:
        """
        Reloads the proxy pool with fresh proxies and attempts
        to retrieve an available proxy.
        """
        exhausted_proxies = set(self.proxy_pool.keys())
        fresh_proxies = set(self._load_proxies())
        new_proxies = fresh_proxies - exhausted_proxies

        if not new_proxies:
            error_message = "No new proxies available for reloading the pool"
            self.logger.error(error_message)
            raise ProxyReloadError(error_message)

        validated_proxies = self._validate_proxies(list(new_proxies))
        old_count = len(self.proxy_pool)
        self.proxy_pool.update({proxy: (0, False) for proxy in validated_proxies})
        new_count = len(self.proxy_pool)
        self.logger.info(f"Reloaded proxy pool: {old_count} -> {new_count} proxies")

        for proxy, (usage, in_use) in self.proxy_pool.items():
            if usage < self.usage_limit and not in_use:
                self.proxy_pool[proxy] = (usage + 1, True)
                return proxy

        error_message = "No available proxies found after reloading"
        self.logger.error(error_message)
        raise ProxyReloadError(error_message)

    def get_proxy(self) -> str:
        """
        Retrieves an available proxy from the pool.
        If no available proxies are found, attempts to
        reload the pool with fresh proxies.
        """
        for proxy, (usage, in_use) in self.proxy_pool.items():
            if usage < self.usage_limit and not in_use:
                self.proxy_pool[proxy] = (usage + 1, True)
                return proxy
            elif usage >= self.usage_limit:
                self.delete_proxy(proxy)

        self.logger.debug("No available proxies found, reloading pool")
        return self._reload_and_get_proxy()

    def increment_usage(self, proxy: str) -> None:
        """Increments the usage count of a proxy."""
        if proxy in self.proxy_pool:
            usage, _ = self.proxy_pool[proxy]
            if usage < self.usage_limit:
                self.proxy_pool[proxy] = (usage + 1, True)
            else:
                self.delete_proxy(proxy)
                raise UsageError(f"Proxy '{proxy}' has reached its usage limit")
        else:
            self.logger.warning(f"Proxy '{proxy}' not found in pool")

    def release_proxy(self, proxy: str) -> None:
        """Releases a proxy back to the pool, making it available for use again."""
        if proxy in self.proxy_pool:
            usage, _ = self.proxy_pool[proxy]
            if usage < self.usage_limit:
                self.proxy_pool[proxy] = (usage, False)
                self.logger.info(f"Proxy '{proxy}' released back to pool")
            else:
                self.logger.info(f"Proxy '{proxy}' exceeded usage limit")
                self.delete_proxy(proxy)
        else:
            self.logger.warning(f"Proxy '{proxy}' not found in pool")

    def delete_proxy(self, proxy: str) -> None:
        """Removes a proxy from the pool."""
        if proxy in self.proxy_pool:
            del self.proxy_pool[proxy]
            self.logger.info(f"Proxy '{proxy}' removed from the pool")
