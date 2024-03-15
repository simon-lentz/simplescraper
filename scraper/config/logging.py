import os
import logging
import json
from datetime import datetime

from .validator import LoggingConfig


class JsonFormatter(logging.Formatter):
    """
    Formats log records into JSON format.

    This formatter converts log records into a JSON object, making it easier
    to parse and analyze log data.
    """

    def format(self, record: logging.LogRecord) -> str:
        """
        Formats a log record into a JSON string.

        Args:
            record: The log record to format.

        Returns:
            A JSON-formatted string representing the log record.
        """
        log_record = {
            "time": datetime.fromtimestamp(record.created).isoformat(),
            "name": record.name,
            "level": record.levelname,
            "origin": f"{record.module}.{record.funcName}, line {record.lineno}",
            "message": record.getMessage(),
        }
        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_record, indent=4) + ","


class StructuredLogger(logging.Logger):
    """
    A logger that uses structured logging with JSON format.

    This logger outputs log records in a structured JSON format, which is
    useful for processing and analyzing log data.
    """

    def __init__(self, target_type: str, cfg: LoggingConfig):
        """
        Initializes the logger with the specified target type and configuration.

        Args:
            target_type: A string representing the type of the target being logged.
            cfg: A LoggingConfig object containing configuration settings for the logger.
        """  # noqa:E501
        super().__init__(name=f"Scraper Log: {target_type}", level=cfg.log_level)
        self.log_directory = cfg.log_directory
        self.log_file = self._get_new_log_file()
        self.log_max_size = self._parse_log_max_size(cfg.log_max_size)
        self._configure_file_handler(cfg.log_level)

    def _get_new_log_file(self):
        """
        Generates a new log file path with a timestamp.

        Returns:
            A Path object representing the new log file path.
        """
        return self.log_directory / f"{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

    def _parse_log_max_size(self, log_max_size: str) -> int:
        """
        Parses the log file size limit from a string to an integer in bytes.

        Args:
            log_max_size: The log file size limit as a string with a unit (e.g., "10MB").

        Returns:
            The log file size limit in bytes as an integer.
        """  # noqa:E501
        size_map = {
            "b": 8,
            "k": 1024,
            "kb": 1024,
            "m": 1024**2,
            "mb": 1024**2,
            "g": 1024**3,
            "gb": 1024**3,
        }
        cfg_val = log_max_size.lower()

        # Extract the numeric part and the unit part from the string
        size = int("".join(filter(str.isdigit, cfg_val)))
        unit = "".join(filter(str.isalpha, cfg_val))

        if unit in size_map:
            return size * size_map[unit]
        else:
            raise ValueError(
                f"Invalid log size unit '{unit}' in '{log_max_size}'. Valid units are: {', '.join(size_map.keys())}"  # noqa:E501
            )

    def _configure_file_handler(self, log_level: str):
        """
        Configures a file handler for writing logs to a file.

        Args:
            log_level: The log level for the file handler.
        """
        file_handler = logging.FileHandler(self.log_file, mode="a")
        file_handler.setLevel(log_level.upper())
        file_handler.setFormatter(JsonFormatter())
        self.addHandler(file_handler)
        with open(self.log_file, "w") as f:
            f.write("[")

    def _rotate_log_file(self):
        """
        Rotates the log file when it reaches or exceeds the size limit.
        """
        self.close()  # Close the current log file
        self.log_file = self._get_new_log_file()  # Get a new log file name
        self._configure_file_handler(self.level)  # Reconfigure the file handler

    def handle(self, record):
        """
        Handles a log record, rotating the log file if necessary.

        Args:
            record: The log record to handle.
        """
        if os.path.getsize(self.log_file) >= self.log_max_size:
            self._rotate_log_file()
        super().handle(record)

    def close(self):
        """
        Closes the logger and its handlers, properly finalizing the log file.
        """
        with open(self.log_file, "rb+") as f:
            f.seek(0, 2)  # Move the cursor to the end of the file
            size = f.tell()
            if size >= 2:
                f.seek(-2, 2)  # Move the cursor to final curly bracket
                f.truncate()  # Remove the last comma and newline
                f.write(b"]")  # Write the closing bracket
            else:
                f.write(b"]")  # if file is empty, close array in-place
        for handler in self.handlers:
            handler.close()
            self.removeHandler(handler)
