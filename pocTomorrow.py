from flask import Flask, render_template, jsonify
from pprint import pprint
import requests
import json
import pandas as pd
from gspread_dataframe import set_with_dataframe
from flatten_json import flatten
import gspread
from gspread_formatting import *
import gspread_formatting as gsf
# from googleapiclient import discovery
import time
from keys.keys import oauth_token, oauth_client_id
from datetime import datetime, timedelta
from goods import gooooooods

# Указываем путь к JSON
gc = gspread.service_account(filename='keys/mypython-374908-4480952f882c.json')

# Заголовки запроса к Яндексу
HEADERS = {
    'Authorization': f'OAuth oauth_token="{oauth_token}", oauth_client_id="{oauth_client_id}"',
    'Content-Type': 'application/json'
}

# Массив ['листGS', 'campaingId']
campaignIdArray = [
    # [263414250, '49039988', 'CWC'],
    # [1481585305, '48429880', 'LESH'],
    # [2138399644, '46655497', 'Int'],
    [1157524177, '52087697', 'poc-tomorrow']
]

today = datetime.now()

day = f'{today.day:02}'
month = f'{today.month:02}'
year = today.year
date_today = f'{day}-{month}-{year}'
# print(date_today)

yesterday = today - timedelta(days=1)
yesterday_day = f'{yesterday.day:02}'
yesterday_month = f'{yesterday.month:02}'
yesterday_year = yesterday.year
date_yesterday = f'{yesterday_day}-{yesterday_month}-{yesterday_year}'
# print(date_yesterday)

before_yesterday = yesterday - timedelta(days=1)
before_yesterday_day = f'{before_yesterday.day:02}'
before_yesterday_month = f'{before_yesterday.month:02}'
before_yesterday_year = before_yesterday.year
date_before_yesterday = f'{before_yesterday_day}-{before_yesterday_month}-{before_yesterday_year}'
# print(date_before_yesterday)

tomorrow = today + timedelta(days=1)
tomorrow_day = f'{tomorrow.day:02}'
tomorrow_month = f'{tomorrow.month:02}'
tomorrow_year = tomorrow.year
date_tomorrow = f'{tomorrow_day}-{tomorrow_month}-{tomorrow_year}'
print(date_tomorrow)

# print(today.weekday()+1)

