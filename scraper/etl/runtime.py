from scraper.config.logging import StructuredLogger
from scraper.web.controller import setup_controller


def run_scraper(logger: StructuredLogger, cfg):
    controller = setup_controller(logger, cfg)
    try:
        controller.connect()
    except Exception as e:
        logger.critical(f"Scraper failed to connect: {e}", exc_info=True)
    for target in cfg["target"]:
        try:
            connection = controller.get_connection(target.target_name)
            driver = connection.get_driver()
            controller.make_request(target.target_name, target.target_domain)
            logger.info(f"Driver for connection '{connection.name}' retrieved '{driver.title}' from '{target.target_domain}'")  # noqa:E501
        except Exception as e:
            logger.warning(f"'{target.target_name}' driver failed to retrieve '{target.target_domain}': {e}", exc_info=True)  # noqa:E501
    try:
        controller.disconnect()
    except Exception as e:
        logger.critical(f"Scraper failed to disconnect: {e}", exc_info=True)
