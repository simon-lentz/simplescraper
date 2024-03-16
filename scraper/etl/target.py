from typing import Dict, List

import scraper.etl.interaction as interaction
import scraper.etl.extraction as extraction

from scraper.config.validator import TargetConfig
from scraper.config.logging import StructuredLogger


class TargetManager:
    def __init__(self, logger: StructuredLogger, cfgs: List[TargetConfig]):
        self.logger = logger
        self.targets: Dict[str, TargetConfig] = {}

        self._assign_targets(cfgs)

    def _assign_targets(self, cfgs: List[TargetConfig]):
        for cfg in cfgs:
            self.targets[cfg.target_name] = cfg

    def perform_interactions(self, driver, target: str):
        target_data = self.targets[target]
        interactions = target_data.interactions
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

    def perform_extractions(self, driver, target: str):
        extracted_data = {}
        target_data = self.targets[target]
        extractions = target_data.extractions
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


"""
TODO
1. I think it makes sense to have the first entry in the value list
   be the selector type (for selenium By type), which can then be
   parsed and passed to the extraction/interaction function to allow
   for someone to use the selector of their choice.
2. The current ignored param values "extraction_name, _" will need to be
   integrated into more complex interactions/extractions over time,
   for now just the default target sources will be ok.
"""
