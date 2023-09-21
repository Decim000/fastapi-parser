import re


def rename_title(title: str) -> str:
    """ Util function for replacing symbols in filename.

    Args:
        title (str): Title of the file.

    Returns:
        str: Renamed title with replaced symbols
    """
    try:
        title_to_list = title.split("/")
        title = title_to_list[-1]
        re.search("\((.*?)\)", title)
        title = title.replace("(", "").replace(")", "")
    except:
        pass

    try:
        title = title.replace(" ", "_")
    except:
        pass

    try:
        title = title.replace("№", "")
    except:
        pass

    try:
        title = title.replace(",", "")
    except:
        pass

    try:
        title = title.replace("«", "").replace("»", "")
    except:
        pass

    try:
        title = title.replace("+", "")
    except:
        pass

    try:
        title = title.replace("[", "")
    except:
        pass

    try:
        title = title.replace("]", "")
    except:
        pass

    return title
