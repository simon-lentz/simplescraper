from typing import List

import scraper.etl.interaction as interact
import scraper.etl.extraction as extract

from scraper.config.validator import TargetConfig
from scraper.config.logging import StructuredLogger


class TargetManager:
    def __init__(self, logger: StructuredLogger):
        self.logger = logger

    def load_input(self, data: TargetConfig) -> List[str]:
        """Loads the list of links from the target input file"""
        input_file = data.input_file
        if input_file.exists():
            try:
                with open(input_file, "r") as file:
                    return [line.strip() for line in file if line.strip()]
            except Exception as e:
                self.logger.error(f"Failed to read links from input file '{input_file}' for '{data.target_name}': {e}")  # noqa:E501
                raise
        else:
            raise FileNotFoundError(f"Failed to load '{input_file}' for '{data.target_name}'")  # noqa:E501

    def perform_startup(self, driver, data: TargetConfig):
        startup = data.startup
        if startup:
            for action in startup:
                try:
                    self._do_interaction(driver, **action.dict())
                except Exception as e:
                    raise e
        else:
            self.logger.info(f"No startup actions specified for '{data.target_name}'")

    def perform_interactions(self, driver, data: TargetConfig):
        interactions = data.interactions
        if interactions:
            for interaction in interactions:
                try:
                    self._do_interaction(driver, **interaction.dict())
                except Exception as e:
                    raise e
        else:
            self.logger.info(f"No interactions specified for '{data.target_name}'")

    def _do_interaction(self, driver, type: str, selector: str, **kwargs):
        match type:
            case "click":
                try:
                    interact.click(driver, selector)
                except Exception as e:
                    self.logger.warning(f"Failed to click '{selector}': {e}", exc_info=True)  # noqa:E501

    def perform_extractions(self, driver, data: TargetConfig):
        extracted_data = []
        extractions = data.extractions
        if extractions:
            for extraction in extractions:
                try:
                    output = self._do_extraction(driver, **extraction.dict())
                    extracted_data.append(output)
                except Exception as e:
                    raise e
            return extracted_data
        else:
            self.logger.info(f"No extractions specified for '{data.target_name}'")

    def _do_extraction(self, driver, type: str, selector: str, **kwargs):
        match type:
            case "source":
                try:
                    page_source_string = extract.source(driver)
                    return page_source_string
                except Exception as e:
                    self.logger.warning(f"Failed to extract page source: {e}", exc_info=True)  # noqa:E501
            case "table":
                try:
                    table = extract.table(driver, selector)
                    return table
                except Exception as e:
                    self.logger.warning(f"Failed to extract table from '{selector}': {e}", exc_info=True)  # noqa:E501
