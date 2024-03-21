from typing import List

from scraper.config.validator import TargetConfig
from scraper.config.logging import StructuredLogger
from scraper.web.controller import WebController

from .target import TargetManager


def run_scraper(logger: StructuredLogger, controller: WebController, cfgs: List[TargetConfig]):  # noqa:E501
    try:
        controller.connect()
    except Exception as e:
        logger.critical(f"Scraper failed to connect: {e}", exc_info=True)

    target_manager = TargetManager(logger, controller)
    for target in cfgs:
        try:
            target_manager.scrape_target(target)
        except Exception as e:
            logger.error(f"Failed to scrape '{target.name}': {e}", exc_info=True)
    try:
        controller.disconnect()
    except Exception as e:
        logger.critical(f"Scraper failed to disconnect: {e}", exc_info=True)
