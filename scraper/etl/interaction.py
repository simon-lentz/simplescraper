from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support.wait import WebDriverWait

from scraper.config.logging import StructuredLogger
from scraper.config.validator import TargetConfig


class InteractionManager:
    def __init__(self, logger: StructuredLogger):
        self.logger = logger

    def startup(self, driver: WebDriver, target: TargetConfig):
        startup_actions = target.startup
        if startup_actions:
            for action in startup_actions:
                self._do_interaction(driver, **action.model_dump())
        else:
            self.logger.info(f"No startup actions specified for '{target.name}'")

    def execute(self, driver: WebDriver, target: TargetConfig):
        interactions = target.interactions
        if interactions:
            for interaction in interactions:
                self._do_interaction(driver, **interaction.model_dump())
        else:
            self.logger.info(f"No interactions specified for '{target.name}'")

    def _do_interaction(self, driver: WebDriver, type: str, selector: str):
        match type:
            case "click":
                self._click_element(driver, selector)

    def _click_element(self, driver: WebDriver, locator: str):
        element = None  # Define element outside of try-except to avoid scope issues
        try:
            # First, try to find and click the element immediately
            element = driver.find_element(By.XPATH, locator)
            driver.execute_script("arguments[0].scrollIntoView();", element)
            element.click()
        except Exception:
            try:
                # If immediate interaction fails, then wait and retry with Action Chains
                element = WebDriverWait(driver, 5).until(lambda x: x.find_element(By.XPATH, locator))  # noqa:E501
                ActionChains(driver).move_to_element(element).click(element).perform()
            except Exception as e:
                self.logger.error(f"Element {locator} could not be clicked: {e}", exc_info=True)  # noqa:E501
