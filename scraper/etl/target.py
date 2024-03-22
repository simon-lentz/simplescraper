import pandas as pd
from typing import List
from pathlib import Path

from scraper.config.logging import StructuredLogger
from scraper.config.validator import TargetConfig
from scraper.web.controller import WebController

from .extraction import ExtractionManager
from .interaction import InteractionManager


class TargetManager:
    def __init__(self, logger: StructuredLogger, controller: WebController):
        self.logger = logger
        self.controller = controller

    def scrape_target(self, target: TargetConfig):

        try:
            # Perform startup actions with target domain
            if target.startup:
                connection = self.controller.get_connection(target.name)
                self.controller.make_request(target.name, target.domain)
                driver = connection.driver
                startup_interact = InteractionManager(self.logger, driver)
                startup_interact.execute(target.name, target.startup)

            # Retrieve links, perform interactions
            for link in self._get_target_links(target):
                connection = self.controller.get_connection(target.name)
                self.controller.make_request(target.name, link)
                driver = connection.driver
                if target.interactions:
                    interact = InteractionManager(self.logger, driver)
                    interact.execute(target.name, target.interactions)
                extract = ExtractionManager(self.logger, driver)
                extraction_results = extract.execute(target.name, target.extractions)
                for output_file, result in extraction_results.items():
                    self.write_output(target.name, result["data"], result["output_type"], Path(output_file))  # noqa:E501

        except Exception as e:
            self.logger.error(f"Failed to scrape '{target.name}': {e}", exc_info=True)

    def _get_target_links(self, target: TargetConfig) -> List[str]:
        input_file = target.input_file
        if input_file.exists():
            try:
                with open(input_file, "r") as file:
                    return [line.strip() for line in file if line.strip()]
            except Exception as e:
                self.logger.error(f"Failed to read links from input file '{input_file}' for '{target.name}': {e}", exc_info=True)  # noqa:E501

    def write_output(self, name: str, data: List[List[str]], output_type: str, output_file: Path):  # noqa:E501
        if not data:
            self.logger.error(f"No data to write for output file: {output_file}")
            return
        df = pd.DataFrame(data)
        # Create the directory if it doesn't exist
        output_file.parent.mkdir(parents=True, exist_ok=True)
        match output_type.lower():
            case "csv":
                df.to_csv(output_file, index=False, header=False)
                self.logger.info(f"Output for '{name}' written to CSV: {output_file}")
            case "json":
                df.to_json(output_file, orient='records', lines=True)
                self.logger.info(f"Output for '{name}' written to JSON: {output_file}")
            case "txt" | "text":
                df.to_csv(output_file, index=False, header=False, sep='\t')
                self.logger.info(f"Output for '{name}' written to TXT: {output_file}")
            case "pandas" | "pkl" | "pickle" | "df" | "dataframe":
                df.to_pickle(output_file)
                self.logger.info(f"Output for '{name}' written to PKL: {output_file}")
            case _:
                self.logger.error(f"Unsupported output type for '{name}': '{output_type}'")  # noqa:E501
