import os
import re
import aspose.words as aw

from pathlib import Path

from .title_handler import rename_title

def convert_doc_to_docx(tender_document_path: str) -> str:
    """Get .doc version of file and saves copy in .docx format.

    Args:
        tender_document_path (str): str path to .doc file.

    Returns:
        str: str path to .docx copy.
    """
    # create path
    tender_document_path = Path(tender_document_path)

    # instantiatiate doc
    doc = aw.Document(tender_document_path.as_posix())

    # fix falename and make it docx
    __correct_filename = rename_title(tender_document_path.name)
    docx_path = f"{os.path.dirname(tender_document_path)}/{__correct_filename}x"

    # save doc as docx
    doc.save(docx_path, aw.SaveFormat.DOCX)
    return docx_path

def clear_tender_number(number):
    try:
        clean_number = re.findall(r'\d+', number)[0]
        return clean_number if clean_number != [] else number 
    except:
        return number