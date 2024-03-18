from scraper.etl.runtime import run_scraper
from scraper.cmd.cli import run_cli
from scraper.web.controller import setup_controller


def main():
    logger, cfg = run_cli()

    if logger is None or cfg is None:
        return

    logger.info("Starting Web Scraper")

    try:
        controller = setup_controller(logger, cfg)
        targets = cfg["target"]
        run_scraper(logger, controller, targets)
    except Exception as e:
        logger.critical(f"Fatal Error: {e}", exc_info=True)
        return

    finally:
        logger.info("Scraper Exited")
        logger.close()  # Ensure the log file is properly closed


if __name__ == "__main__":
    main()
