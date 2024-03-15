from scraper.etl.runtime import run_scraper
from scraper.cmd.cli import run_cli


def main():
    logger, cfg = run_cli()

    if logger is None or cfg is None:
        return

    logger.info("Starting Web Scraper")

    try:
        run_scraper(logger, cfg)
    except Exception as e:
        logger.critical(f"Fatal Error: {e}", exc_info=True)
        return

    finally:
        logger.info("Scraper Exited")
        logger.close()  # Ensure the log file is properly closed


if __name__ == "__main__":
    main()
