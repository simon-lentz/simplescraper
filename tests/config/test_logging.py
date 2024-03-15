import sys
import json
import logging

from scraper.config.logging import JsonFormatter


def test_json_formatter():
    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname=__file__,
        lineno=100,
        msg="Test message",
        args=(),
        exc_info=None,
    )
    formatter = JsonFormatter()
    log_output = formatter.format(record)
    log_data = json.loads(log_output.rstrip(","))
    assert log_data["message"] == "Test message"
    assert log_data["level"] == "INFO"
    assert log_data["name"] == "test"


def test_structured_logger(mock_structured_logger):
    logger = mock_structured_logger
    logger.info("test")
    with open(logger.log_file, "r") as f:
        log_contents = f.read()
        assert "test" in log_contents


def test_json_formatter_with_exception():
    try:
        raise ValueError("Test exception")
    except ValueError:
        exc_info = sys.exc_info()
        record = logging.LogRecord(
            name="test",
            level=logging.ERROR,
            pathname=__file__,
            lineno=100,
            msg="Exception occurred",
            args=(),
            exc_info=exc_info,
        )
    formatter = JsonFormatter()
    log_output = formatter.format(record)
    log_data = json.loads(log_output.rstrip(","))
    assert "exception" in log_data
    assert "Test exception" in log_data["exception"]


def test_structured_logger_initialization(mock_structured_logger):
    logger = mock_structured_logger
    assert logger.level == logging.INFO
    assert len(logger.handlers) == 1
    assert isinstance(logger.handlers[0], logging.FileHandler)
    assert isinstance(logger.handlers[0].formatter, JsonFormatter)
    # Check the log file is opened and initialized correctly
    with open(logger.log_file, "r") as f:
        assert f.read() == "["


def test_structured_logger_log_levels(mock_structured_logger):
    logger = mock_structured_logger

    logger.setLevel(logging.ERROR)
    logger.info("This should not be logged")
    logger.error("This is an error")

    with open(logger.log_file, "r") as f:
        log_contents = f.read()
        assert "This should not be logged" not in log_contents
        assert "This is an error" in log_contents
        # Check that the error message is logged at the correct level
        assert '"level": "ERROR"' in log_contents


def test_structured_logger_multiple_entries(mock_structured_logger):
    logger = mock_structured_logger
    logger.info("First entry")
    logger.info("Second entry")

    with open(logger.log_file, "r") as f:
        log_contents = f.read()
        assert "First entry" in log_contents
        assert "Second entry" in log_contents


def test_structured_logger_close(mock_structured_logger):
    logger = mock_structured_logger
    log_file = logger.log_file
    logger.close()

    with open(log_file, "r") as f:
        log_content = f.read()
    assert log_content.endswith("]")
    # Check that the log file content is a valid JSON array
    try:
        json_array = json.loads(log_content)
        assert isinstance(json_array, list)
    except json.JSONDecodeError:
        assert False, "Log file content is not a valid JSON array"

    # Ensure the logger no longer has any handlers
    assert len(logger.handlers) == 0


def test_structured_logger_exception_logging(mock_structured_logger):
    logger = mock_structured_logger
    try:
        raise ValueError("Test exception")
    except ValueError:
        logger.exception("An error occurred")

    with open(logger.log_file, "r") as f:
        log_contents = f.read()
        assert "An error occurred" in log_contents
        assert "Test exception" in log_contents
