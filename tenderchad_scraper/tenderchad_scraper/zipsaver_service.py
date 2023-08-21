import logging
import os
import re

from zipfile import ZipFile
from pathlib import Path

from .s3_service import UploadToS3
from .title_handler import rename_title
from .saver_utils import convert_doc_to_docx, clear_tender_number


class ZipArchivedFileSaverService():
    def __init__(self, path, title, number):
          self.path = path
          self.title = title
          self.number = clear_tender_number(number)
    
    def _save_zipped_file(self):
        try:
            logging.warning(self.path)
            self.zip_obj = ZipFile(self.path)
            
            with self.zip_obj:
                archive_encoding = 'cp866'
                print(self.zip_obj.namelist())

                for filename in self.zip_obj.namelist():
                    print(filename.encode('cp437').decode(archive_encoding))

                    if filename.endswith("/"):
                        continue
                    if filename.endswith(".doc"):
                        self.__save_doc_file(filename=filename)
                    # else:
                    #     self.__save_common_file(filename=filename)

            self.zip_obj.close()
            # os.remove(self.path)
            print("OK")
        except Exception as e:
            print(e)
            # os.remove(self.path)

    def __save_common_file(self, filename):
        archive_encoding = 'cp866'
        __bytes = self.zip_obj.read(filename)
        __item_info = self.zip_obj.getinfo(filename)
        __name = __item_info.filename
        __name = __name.encode('cp437').decode(archive_encoding)
        __correct_filename = rename_title(__name)
        # with open(f"temp/{__correct_filename}", "wb") as binary_file:
        #         binary_file.write(__bytes)
        upload_service = UploadToS3(self.number, __correct_filename, __bytes)
        upload_service.upload_to_s3()

    def __save_doc_file(self, filename):
        archive_encoding = 'cp866'
        # make folder temp/{tender-number}
        path = Path.cwd() / "temp" / str(self.number)
        # extract .doc file to folder above 
        doc_path = self.zip_obj.extract(filename, Path(path))
        # decode filename to rename file with proper name
        __name = filename.encode('cp437').decode(archive_encoding)
        __correct_filename = rename_title(__name)
        correct_doc_path = doc_path.replace(filename, __correct_filename)
        os.rename(doc_path, correct_doc_path)
        # make doc -> docx
        docx_path = convert_doc_to_docx(correct_doc_path)
        logging.warning(docx_path)

    
