from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def click(driver: WebDriver, locator: str):
    """
    Attempts to click on a web element immediately. If unsuccessful, it waits
    for the element to be clickable and tries using Action Chains.
    """
    element = None  # Define element outside of try-except to avoid scope issues
    try:
        # First, try to find and click the element immediately
        element = driver.find_element(By.XPATH, locator)
        driver.execute_script("arguments[0].scrollIntoView();", element)
        element.click()
    except Exception:
        try:
            # If immediate interaction fails, then wait and retry with Action Chains
            element = WebDriverWait(driver, 1, 0.05).until(
                EC.element_to_be_clickable((By.XPATH, locator))
            )
            ActionChains(driver).move_to_element(element).click(element).perform()
        except Exception as e:
            raise Exception(f"Element '{locator}' could not be clicked: {e}")  # noqa:E501
