import re

def rename_title(title):
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