# Пробегаю по каждому магазину и листуGS
for campaingId in campaignIdArray:

    # Вывожу Лист и Кампанию
    print('= = = = = = = = = = = = = = = ')
    print('ЛистGS:', campaingId[0])
    print('СampaingId:', campaingId[1])

    # Завтра
    response1 = requests.get(
        'https://api.partner.market.yandex.ru/v2/campaigns/' + '52087697' +
        '/orders.json?page=1&supplierShipmentDateFrom=' +
        date_tomorrow + '&supplierShipmentDateTo=' +
        date_tomorrow + '&status=PROCESSING',
        headers=HEADERS
    ).json()
    print("\nВсего заказов: ", response1['pager']['total'])
    print("Всего страниц: ", response1['pager']['pagesCount'])

    # Количество страниц в ответе
    pagesCount1 = response1['pager']['pagesCount']
    # Переменная в которую соберу все заказы из всех страниц
    data = response1['orders']

    # Тут цикл в котором я забираю вообще все заказы с маркета
    if pagesCount1 > 1:
        for i in range(2, pagesCount1+1):
            response2 = requests.get(
                'https://api.partner.market.yandex.ru/v2/campaigns/' + '52087697' + '/orders.json?page=' +
                str(i) + '&supplierShipmentDateFrom=' + date_tomorrow +
                '&supplierShipmentDateTo=' + date_tomorrow + '&status=PROCESSING',
                headers=HEADERS
            ).json()
            # print("ВОТ ЭТО ",response2)
            data = data + response2['orders']

    # ДатаФрейм
    df = pd.json_normalize(
        data,
        max_level=5,
        record_path=[
            'items',
        ],
        meta=[
            'id',
            'status',
            'substatus',
            'creationDate',
            'itemsTotal',
            'total',
            'deliveryTotal',
            'subsidyTotal',
            'totalWithSubsidy',
            'buyerItemsTotal',
            'buyerTotal',
            'buyerItemsTotalBeforeDiscount',
            'buyerTotalBeforeDiscount',
            'paymentType',
            'paymentMethod',
            ['delivery', 'shipments'],
            ['delivery', 'dates', 'fromDate'],
            ['subsidies'],
            # '',
        ],
        record_prefix='_',
        errors='ignore'
    )

    # Это сглаживает все
    # dict_flattened = (flatten(record, '.') for record in data)
    # df = pd.DataFrame(dict_flattened)

    # Все NaN меняет на 0
    # df.fillna(0)

    # Преобразую в json и вытягиваю shipmentDate
    def get_delivery_shipmentDate(shipmentDate):
        shipmentDate = str(shipmentDate).replace("\'", "\"")
        shipmentDate_data = json.loads(shipmentDate)
        shipmentDate_value = shipmentDate_data['shipmentDate']
        return shipmentDate_value

    # Преобразую в json и вытягиваю amount
    def get_subsidies_amount(amount):
        if pd.isna(amount):
            return 0
        else:
            amount = str(amount).replace(
                "\'", "\"").replace("[", "").replace("]", "")
            amount_data = json.loads(amount)
            amount_value = amount_data['amount']
            return amount_value

    # Количество строк в ДФ
    num_rows = df.shape[0]

    # Цикл в котором преобразую весь столбец delivery.shipments
    for i in range(num_rows):
        df.at[i, 'delivery.shipments'] = get_delivery_shipmentDate(
            df.at[i, 'delivery.shipments'])

    # Цикл в котором преобразую весь столбец subsidies
    for i in range(num_rows):
        df.at[i, 'subsidies'] = get_subsidies_amount(df.at[i, 'subsidies'])

    # Перевод статуса
    status_db = {
        "CANCELLED": '=CONCATENATE("CANCELLED";CHAR(10);"(Заказ отменен)")',
        "DELIVERED": '=CONCATENATE("DELIVERED";CHAR(10);"(Заказ получен покупателем)")',
        "DELIVERY": '=CONCATENATE("DELIVERY";CHAR(10);"(Заказ передан в службу доставки)")',
        "PICKUP": '=CONCATENATE("PICKUP";CHAR(10);"(Заказ доставлен в пункт самовывоза)")',
        "PROCESSING": '=CONCATENATE("PROCESSING";CHAR(10);"(Заказ находится в обработке)")',
        "UNPAID": '=CONCATENATE("UNPAID";CHAR(10);"(Заказ оформлен, но еще не оплачен [если выбрана оплата при оформлении])")',
    }

    def get_status_translate(status):
        try:
            return status_db[str(status)]
        except:
            return status

    for i in range(num_rows):
        df.at[i, 'status'] = get_status_translate(df.at[i, 'status'])

    # Перевод субстатуса
    substatus_db = {
        'STARTED': '=CONCATENATE("STARTED"; CHAR(10); "(Заказ подтвержден, его можно начать обрабатывать)")',
        'READY_TO_SHIP': '=CONCATENATE("READY_TO_SHIP"; CHAR(10); "(Заказ собран и готов к отправке)")',
        'SHIPPED': '=CONCATENATE("SHIPPED"; CHAR(10); "(Заказ передан службе доставки)")',
        'DELIVERY_SERVICE_UNDELIVERED': '=CONCATENATE("DELIVERY_SERVICE_UNDELIVERED"; CHAR(10); "(Служба доставки не смогла доставить заказ)")',
        'PROCESSING_EXPIRED': '=CONCATENATE("PROCESSING_EXPIRED"; CHAR(10); "(Магазин не обработал заказ в течение семи дней)")',
        'REPLACING_ORDER': '=CONCATENATE("REPLACING_ORDER"; CHAR(10); "(Покупатель решил заменить товар другим по собственной инициативе)")',
        'RESERVATION_EXPIRED': '=CONCATENATE("RESERVATION_EXPIRED"; CHAR(10); "(Покупатель не завершил оформление зарезервированного заказа в течение 10 минут)")',
        'RESERVATION_FAILED': '=CONCATENATE("RESERVATION_FAILED"; CHAR(10); "(Маркет не может продолжить дальнейшую обработку заказа)")',
        'SHOP_FAILED': '=CONCATENATE("SHOP_FAILED"; CHAR(10); "(Магазин не может выполнить заказ)")',
        'USER_CHANGED_MIND': '=CONCATENATE("USER_CHANGED_MIND"; CHAR(10); "(Покупатель отменил заказ по личным причинам)")',
        'USER_NOT_PAID': '=CONCATENATE("USER_NOT_PAID"; CHAR(10); "(Покупатель не оплатил заказ (для типа оплаты PREPAID) в течение 30 минут)")',
        'USER_REFUSED_DELIVERY': '=CONCATENATE("USER_REFUSED_DELIVERY"; CHAR(10); "(Покупателя не устроили условия доставки)")',
        'USER_REFUSED_PRODUCT': '=CONCATENATE("USER_REFUSED_PRODUCT"; CHAR(10); "(Покупателю не подошел товар)")',
        'USER_REFUSED_QUALITY': '=CONCATENATE("USER_REFUSED_QUALITY"; CHAR(10); "(Покупателя не устроило качество товара)")',
        'USER_UNREACHABLE': '=CONCATENATE("USER_UNREACHABLE"; CHAR(10); "(Не удалось связаться с покупателем)")',
        'USER_WANTS_TO_CHANGE_DELIVERY_DATE': '=CONCATENATE("USER_WANTS_TO_CHANGE_DELIVERY_DATE"; CHAR(10); "(Покупатель хочет получить заказ в другой день)")',
        'CANCELLED_COURIER_NOT_FOUND': '=CONCATENATE("CANCELLED_COURIER_NOT_FOUND"; CHAR(10); "(Не удалось найти курьера)")',
    }

    # substatus_db = {
    #     'STARTED': 'STARTED (Заказ подтвержден, его можно начать обрабатывать)',
    #     'READY_TO_SHIP': 'READY_TO_SHIP (Заказ собран и готов к отправке)',
    #     'SHIPPED': 'SHIPPED (Заказ передан службе доставки)',
    #     'DELIVERY_SERVICE_UNDELIVERED': 'DELIVERY_SERVICE_UNDELIVERED (Служба доставки не смогла доставить заказ)',
    #     'PROCESSING_EXPIRED': 'PROCESSING_EXPIRED (Магазин не обработал заказ в течение семи дней)',
    #     'REPLACING_ORDER': 'REPLACING_ORDER (Покупатель решил заменить товар другим по собственной инициативе)',
    #     'RESERVATION_EXPIRED': 'RESERVATION_EXPIRED (Покупатель не завершил оформление зарезервированного заказа в течение 10 минут)',
    #     'RESERVATION_FAILED': 'RESERVATION_FAILED (Маркет не может продолжить дальнейшую обработку заказа)',
    #     'SHOP_FAILED': 'SHOP_FAILED (Магазин не может выполнить заказ)',
    #     'USER_CHANGED_MIND': 'USER_CHANGED_MIND (Покупатель отменил заказ по личным причинам)',
    #     'USER_NOT_PAID': 'USER_NOT_PAID (Покупатель не оплатил заказ (для типа оплаты PREPAID) в течение 30 минут)',
    #     'USER_REFUSED_DELIVERY': 'USER_REFUSED_DELIVERY (Покупателя не устроили условия доставки)',
    #     'USER_REFUSED_PRODUCT': 'USER_REFUSED_PRODUCT (Покупателю не подошел товар)',
    #     'USER_REFUSED_QUALITY': 'USER_REFUSED_QUALITY (Покупателя не устроило качество товара)',
    #     'USER_UNREACHABLE': 'USER_UNREACHABLE (Не удалось связаться с покупателем)',
    #     'USER_WANTS_TO_CHANGE_DELIVERY_DATE': 'USER_WANTS_TO_CHANGE_DELIVERY_DATE (Покупатель хочет получить заказ в другой день)',
    #     'CANCELLED_COURIER_NOT_FOUND': 'CANCELLED_COURIER_NOT_FOUND (Не удалось найти курьера)',
    # }

    def get_substatus_translate(substatus):
        try:
            return substatus_db[str(substatus)]
        except:
            return substatus

    for i in range(num_rows):
        df.at[i, 'substatus'] = get_substatus_translate(df.at[i, 'substatus'])

    # Получаю названия колонок из ДФ
    columnInData = list(df.columns.values)
    print("\nВсе колонки в ДФ: \n", columnInData)

    # Колонки, которые удалю
    needDrop = [
        '_vat',
        '_partnerWarehouseId',
        '_promos',
        '_price',
        '_buyerPriceBeforeDiscount',
        '_offerId',
        '_instances',
        '_subsidy',
        '_feedCategoryId',
        '_feedId',
        '_id'
    ]

    # Если попробую удалить столбец, которого нет в ДФ, будет ошибка
    # Поэтому делаю массив, в котором будут только те колонки, которые нужно удалить и они есть в ДФ
    result_needDrop = list(set(columnInData) & set(needDrop))
    print("\nЭти колонки удаляю: \n", result_needDrop)

    # # Удаляю колонки
    df.drop(
        columns=result_needDrop,
        axis=1,
        inplace=True
    )
    # =================================================================================

    # Открываем таблицу
    sh = gc.open_by_url(
        'https://docs.google.com/spreadsheets/d/1Vx9RkLzxtsncULEkd7XsHQgVrcS-dzQSdocZjLp8Uw0/edit#gid=0')

    # Очистить лист
    sh.values_clear("'" + campaingId[2] + "'!A1:X")

    # Лист, в который вставляем
    worksheet = sh.worksheet(campaingId[2])
