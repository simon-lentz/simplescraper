from typing import List

import scraper.etl.interaction as interaction
import scraper.etl.extraction as extraction

from scraper.config.validator import TargetConfig
from scraper.config.logging import StructuredLogger


class TargetManager:
    def __init__(self, logger: StructuredLogger):
        self.logger = logger

    def load_input(self, data) -> List[str]:
        """Loads the list of links from the target input file"""
        input_file = data.input_file
        if input_file.exists():
            with open(input_file, "r") as file:
                return [line.strip() for line in file if line.strip()]

    def perform_startup(self, driver, data: TargetConfig):
        startup = data.startup
        if startup:
            for startup_dict in startup:
                try:
                    self._perform_interaction(driver, startup_dict)
                except Exception as e:
                    self.logger.error(f"Error performing startup item: {e}", exc_info=True)  # noqa:E501

    def perform_interactions(self, driver, data: TargetConfig):
        interactions = data.interactions
        if interactions:
            for interaction_dict in interactions:
                try:
                    self._perform_interaction(driver, interaction_dict)
                except Exception as e:
                    self.logger.error(f"Error performing interaction: {e}", exc_info=True)   # noqa:E501

    def _perform_interaction(self, driver, interaction_dict):
        for interaction_name, params in interaction_dict.items():
            try:
                interaction_func = getattr(interaction, interaction_name)
                interaction_func(driver, *params)
            except Exception as e:
                raise Exception(f"Error performing interaction '{interaction_name}': {e}")   # noqa:E501

    def perform_extractions(self, driver, data: TargetConfig):
        extracted_data = {}
        extractions = data.extractions
        if extractions:
            for extraction_dict in extractions:
                try:
                    extraction_name, data = self._perform_extraction(driver, extraction_dict)  # noqa:E501
                    extracted_data[extraction_name] = data
                except Exception as e:
                    self.logger.error(f"Error performing extraction: {e}", exc_info=True)  # noqa:E501
        return extracted_data

    def _perform_extraction(self, driver, extraction_dict):
        for extraction_name, _ in extraction_dict.items():
            try:
                extraction_func = getattr(extraction, extraction_name)
                data = extraction_func(driver)  # driver, *params
                return extraction_name, data
            except Exception as e:
                raise Exception(f"Error performing extraction '{extraction_name}': {e}")
