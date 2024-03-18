from .target import TargetManager

from scraper.config.logging import StructuredLogger
from scraper.web.controller import setup_controller


def run_scraper(logger: StructuredLogger, cfg):
    controller = setup_controller(logger, cfg)
    target_manager = TargetManager(logger)
    try:
        controller.connect()
    except Exception as e:
        logger.critical(f"Scraper failed to connect: {e}", exc_info=True)
    for config in cfg["target"]:
        try:
            connection = controller.get_connection(config.target_name)
            driver = connection.get_driver()
            controller.make_request(config.target_name, config.target_domain)
            target_manager.perform_startup(driver, config)
            logger.info(f"Startup complete for '{config.target_name}'")  # noqa:E501
            links = target_manager.load_input(config)
            for link in links:
                controller.make_request(config.target_name, link)
                try:
                    target_manager.perform_interactions(driver, config)
                except Exception as e:
                    logger.warning(f"TargetManager failed to perform interactions for '{config.target_name}': {e}", exc_info=True)  # noqa:E501
                try:
                    extracted_config = target_manager.perform_extractions(driver, config)  # noqa:E501
                    logger.info(f"TargetManager for '{config.target_name}' extracted: '{extracted_config}'")  # noqa:E501
                except Exception as e:
                    logger.warning(f"TargetManager failed to perform extractions for '{config.target_name}': {e}", exc_info=True)  # noqa:E501
        except Exception as e:
            logger.warning(f"Startup failed for '{config.target_name}': {e}", exc_info=True)  # noqa:E501
    try:
        controller.disconnect()
    except Exception as e:
        logger.critical(f"Scraper failed to disconnect: {e}", exc_info=True)
