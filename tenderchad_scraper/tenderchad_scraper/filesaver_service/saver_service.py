import io
import os
import logging
import aspose.words as aw

from tenderchad_scraper.s3_service import UploadToS3
from tenderchad_scraper.filesaver_service.rarsaver_service import RarArchivedFileSaverService
from tenderchad_scraper.filesaver_service.zipsaver_service import ZipArchivedFileSaverService
from tenderchad_scraper.title_util import rename_title


class FileSaver:

    """Common class for saving files with different extensions.
    If file in zip/rar, service call for special saver class.
    """    

    def __init__(self, title, bytes, number, temp_path) -> None:
        self.title = title
        self.extension = self.title.split(".")[-1]
        self.file = bytes
        self.number = number
        self.temp_path = temp_path
        self._files = []

    def accumulate_files(self, filename):
        """Add filename to list.

        Args:
            filename (str): name of the file.
        """ 
        self._files.append(filename)


    def _save_file(self):
        """ Routing function to choose the way to save file according to its extension
        """    
        logging.warning(f"{self.extension}")

        if (self.extension != "doc") and (self.extension != "zip") and (self.extension != "rar"):
            # upload file in common format
            upload_service = UploadToS3(self.number, self.title, self.file)
            upload_service.upload_to_s3()

            # save filename to all filenames
            self.accumulate_files(self.title)

        if self.extension == "doc":
            # MAYBE use subprocess and libreoffice

            # extract .doc data
            data = io.BytesIO(self.file)
            document = aw.Document(data)

            # make temp/number folder to store .docx
            if not os.path.exists(self.temp_path):
                os.makedirs(self.temp_path)

            # rename .docx file and save to folder
            self.title = rename_title(self.title)
            docx_path = os.path.join(self.temp_path, f"{self.title}x")
            document.save(docx_path, aw.SaveFormat.DOCX)
            # fp = tempfile.NamedTemporaryFile(suffix=".doc")
            # fp.write(self.file)
            # fp.seek(0)
            # temp_doc_path = fp.name
            # subprocess.call(['lowriter', '--headless', '--convert-to', 'docx', temp_doc_path])
            # fp.close()

            # upload .doc
            upload_service = UploadToS3(self.number, self.title, self.file)
            upload_service.upload_to_s3()

            # upload .docx
            upload_service_docx = UploadToS3(self.number, f"{self.title}x", None)
            upload_service_docx.upload_to_s3_from_disk()

            # remove temp .docx file
            os.remove(docx_path)

            # save filename to all filenames
            self.accumulate_files(self.title)
            self.accumulate_files(f"{self.title}x")

        if self.extension == "zip":
            # make temp/number folder
            if not os.path.exists(self.temp_path):
                os.makedirs(self.temp_path)

            # save archive to temp/number
            with open(f"{self.temp_path}/{self.title}", "wb") as binary_file:
                binary_file.write(self.file)
            zip_saver = ZipArchivedFileSaverService(path = os.path.abspath(f"{self.temp_path}/{self.title}"), title = self.title, number = self.number, temp_path=self.temp_path)
            zip_saver._save_zipped_file()

            # save filename to all filenames
            self.accumulate_files(self.title)
            self.accumulate_files(zip_saver._files)

        if self.extension == "rar":
            # make temp/number folder
            if not os.path.exists(self.temp_path):
                os.makedirs(self.temp_path)

            # save archive to temp/number
            with open(f"{self.temp_path}/{self.title}", "wb") as binary_file:
                binary_file.write(self.file)
            rar_saver = RarArchivedFileSaverService(path = os.path.abspath(f"{self.temp_path}/{self.title}"), title = self.title, number = self.number, temp_path=self.temp_path)
            rar_saver._save_zipped_file()

            # save filename to all filenames
            self.accumulate_files(self.title)
            self.accumulate_files(zip_saver._files)


