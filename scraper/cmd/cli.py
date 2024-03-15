import argparse
from pathlib import Path

from scraper.config.validator import (
    load_config,
    LoggingConfig,
    DockerConfig,
    ProxyConfig,
    DriverConfig,
    TargetConfig,
)
from scraper.config.logging import StructuredLogger


def parse_arguments():
    """
    Parses command line arguments for the web scraper.
    """
    parser = argparse.ArgumentParser(description="Web Scraper")
    parser.add_argument(
        "--target-type",
        type=str,
        default="example",
        help="Specify the target type (or leave blank for example runtime)",
    )
    parser.add_argument(
        "--config-format",
        type=str,
        default="yaml",
        help="Defaults to YAML, also supports: JSON, TOML",
    )
    return parser.parse_args()


def run_cli():
    args = parse_arguments()
    target_type = args.target_type
    config_format = args.config_format.lower()

    # Convert config format to file extension
    if config_format in ["yaml", "json", "toml"]:
        config_format = "." + config_format
    else:
        print(f"Unsupported config format: {config_format}")
        return None, None

    if target_type == "example":
        # Use default configuration values
        cfg = {
            "logging": LoggingConfig(),
            "docker": DockerConfig(),
            "proxy": ProxyConfig(),
            "driver": DriverConfig(),
            "target": [
                TargetConfig(),
                TargetConfig(
                    target_name="forms",
                    target_domain="https://www.scrapethissite.com/pages/forms/",
                    follow_links=True,
                ),
            ],
        }
    else:
        config_file = Path(f"files/configs/{target_type}{config_format}")
        try:
            cfg = load_config(config_file)
        except Exception as e:
            print(f"Fatal Error (config.load_config): {e}")
            return None, None

    logger_cfg = cfg["logging"]
    logger = StructuredLogger(target_type, logger_cfg)

    return logger, cfg