# =================================================================================
    df_new = df
    # Меняем колонки местами
    df_new = pd.DataFrame(
        df,
        columns=[
            'id',
            'status',
            'substatus',
            # 'creationDate',
            # 'itemsTotal',
            # 'total',
            # 'deliveryTotal',
            # 'subsidyTotal',
            # 'totalWithSubsidy',
            # 'buyerItemsTotal',
            # 'buyerTotal',
            # 'buyerItemsTotalBeforeDiscount',
            # 'buyerTotalBeforeDiscount',
            # 'paymentType',
            # 'paymentMethod',
            '_offerName',
            # '_buyerPrice',
            # '_buyerPriceBeforeDiscount',
            '_count',
            '_shopSku',
            # '_subsidy',
            # 'delivery.dates.fromDate',
            'delivery.shipments',
            # 'subsidies',
        ]
    )

    # Переводим заголовки на русский
    df_new.rename(
        columns={
            'id': 'Идентификатор заказа',
            'status': 'Статус заказа',
            'substatus': 'Этап обработки заказа',
            'creationDate': 'Дата и время оформления заказа',
            'itemsTotal': 'Стоимость всех товаров в заказе в валюте магазина',
            'total': 'Стоимость всех товаров в заказе в валюте магазина',
            'deliveryTotal': 'Стоимость доставки в валюте заказа',
            'subsidyTotal': 'Общее вознаграждение партнеру за скидки по всем товарам в заказе',
            'totalWithSubsidy': 'Сумма стоимости всех товаров в заказе и вознаграждения за них в валюте магазина (сумма параметров total и subsidyTotal)',
            'buyerItemsTotal': 'Стоимость всех товаров в заказе в валюте покупателя',
            'buyerTotal': 'Стоимость всех товаров в заказе в валюте покупателя',
            'buyerItemsTotalBeforeDiscount': 'Стоимость всех товаров в заказе в валюте покупателя',
            'buyerTotalBeforeDiscount': 'Стоимость всех товаров в заказе в валюте покупателя',
            'paymentType': 'Тип оплаты заказа',
            'paymentMethod': 'Способ оплаты заказа',
            '_offerName': 'Название товара',
            '_buyerPrice': 'Цена товара в валюте покупателя. В цене уже учтены скидки по: (акциям; купонам; промокодам',
            '_buyerPriceBeforeDiscount': 'Стоимость товара в валюте покупателя до применения скидок',
            '_count': 'Количество товара',
            '_shopSku': 'Ваш SKU',
            '_subsidy': 'Общее вознаграждение партнеру от Маркета за все акции Маркета, в которых участвует товар',
            'delivery.dates.fromDate': 'Ближайшая дата доставки',
            'delivery.shipments': 'День, в который нужно отгрузить заказы службе доставки',
            'subsidies': 'Размер субсидии',
        },
        inplace=True
    )
    print('\nDataFrame:')
    print(df_new.head())

    # Удаляю отмененные заказы
    df_new = df_new.loc[df['status'] !=
                        '=CONCATENATE("CANCELLED";CHAR(10);"(Заказ отменен)")']
    # Удаляю SHIPPED (Заказ передан службе доставки)
    df_new = df_new.loc[df['substatus'] !=
                        '=CONCATENATE("SHIPPED"; CHAR(10); "(Заказ передан службе доставки)")']

    SKUArr = list(df_new.iloc[:, 5])
    print(len(SKUArr))

    # pushToGSImages.append('=IMAGE("https://avatars.mds.yandex.net/get-mpic/4785755/img_id3585165248317282340.jpeg/orig";4;100;100)')

    # for sku in SKUArr:
    #     # print('======================Ищу это: ', sku)
    #     for goods in range(len(gooooooods.get('offerMappingEntries'))):
    #         if sku == gooooooods.get('offerMappingEntries')[goods].get('offer').get('shopSku'):
    #             if gooooooods.get('offerMappingEntries')[goods].get('offer').get('pictures'):
    #                 pushToGSImages.append('=IMAGE("' + str(gooooooods.get('offerMappingEntries')[goods].get('offer').get('pictures')[0]) + '";4;100;100)')
    #             else:
    #                 pushToGSImages.append('')
    #         # pushToGSImages.append('')
    #     print('======================Ищу это: ', pushToGSImages)
    pushToGSImages = []
    for i in range(2, len(SKUArr)+2):
        # pushToGSImages.append(
        #     f"=IMAGE(VLOOKUP(F{i};'SKU от Виталия'!A:F;6;0);4;80;80)")
        pushToGSImages.append(f"=if(VLOOKUP(F{i};" + "'" + "SKU от Виталия" + "'" +
                              f'!A:F;6;0)="";CONCATENATE("😨";CHAR(10);"Картинки нет");IMAGE(VLOOKUP(F{i};' + "'" + "SKU от Виталия" + "'" + "!A:F;6;0);4;80;80))")
    df_new["Картинка"] = pushToGSImages

    pushToGSGroup = []
    for i in range(2, len(SKUArr)+2):
        pushToGSGroup.append(
            f"=VLOOKUP(F{i};'SKU от Виталия'!A:B;2;0)")
    df_new["Группа"] = pushToGSGroup

    # # Меняем колонки местами
    # df_new = pd.DataFrame(
    #     df_new,
    #     columns=[
    #         'Идентификатор заказа',
    #         'Статус заказа',
    #         'Этап обработки заказа',
    #         'Группа',
    #         'Название товара',
    #         'Количество товара',
    #         'Ваш SKU',
    #         'День, в который нужно отгрузить заказы службе доставки',
    #         'Картинка'
    #     ]
    # )

    print(df_new.head())

    # Заливаем DataFrame в гугл таблицу
    set_with_dataframe(worksheet, df_new)
    time.sleep(3)
