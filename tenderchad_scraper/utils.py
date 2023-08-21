from datetime import datetime
from dateutil.relativedelta import relativedelta

async def generate_url(params):
    """Function that generates URL according to preferences for "zakupki.gov.ru" site.

    Args:
        body (dict): Dictionary with keywords, technologies, stage, law, price and date

    Returns:
        str: URL string
    """

    keywords = params.get("search")
    stages = params.get("purchaseStage")
    law_type = params.get("federalLaw")
    date_min = params.get("minDate")
    date_max = params.get("maxDate")
    price_min = params.get("minPrice")
    price_max = params.get("maxPrice")
    supplier_definition = params.get("supplier")

    if not (date_min and date_max):
        date_min = (datetime.now() - relativedelta(years=1)).strftime("%d.%m.%Y")
        date_max = datetime.now().strftime("%d.%m.%Y")

    date_list = [date_min, date_max]
    price_list = [price_min, price_max]

    basic_url = "https://zakupki.gov.ru/epz/order/extendedsearch/results.html?"
    search_url = "searchString="
    url_tail = "&morphology=on&pageNumber=1&sortDirection=false&recordsPerPage=_&showLotsInfoHidden=false&sortBy=UPDATE_DATE&currencyIdGeneral=-1"
    law_url = ""
    stage_url = ""
    price_url = ""
    date_url = ""
    supplier_url = ""

    keywords = keywords.replace(" ", "+")

    fz_names = {"44-ФЗ": "&fz44=on", "223-ФЗ": "&fz223=on"}

    stage_names = {
        "Подача заявок": "&af=on",
        "Работа комиссии": "&ca=on",
        "Закупка завершена": "&pc=on",
        "Определение поставщика завершено": "&pc=on",
        "Закупка отменена": "&pa=on",
        "Определение поставщика отменено": "&pa=on",
    }

    supplier_names = {
        "Электронный аукцион": {
            "fz44": "EA20%2CEAP20%2CEA44%2CEAP44%2CINM111%2CINMP111%2CZA111%2CZA44%2CZAP44%2CEEA20%2CEEA44",
            "fz223": "EF%2CAE%2CAESMBO%2COA",
        },
        "Запрос котировок": {
            "fz44": "ZK504%2CZKP504%2CZK20%2CZKP20%2CZKOP44%2CZKE44%2CZKI44%2CZKB44%2CZKBGP44%2CZK44%2CZKP44%2CZKOO44",
            "fz223": "ZK504%2CZKP504%2CZK20%2CZKP20%2CINM111%2CINMP111%2CZK111%2CZKB111%2CZKI44%2CZK%2CZKESMBO",
        },
        "Открытый конкурс": {
            "fz44": "INM111%2CINMP111%2COK111%2COKU111%2COKD111%2CZKK111%2CZKKU111%2CZKKD111%2COK504%2COKP504%2COK20%2COKP20%2COKK504%2COKA504%2COKA20%2COKI504%2COKB504%2COKI20%2COKB20%2COKU504%2COKUP504%2COKUK504%2COKUI504%2COK44%2COKP44%2CPK44%2COKA44%2CZKK44%2CZKKP44%2CZKKI44%2CZKKE44%2COKD504%2COKDP504%2COKDK504%2COKDI504%2CZKKU44%2CZKKUP44%2CZKKUI44%2CZKKUE44%2CZKKD44%2CZKKDP44%2CZKKDI44%2CZKKDE",
            "fz223": "",
        },
    }
    actuality_status = True
    if (stages != []) and (stages != [""]) and (stages != None):
        for stage in stages:
            if (stage in s for s in stage_names.keys()):
                stage_url += stage_names.get(stage)

    print(actuality_status)
    if (law_type != []) and (law_type != [""]) and (law_type != None):
        for law in law_type:
            if (law in s for s in fz_names.keys()):
                law_url += fz_names.get(law)

    if (
        (supplier_definition != [])
        and (supplier_definition != [""])
        and (supplier_definition != None)
        and (supplier_definition != [None])
    ):
        if not all(elem in supplier_definition for elem in list(supplier_names.keys())):
            supplier_url = "&placingWayList="
            if law_url:
                if "44-ФЗ" in law_type:
                    for sup in supplier_definition:
                        try:
                            supplier_url += supplier_names.get(sup).get("fz44") + "%"
                        except:
                            pass
                    supplier_url += "&selectedLaws=FZ44"
                if "223-ФЗ" in law_type:
                    for sup in supplier_definition:
                        try:
                            supplier_url += supplier_names.get(sup).get("fz223") + "%"
                        except:
                            pass
                    supplier_url += "&selectedLaws=FZ223"

        else:
            pass
    else:
        pass

    if (
        (price_list == [])
        and (price_list == [""])
        and (price_list != None)
        and (price_list != [[], []])
    ):
        price_url = ""
    else:
        price_keys = ["&priceFromGeneral=", "&priceToGeneral="]
        for i, price in enumerate(price_list):
            if price != None:
                date_url += price_keys[i] + price

    if (date_list == []) and (date_list == [""]) and (date_list != None):
        date_url = ""
    else:
        print(date_list)
        date_keys = ["&publishDateFrom=", "&applSubmissionCloseDateFrom="]
        for i, date in enumerate(date_list):
            if date:
                date_url += date_keys[i] + date

    generated_url = (
        basic_url
        + search_url
        + keywords
        + url_tail
        + law_url
        + stage_url
        + supplier_url
        + price_url
        + date_url
    )
    print(generated_url)
    return generated_url
