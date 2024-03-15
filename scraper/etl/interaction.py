from typing import List
from selenium.webdriver.common.by import By
from selenium.webdriver.support.select import Select
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def click(driver: WebDriver, locator: str, timeout: float = 3, polling: float = 0.05):
    try:
        WebDriverWait(driver, timeout, polling).until(
            EC.element_to_be_clickable((By.XPATH, locator))
        ).click()
    except Exception as e:
        raise RuntimeError(f"click failed: {e}")


def paginate(
    driver: WebDriver, locator: str, timeout: float = 3, polling: float = 0.05
) -> bool:
    """
    Handles pagination if applicable, clicking the 'next' button to load more items.
    """
    try:
        WebDriverWait(driver, timeout, polling).until(
            EC.element_to_be_clickable((By.XPATH, locator))
        ).click()
        return True
    except Exception:
        return False


def dropdown(
    driver: WebDriver,
    locator: str,
    value: str,
    timeout: float = 3,
    polling: float = 0.05,
):
    """
    Selects a value from a dropdown menu identified by the dropdown_locator.
    """
    try:
        select_element = Select(
            WebDriverWait(driver, timeout, polling).until(
                EC.visibility_of_element_located((By.XPATH, locator))
            )
        )
    except Exception as e:
        raise RuntimeError(f"failed to select dropdown with {locator}: {e}")
    try:
        select_element.select_by_value(value)
    except Exception as e:
        raise RuntimeError(f"failed to select {value} from {select_element}: {e}")


def perform_interactions(driver, interactions: List[List]):
    for interaction in interactions:
        try:
            match interaction[0]:
                case "click":
                    click(driver, interaction[1])
                case "paginate":
                    while True:
                        paginate(driver, interaction[1])
                case "dropdown":
                    dropdown(driver, interaction[1], interaction[2])
                case _:
                    raise Exception(f"Unknown Interaction '{interaction[0]}'")
        except Exception as e:
            raise e
