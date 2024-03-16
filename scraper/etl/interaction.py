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


"""
TODO
1. Make specific interactions for a "startup" config dict that will be like:
   {"cookies": "cookies selector", "terms": "terms and conditions selector", etc.}

2. The TargetManager should then use the target domain value with the startup dict
   to prepare the target page for the specific interactions and extractions
"""
