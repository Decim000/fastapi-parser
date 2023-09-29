import os
import logging

from pathlib import Path

from .filesaver_service.saver_service import FileSaver
from .filesaver_service.saver_utils import clear_tender_number


def handle_bytes(response, title: str, number: str) -> list:
    """External function for handling file saving outside of the scrapy framework.

    Args:
        response (requests.Response): Response object
        title (str): title of the file.
        number (str): number of the tender.

    Returns:
        list: All collected filenames
    """
    logging.warning("start scraping...")
    
    number = clear_tender_number(number)
    # make temp/number folder
    TEMP_PATH = Path.cwd()/"temp"/number
    if not os.path.exists(TEMP_PATH):
        os.makedirs(TEMP_PATH)
    
    # call savemanager for downloading files
    save_manager = FileSaver(title, response.content, number, TEMP_PATH)
    save_manager._save_file()

    logging.warning(f"i found all filenames: {save_manager._files}")

    return save_manager._files if save_manager._files else []
