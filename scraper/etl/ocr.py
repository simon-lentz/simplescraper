import pytesseract
from io import BytesIO
from PIL import Image, ImageOps, ImageFilter

from scraper.web.controller import WebController
from .exceptions import OCRException


def img_to_txt(target_name: str, link: str, controller: WebController) -> str:  # noqa:E501
    try:
        controller.make_request(target_name, link)
        driver = controller.get_driver(target_name)
        raw_image = driver.get_screenshot_as_png()
        try:
            processed_image = preprocess(raw_image)
            if processed_image:
                try:
                    text = pytesseract.image_to_string(processed_image, config="--psm 7")  # noqa:E501
                    return text.strip()
                except pytesseract.TesseractError as e:
                    raise OCRException(f"Failed to extract string from image for {target_name} at {link}: {e}")  # noqa:E501
        except Exception as e:
            raise OCRException(f"Preprocessing failed for {target_name} at {link}: {e}")
    except Exception as e:
        raise OCRException(f"Failed to retrieve image for {target_name} at {link}: {e}")


def preprocess(raw_image: bytes) -> Image.Image:
    try:
        image = Image.open(BytesIO(raw_image))
        # Define cropping box
        left = (1920 / 2) - 50
        upper = (995 / 2) - 30
        right = left + 100
        lower = upper + 60
        cropped_image = image.crop((int(left), int(upper), int(right), int(lower)))
        # Resizing and filtering
        resized_image = cropped_image.resize(
            (cropped_image.width * 3, cropped_image.height * 3),
            Image.Resampling.LANCZOS,
        )
        median_filtered_image = resized_image.filter(ImageFilter.MedianFilter(size=3))
        grayscale_image = ImageOps.grayscale(median_filtered_image)
        # Thresholding
        threshold = 230
        processed_image = grayscale_image.point(lambda p: p > threshold and 255)
        return processed_image
    except Exception as e:
        raise OCRException("Failed to preprocess the image") from e