# =================================================================================
    # Закрепляем первую строку
    set_frozen(worksheet, rows=1)

    set_row_height(worksheet, '1', 72)
    set_row_height(worksheet, '2:1000', 80)

    formatBottomWrapLeft = gsf.cellFormat(
        wrapStrategy='WRAP',
        verticalAlignment='MIDDLE',
        horizontalAlignment='LEFT'
    )
    format_cell_range(worksheet, 'D2:D', formatBottomWrapLeft)

    formatCenter = gsf.cellFormat(
        wrapStrategy='WRAP',
        verticalAlignment='MIDDLE',
        horizontalAlignment='CENTER'
    )
    format_cell_range(worksheet, 'A2:A', formatCenter)
    format_cell_range(worksheet, 'B2:B', formatCenter)
    format_cell_range(worksheet, 'C2:C', formatCenter)
    format_cell_range(worksheet, 'E2:E', formatCenter)
    format_cell_range(worksheet, 'F2:F', formatCenter)
    format_cell_range(worksheet, 'G2:G', formatCenter)
    format_cell_range(worksheet, 'H2:H', formatCenter)
    format_cell_range(worksheet, 'I2:I', formatCenter)

    # Переменная со стилями для строки заголовков
    fmt = gsf.cellFormat(
        backgroundColor=gsf.color(211/255, 211/255, 211/255),
        textFormat=gsf.textFormat(
            bold=True, foregroundColor=gsf.color(0, 0, 0)),
        horizontalAlignment='CENTER',
        verticalAlignment='MIDDLE',
        wrapStrategy='WRAP'
    )
    format_cell_range(worksheet, '1', fmt)

    body = {
        'requests':
            [
                # Идентификатор заказа
                {
                    "updateDimensionProperties": {
                        "range": {
                            "sheetId": campaingId[0],
                            "dimension": "COLUMNS",  # COLUMNS - потому что столбец
                            "startIndex": 0,         # Столбцы нумеруются с нуля
                            "endIndex": 1            # startIndex берётся включительно, endIndex - НЕ включительно,
                        },
                        "properties": {
                            "pixelSize": 140     # размер в пикселях
                        },
                        # нужно задать только pixelSize и не трогать другие параметры столбца
                        "fields": "pixelSize"
                    },
                },
                # Статус заказа	- Этап обработки заказа
                {
                    "updateDimensionProperties": {
                        "range": {
                            "sheetId": campaingId[0],
                            "dimension": "COLUMNS",  # COLUMNS - потому что столбец
                            "startIndex": 1,         # Столбцы нумеруются с нуля
                            "endIndex": 3            # startIndex берётся включительно, endIndex - НЕ включительно,
                        },
                        "properties": {
                            "pixelSize": 120     # размер в пикселях
                        },
                        # нужно задать только pixelSize и не трогать другие параметры столбца
                        "fields": "pixelSize"
                    },
                },
                # Название товара
                {
                    "updateDimensionProperties": {
                        "range": {
                            "sheetId": campaingId[0],
                            "dimension": "COLUMNS",  # COLUMNS - потому что столбец
                            "startIndex": 3,         # Столбцы нумеруются с нуля
                            "endIndex": 4            # startIndex берётся включительно, endIndex - НЕ включительно,
                        },
                        "properties": {
                            "pixelSize": 300     # размер в пикселях
                        },
                        # нужно задать только pixelSize и не трогать другие параметры столбца
                        "fields": "pixelSize"
                    },
                },
                # Количество товара
                {
                    "updateDimensionProperties": {
                        "range": {
                            "sheetId": campaingId[0],
                            "dimension": "COLUMNS",  # COLUMNS - потому что столбец
                            "startIndex": 4,         # Столбцы нумеруются с нуля
                            "endIndex": 5            # startIndex берётся включительно, endIndex - НЕ включительно,
                        },
                        "properties": {
                            "pixelSize": 110     # размер в пикселях
                        },
                        # нужно задать только pixelSize и не трогать другие параметры столбца
                        "fields": "pixelSize"
                    },
                },
                # Ваш SKU
                {
                    "updateDimensionProperties": {
                        "range": {
                            "sheetId": campaingId[0],
                            "dimension": "COLUMNS",  # COLUMNS - потому что столбец
                            "startIndex": 5,         # Столбцы нумеруются с нуля
                            "endIndex": 6            # startIndex берётся включительно, endIndex - НЕ включительно,
                        },
                        "properties": {
                            "pixelSize": 200     # размер в пикселях
                        },
                        # нужно задать только pixelSize и не трогать другие параметры столбца
                        "fields": "pixelSize"
                    },
                },
                # День, в который нужно отгрузить заказы службе доставки
                {
                    "updateDimensionProperties": {
                        "range": {
                            "sheetId": campaingId[0],
                            "dimension": "COLUMNS",  # COLUMNS - потому что столбец
                            "startIndex": 6,         # Столбцы нумеруются с нуля
                            "endIndex": 7            # startIndex берётся включительно, endIndex - НЕ включительно,
                        },
                        "properties": {
                            "pixelSize": 160     # размер в пикселях
                        },
                        # нужно задать только pixelSize и не трогать другие параметры столбца
                        "fields": "pixelSize"
                    },
                },
                # Картинка - Группа
                {
                    "updateDimensionProperties": {
                        "range": {
                            "sheetId": campaingId[0],
                            "dimension": "COLUMNS",  # COLUMNS - потому что столбец
                            "startIndex": 7,         # Столбцы нумеруются с нуля
                            "endIndex": 9            # startIndex берётся включительно, endIndex - НЕ включительно,
                        },
                        "properties": {
                            "pixelSize": 95     # размер в пикселях
                        },
                        # нужно задать только pixelSize и не трогать другие параметры столбца
                        "fields": "pixelSize"
                    },
                }
            ]

    }

    sh.batch_update(body)

    requests1 = []
