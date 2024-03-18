from typing import List

from scraper.config.logging import StructuredLogger
from scraper.web.controller import WebController
from scraper.config.validator import TargetConfig

from .interaction import InteractionManager
from .extraction import ExtractionManager


def target_links(logger: StructuredLogger, target: TargetConfig) -> List[str]:
    """Loads the list of links from the target's input file"""
    input_file = target.input_file
    if input_file.exists():
        try:
            with open(input_file, "r") as file:
                return [line.strip() for line in file if line.strip()]
        except Exception as e:
            logger.error(f"Failed to read links from input file '{input_file}' for '{target.name}': {e}")  # noqa:E501
    else:
        raise FileNotFoundError(f"Failed to load '{input_file}' for '{target.name}'")  # noqa:E501


def run_scraper(logger: StructuredLogger, controller: WebController, cfgs: List[TargetConfig]):  # noqa:E501
    # attempt to create connections
    try:
        controller.connect()
        interact = InteractionManager(logger)
        extract = ExtractionManager(logger)
    except Exception as e:
        logger.critical(f"Scraper failed to connect: {e}", exc_info=True)
    for target in cfgs:
        # retrieve target connections, get target domain
        connection = controller.get_connection(target.name)
        driver = connection.get_driver()
        controller.make_request(target.name, target.domain)
        # attempt startup actions
        try:
            interact.startup(driver, target)
            logger.info(f"Startup complete for '{target.name}'")
        except Exception as e:
            logger.error(f"Startup failed for '{target.name}': {e}")
        # iterate over target links, perform interactions and extractions
        for link in target_links(logger, target):
            try:
                controller.make_request(target.name, link)
                logger.info(f"Retrieved '{link}' for '{target.name}': {driver.title}")
                interact.execute(driver, target)
            except Exception as e:
                logger.error(f"Failed to retrieve '{link}' for '{target.name}': {e}")
            try:
                data = extract.execute(driver, target)
                logger.info(f"Retrieved '{data}'")
            except Exception as e:
                logger.error(f"Failed to extract target data from '{link}' for '{target.name}': {e}")  # noqa:E501
    # attempt to disconnect all connection resources
    try:
        controller.disconnect()
    except Exception as e:
        logger.critical(f"Scraper failed to disconnect: {e}", exc_info=True)
