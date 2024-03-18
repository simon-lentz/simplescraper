from typing import List

from scraper.config.logging import StructuredLogger
from scraper.web.controller import WebController
from scraper.config.validator import TargetConfig

from .target import TargetManager


def run_scraper(logger: StructuredLogger, controller: WebController, targets: List[TargetConfig]):  # noqa:E501
    manager = TargetManager(logger)
    try:
        controller.connect()
    except Exception as e:
        logger.critical(f"Scraper failed to connect: {e}", exc_info=True)
    for cfg in targets:
        try:
            connection = controller.get_connection(cfg.target_name)
            driver = connection.get_driver()
            controller.make_request(cfg.target_name, cfg.target_domain)
            manager.perform_startup(driver, cfg)
            logger.info(f"Startup complete for '{cfg.target_name}'")  # noqa:E501
            links = manager.load_input(cfg)
            for link in links:
                controller.make_request(cfg.target_name, link)
                try:
                    manager.perform_interactions(driver, cfg)
                except Exception as e:
                    logger.warning(f"TargetManager failed to perform interactions for '{cfg.target_name}': {e}", exc_info=True)  # noqa:E501
                try:
                    extracted_cfg = manager.perform_extractions(driver, cfg)  # noqa:E501
                    logger.info(f"TargetManager for '{cfg.target_name}' extracted: '{extracted_cfg}'")  # noqa:E501
                except Exception as e:
                    logger.warning(f"TargetManager failed to perform extractions for '{cfg.target_name}': {e}", exc_info=True)  # noqa:E501
        except Exception as e:
            logger.warning(f"Startup failed for '{cfg.target_name}': {e}", exc_info=True)  # noqa:E501
    try:
        controller.disconnect()
    except Exception as e:
        logger.critical(f"Scraper failed to disconnect: {e}", exc_info=True)
