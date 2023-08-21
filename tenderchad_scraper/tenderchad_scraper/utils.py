
import logging

from .saver_service import FileSaver


def handle_bytes(response, title, number):
    logging.warning("i have  silly thing to say")
    save_manager = FileSaver(title, response.content, number)
    save_manager._save_file()

