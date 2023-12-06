import logging
import os

from zipfile import ZipFile
from pathlib import Path

from tenderchad_scraper.s3_service import UploadToS3
from tenderchad_scraper.filesaver_service.saver_utils import convert_doc_to_docx
from tenderchad_scraper.title_util import rename_title
# from saver_utils import convert_doc_to_docx


class ZipArchivedFileSaverService:
    """Class for saving zip-files. Must have encoding.
    """    
    def __init__(self, path, title, number, temp_path):
        self.path = path
        self.title = title
        self.number = number
        self.archive_encoding = 'cp866'
        self.temp_path = temp_path
        self._files = []

    def update_files(self, filename):
        """Add filename to list.

        Args:
            filename (str): name of the file.
        """
        self._files.append(filename)

    def _save_zipped_file(self):
        """Routing function for saving inner files.
        Iterate over all files in the archive and choose the way to save each file.
        """
        try:
            logging.warning(self.path)
            self.zip_obj = ZipFile(self.path)
 
            with self.zip_obj:
                print(self.zip_obj.namelist())

                for filename in self.zip_obj.namelist():
                    print(filename.encode('cp437').decode(self.archive_encoding))

                    if filename.endswith("/"):
                        continue
                    if filename.endswith(".doc"):
                        self.__save_doc_file(filename=filename)
                    else:
                        self.__save_common_file(filename=filename)

            self.zip_obj.close()
            # os.remove(self.path)
            print("OK")

        except Exception as e:
            print(e)
            # os.remove(self.path)

    def __save_common_file(self, filename: str):
        """Function for saving file to S3 with extension that doesn't need to be converted.

        Args:
            filename (str): Name of the file as it is written ib the archive.
        """
        __bytes = self.zip_obj.read(filename)
        __item_info = self.zip_obj.getinfo(filename)
        __name = __item_info.filename
        __name = __name.encode('cp437').decode(self.archive_encoding)
        __correct_filename = rename_title(__name)
        # with open(f"temp/{__correct_filename}", "wb") as binary_file:
        #         binary_file.write(__bytes)
        upload_service = UploadToS3(self.number, __correct_filename, __bytes)
        upload_service.upload_to_s3()

        self.update_files(__correct_filename)

    def __save_doc_file(self, filename):
        """Function for saving .doc-file and uploading to S3.

        Args:
            filename (str): Name of the file as it is written ib the archive.
        """
        # extract .doc file to folder above 
        doc_path = self.zip_obj.extract(filename, Path(self.temp_path))

        # decode filename to rename file with proper name
        __name = filename
        __name = filename.encode('cp437').decode(self.archive_encoding)
        __correct_filename = rename_title(__name)
        correct_doc_path = doc_path.replace(filename, __correct_filename)
        os.rename(doc_path, correct_doc_path)

        # make doc -> docx
        docx_path = convert_doc_to_docx(correct_doc_path)
        logging.warning(docx_path)

        # upload .doc file
        upload_service = UploadToS3(self.number, __correct_filename, None)
        upload_service.upload_to_s3_from_disk()

        # upload .docx file
        docx_filename = docx_path.split("/")[-1]
        upload_service = UploadToS3(self.number, docx_filename, None)
        upload_service.upload_to_s3_from_disk()

        # remove files from disk
        os.remove(correct_doc_path)
        os.remove(docx_path)

        # save filename to all filenames
        self.update_files(__correct_filename)
        self.update_files(docx_filename)