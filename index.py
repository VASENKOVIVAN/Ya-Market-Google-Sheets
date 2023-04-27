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
    [355247618, '52087697', 'poc']
]

# Пробегаю по каждому магазину и листуGS
for campaingId in campaignIdArray:

    # Вывожу Лист и Кампанию
    print('= = = = = = = = = = = = = = = ')
    print('ЛистGS:', campaingId[0])
    print('СampaingId:', campaingId[1])

    # Получаю первый лист из которого вытяну сколько всего страниц и 1-50 заказы
    response1 = requests.get(
        'https://api.partner.market.yandex.ru/v2/campaigns/' +
        str(campaingId[1]) + '/orders.json?page=1',
        headers=HEADERS
    ).json()

    print("\nВсего заказов: ", response1['pager']['total'])
    print("Всего страниц: ", response1['pager']['pagesCount'])

    # Количество страниц в ответе
    pagesCount = response1['pager']['pagesCount']
    # Переменная в которую соберу все заказы из всех страниц
    data = response1['orders']

    # Тут цикл в котором я забираю вообще все заказы с маркета
    if pagesCount > 1:
        for i in range(2, pagesCount+1):
            response2 = requests.get(
                'https://api.partner.market.yandex.ru/v2/campaigns/' +
                campaingId[1] + '/orders.json?page=' + str(i),
                headers=HEADERS
            ).json()
            # print("ВОТ Э ",response2)
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
        "CANCELLED": "CANCELLED (Заказ отменен)",
        "DELIVERED": "DELIVERED (Заказ получен покупателем)",
        "DELIVERY": "DELIVERY (Заказ передан в службу доставки)",
        "PICKUP": "PICKUP (Заказ доставлен в пункт самовывоза)",
        "PROCESSING": "PROCESSING (Заказ находится в обработке)",
        "UNPAID": "UNPAID (Заказ оформлен, но еще не оплачен [если выбрана оплата при оформлении])",
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
        'STARTED': 'STARTED (Заказ подтвержден, его можно начать обрабатывать)',
        'READY_TO_SHIP': 'READY_TO_SHIP (Заказ собран и готов к отправке)',
        'SHIPPED': 'SHIPPED (Заказ передан службе доставки)',
        'DELIVERY_SERVICE_UNDELIVERED': 'DELIVERY_SERVICE_UNDELIVERED (Служба доставки не смогла доставить заказ)',
        'PROCESSING_EXPIRED': 'PROCESSING_EXPIRED (Магазин не обработал заказ в течение семи дней)',
        'REPLACING_ORDER': 'REPLACING_ORDER (Покупатель решил заменить товар другим по собственной инициативе)',
        'RESERVATION_EXPIRED': 'RESERVATION_EXPIRED (Покупатель не завершил оформление зарезервированного заказа в течение 10 минут)',
        'RESERVATION_FAILED': 'RESERVATION_FAILED (Маркет не может продолжить дальнейшую обработку заказа)',
        'SHOP_FAILED': 'SHOP_FAILED (Магазин не может выполнить заказ)',
        'USER_CHANGED_MIND': 'USER_CHANGED_MIND (Покупатель отменил заказ по личным причинам)',
        'USER_NOT_PAID': 'USER_NOT_PAID (Покупатель не оплатил заказ (для типа оплаты PREPAID) в течение 30 минут)',
        'USER_REFUSED_DELIVERY': 'USER_REFUSED_DELIVERY (Покупателя не устроили условия доставки)',
        'USER_REFUSED_PRODUCT': 'USER_REFUSED_PRODUCT (Покупателю не подошел товар)',
        'USER_REFUSED_QUALITY': 'USER_REFUSED_QUALITY (Покупателя не устроило качество товара)',
        'USER_UNREACHABLE': 'USER_UNREACHABLE (Не удалось связаться с покупателем)',
        'USER_WANTS_TO_CHANGE_DELIVERY_DATE': 'USER_WANTS_TO_CHANGE_DELIVERY_DATE (Покупатель хочет получить заказ в другой день)',
        'CANCELLED_COURIER_NOT_FOUND': 'CANCELLED_COURIER_NOT_FOUND (Не удалось найти курьера)',
    }

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
        # '_buyerPriceBeforeDiscount',
        '_offerId',
        '_instances',
        # '_subsidy',
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

    # Открываем таблицу
    sh = gc.open_by_url(
        'https://docs.google.com/spreadsheets/d/1Vx9RkLzxtsncULEkd7XsHQgVrcS-dzQSdocZjLp8Uw0/edit#gid=0')

    # Очистить лист
    sh.values_clear("'" + campaingId[2] + "'!A1:X")

    # Лист, в который вставляем
    worksheet = sh.worksheet(campaingId[2])

    # Меняем колонки местами
    df_new = df
    df_new = pd.DataFrame(
        df,
        columns=[
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
            '_offerName',
            '_buyerPrice',
            '_buyerPriceBeforeDiscount',
            '_count',
            '_shopSku',
            '_subsidy',
            'delivery.dates.fromDate',
            'delivery.shipments',
            'subsidies',
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

    # Заливаем DataFrame в гугл таблицу
    set_with_dataframe(worksheet, df_new)
    time.sleep(3)

    # Закрепляем первую строку
    set_frozen(worksheet, rows=1)

    set_row_height(worksheet, '1', 50)
    set_row_height(worksheet, '2:1000', 22)

    # Переменная со стилями для строки заголовков
    fmt = gsf.cellFormat(
        backgroundColor=gsf.color(211/255, 211/255, 211/255),
        textFormat=gsf.textFormat(
            bold=True, foregroundColor=gsf.color(0, 0, 0)),
        # textFormat=gsf.textFormat(bold=True),
        horizontalAlignment='CENTER',
        verticalAlignment='MIDDLE',
        wrapStrategy='WRAP'
    )
    format_cell_range(worksheet, '1', fmt)

    fmt2 = gsf.cellFormat(
        wrapStrategy='WRAP'
    )
    format_cell_range(worksheet, 'D', fmt2)

    # Авторесайз строк и столбцов
    # requests1 = []
    # requests1.append({
    #     "autoResizeDimensions": {
    #         "dimensions": {
    #         "sheetId": 263414250,
    #         "dimension": "ROWS",
    #         }
    #     }
    #     })

    # requests1.append({
    #     "autoResizeDimensions": {
    #         "dimensions": {
    #         "sheetId": 263414250,
    #         "dimension": "COLUMNS",
    #         }
    #     }
    #     })

    # body = {
    #     'requests': {
    #         "autoResizeDimensions": {
    #             "dimensions": {
    #                 "sheetId": campaingId[0],
    #                 "dimension": "COLUMNS",
    #             }
    #         }
    #     }
    # }

    # sh.batch_update(body)

    body = {
        'requests':
            # Задать ширину столбца A: 317 пикселей
            {
                "updateDimensionProperties": {
                    "range": {
                        "sheetId": campaingId[0],
                        "dimension": "COLUMNS",  # COLUMNS - потому что столбец
                        "startIndex": 0,         # Столбцы нумеруются с нуля
                        "endIndex": 25            # startIndex берётся включительно, endIndex - НЕ включительно,
                    },
                    "properties": {
                        "pixelSize": 120     # размер в пикселях
                    },
                    # нужно задать только pixelSize и не трогать другие параметры столбца
                    "fields": "pixelSize"
                },
            },
    }

    sh.batch_update(body)

    requests1 = []

    # Ширина столбцов
    # set_column_width(worksheet, 'A', 120) # 'id':'Идентификатор заказа',
    # set_column_width(worksheet, 'B', 120) # 'status':'Статус заказа',
    # set_column_width(worksheet, 'C', 120) # 'substatus':'Этап обработки заказа',
    # set_column_width(worksheet, 'D', 90) # 'creationDate':'Дата и время оформления заказа',
    # set_column_width(worksheet, 'E', 90) # 'itemsTotal':'Стоимость всех товаров в заказе в валюте магазина',
    # set_column_width(worksheet, 'F', 90) # 'total':'Стоимость всех товаров в заказе в валюте магазина',
    # set_column_width(worksheet, 'G', 90) # 'deliveryTotal':'Стоимость доставки в валюте заказа',
    # set_column_width(worksheet, 'H', 90) # 'subsidyTotal':'Общее вознаграждение партнеру за скидки по всем товарам в заказе',
    # set_column_width(worksheet, 'I', 90) # 'totalWithSubsidy':'Сумма стоимости всех товаров в заказе и вознаграждения за них в валюте магазина (сумма параметров total и subsidyTotal)',
    # set_column_width(worksheet, 'J', 90) # 'buyerItemsTotal':'Стоимость всех товаров в заказе в валюте покупателя',
    # set_column_width(worksheet, 'K', 90) # 'buyerTotal':'Стоимость всех товаров в заказе в валюте покупателя',
    # set_column_width(worksheet, 'L', 90) # 'buyerItemsTotalBeforeDiscount':'Стоимость всех товаров в заказе в валюте покупателя',
    # set_column_width(worksheet, 'M', 90) # 'buyerTotalBeforeDiscount':'Стоимость всех товаров в заказе в валюте покупателя',
    # set_column_width(worksheet, 'N', 90) # 'paymentType':'Тип оплаты заказа',
    # set_column_width(worksheet, 'O', 90) # 'paymentMethod':'Способ оплаты заказа',
    # set_column_width(worksheet, 'P', 90) # '_offerName':'Название товара',
    # set_column_width(worksheet, 'Q', 90) # '_buyerPrice':'Цена товара в валюте покупателя. В цене уже учтены скидки по: (акциям; купонам; промокодам',
    # set_column_width(worksheet, 'R', 90) # '_buyerPriceBeforeDiscount':'Стоимость товара в валюте покупателя до применения скидок',
    # set_column_width(worksheet, 'S', 90) # '_count':'Количество товара',
    # set_column_width(worksheet, 'T', 90) # '_shopSku':'Ваш SKU',
    # set_column_width(worksheet, 'U', 90) # '_subsidy':'Общее вознаграждение партнеру от Маркета за все акции Маркета, в которых участвует товар',
    # set_column_width(worksheet, 'V', 90) # 'delivery.dates.fromDate':'Ближайшая дата доставки',
    # set_column_width(worksheet, 'W', 90) # 'delivery.shipments':'День, в который нужно отгрузить заказы службе доставки',
    # set_column_width(worksheet, 'X', 90) # 'subsidies':'Размер субсидии',

    # body2 = {
    #     'requests': {
    #         "autoResizeDimensions": {
    #             "dimensions": {
    #                 "sheetId": campaingId[0],
    #                 "dimension": "ROWS",
    #             }
    #         },
    #     }
    # }
    # sh.batch_update(body2)

    # results = service.spreadsheets().batchUpdate(spreadsheetId = spreadsheet['spreadsheetId'], body = {
    # "requests": [

    #     # Задать ширину столбца A: 317 пикселей
    #     {
    #     "updateDimensionProperties": {
    #         "range": {
    #         "sheetId": 0,
    #         "dimension": "COLUMNS",  # COLUMNS - потому что столбец
    #         "startIndex": 0,         # Столбцы нумеруются с нуля
    #         "endIndex": 1            # startIndex берётся включительно, endIndex - НЕ включительно,
    #                                 # т.е. размер будет применён к столбцам в диапазоне [0,1), т.е. только к столбцу A
    #         },
    #         "properties": {
    #         "pixelSize": 317     # размер в пикселях
    #         },
    #         "fields": "pixelSize"  # нужно задать только pixelSize и не трогать другие параметры столбца
    #     }
    #     },

    #     # Задать ширину столбца B: 200 пикселей
    #     {
    #     "updateDimensionProperties": {
    #         "range": {
    #         "sheetId": 0,
    #         "dimension": "COLUMNS",
    #         "startIndex": 1,
    #         "endIndex": 2
    #         },
    #         "properties": {
    #         "pixelSize": 200
    #         },
    #         "fields": "pixelSize"
    #     }
    #     },

    #     # Задать ширину столбцов C и D: 165 пикселей
    #     {
    #     "updateDimensionProperties": {
    #         "range": {
    #         "sheetId": 0,
    #         "dimension": "COLUMNS",
    #         "startIndex": 2,
    #         "endIndex": 4
    #         },
    #         "properties": {
    #         "pixelSize": 165
    #         },
    #         "fields": "pixelSize"
    #     }
    #     },

    #     # Задать ширину столбца E: 100 пикселей
    #     {
    #     "updateDimensionProperties": {
    #         "range": {
    #         "sheetId": 0,
    #         "dimension": "COLUMNS",
    #         "startIndex": 4,
    #         "endIndex": 5
    #         },
    #         "properties": {
    #         "pixelSize": 100
    #         },
    #         "fields": "pixelSize"
    #     }
    #     }
    # ]
    # }).execute()
