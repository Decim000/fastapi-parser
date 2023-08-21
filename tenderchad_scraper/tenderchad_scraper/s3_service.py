import boto3
import logging

from pathlib import Path
from environ import Env

from .saver_utils import clear_tender_number

env = Env()
Env.read_env()

AWS_ACCESS_KEY_ID = env("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = env("AWS_SECRET_ACCESS_KEY")
AWS_STORAGE_BUCKET_NAME = env("AWS_STORAGE_BUCKET_NAME")
AWS_DOCS_FOLDER = env("AWS_DOCS_FOLDER")

client = boto3.client(
        "s3",
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    )

class UploadToS3:
    def __init__(self, number, title, bytes):
        self.client = client
        self.number = number
        self.title = title
        self.file = bytes

    def upload_to_s3(self):
        try:
            number_folder = clear_tender_number(self.number)
            full_path = f"{AWS_DOCS_FOLDER}{number_folder}/{self.title}"
            self.client.put_object(Body=self.file, Bucket=AWS_STORAGE_BUCKET_NAME, Key=full_path)
            
        except:
            logging.error("Error while uploading to S3")

    def upload_to_s3_from_disk(self):
        try:
            number_folder = clear_tender_number(self.number)
            path = Path.cwd() / "temp" / str(number_folder) / self.title
            key = f"{AWS_DOCS_FOLDER}{number_folder}/{self.title}"
            self.client.upload_file(path, AWS_STORAGE_BUCKET_NAME, key)

        except:
            logging.error("Error while uploading to S3")