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
from googleapiclient import discovery
import time
from keys.keys import oauth_token, oauth_client_id

# Указываем путь к JSON
gc = gspread.service_account(filename='keys/mypython-374908-4480952f882c.json')

campaignIdArray = ['49039988', '48371734', '48429880', '46655497']

HEADERS = {
    'Authorization': f'OAuth oauth_token="{oauth_token}", oauth_client_id="{oauth_client_id}"',
    'Content-Type': 'application/json'
}

gidListArray = [339962401, 339962401, 1481585305, 2138399644]

campaignIdArray = [
    [263414250, '49039988'],
    # [339962401, '48371734'],
    # [1481585305, '48429880'],
    # [2138399644, '46655497']
]

for campaingId in campaignIdArray:

    print(campaingId[0])
    print(campaingId[1])


    # Получаю первый лист из которого вытяну сколько всего страниц и 1-50 заказы
    response1 = requests.get(
            'https://api.partner.market.yandex.ru/v2/campaigns/' + str(campaingId[1]) + '/orders.json?page=1',
            headers=HEADERS
    ).json()

    print("Всего заказов: ", response1['pager']['total'])
    print("Всего страниц: ", response1['pager']['pagesCount'])
    pagesCount = response1['pager']['pagesCount']
    all_data = response1['orders']

    # Тут цикл в котором я забираю вообще все заказы с маркета

    # if pagesCount > 1:
    #     for i in range(2, pagesCount+1):
    #         response = requests.get(
    #             'https://api.partner.market.yandex.ru/v2/campaigns/' + campaingId[1] + '/orders.json?page' + str(i),
    #             headers=HEADERS
    #         ).json()
    #         all_data = all_data + response['orders']
    data = all_data

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

    # qwer = str(df.at[3, 'delivery.shipments'])
    # s = qwer.replace("\'", "\"")
    # data_qwer = json.loads(s)
    # print(data_qwer['shipmentDate'])
    # df.at[3, 'delivery.shipments'] = data_qwer['shipmentDate']

    # df['id'] = df['id'].astype( str )

    df.fillna(0)

    def eerrrr(q):
        w = str(q)
        print (w)
        rgfd = w.replace("\'", "\"")
        print (rgfd)
        data_qwer = json.loads(rgfd)
        date_sh = data_qwer['shipmentDate']
        sdjkh = date_sh.replace("-", ".")
        print("вылдфовоылодлвфыодлоывлдофывлдодлвы   ",sdjkh)
        return sdjkh
    
    def eerrrr2(q):
        print(type(q))
        if pd.isna(q):
            print('dlksajdl;hjlkjdfhlksadhflkjhgdslkjfhlkjsdgalkfjglsdjkhfljhk')
            return ''
        else:
            w = str(q)
            print('dlksajdl;hjlkjdfhlksadhflkjhgdslkjfhlkjsdgalkfjglsdjkhfljhk',w)
            print (w)
            rgfd = w.replace("\'", "\"")
            qweweqwe =  rgfd.replace("[", "")
            asfasfsfafaf = qweweqwe.replace("]", "")
            print (asfasfsfafaf)
            data_qwer2 = json.loads(asfasfsfafaf)
            date_sh = data_qwer2['amount']
            print("вылдфовоылодлвфыодлоывлдофывлдодлвы   ",date_sh)
            return date_sh

    num_rows = df.shape[0]

    for i in range(num_rows):
        df.at[i, 'delivery.shipments'] = eerrrr(df.at[i, 'delivery.shipments'])

    for i in range(num_rows):
        df.at[i, 'subsidies'] = eerrrr2(df.at[i, 'subsidies'])


    # df['id'] = df['id'].replace("id", "asdasdasda")

    # print(df.head())

    columnInData = list(df.columns.values)
    print(columnInData)
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

    result = list(set(columnInData) & set(needDrop))
    print(result)

    print(df.head())
    df.drop(
        columns = result,
        axis = 1, 
        inplace=True
    )

    # Открываем таблицу
    sh = gc.open_by_url('https://docs.google.com/spreadsheets/d/1Vx9RkLzxtsncULEkd7XsHQgVrcS-dzQSdocZjLp8Uw0/edit#gid=0')

    # Очистить лист
    sh.values_clear("'" + campaingId[1] + "'!A1:Z")

    # Лист, в который вставляем
    worksheet = sh.worksheet(campaingId[1])

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
        columns = {
            # 'id':'Идентификатор заказа', 
            # 'creationDate':'Дата и время оформления заказа',
            # '_shopSku':'Ваш SKU',
            # '_offerName':'Название товара',
            # '_count':'Количество товара',
            # '_price':'Цена товара',
            # 'status':'Статус заказа',
            # 'substatus':'Этап обработки заказа',
            # 'paymentType':'Тип оплаты заказа',


            'id':'Идентификатор заказа',
            'status':'Статус заказа',
            'substatus':'Этап обработки заказа',
            'creationDate':'Дата и время оформления заказа',
            'itemsTotal':'Стоимость всех товаров в заказе в валюте магазина',
            'total':'Стоимость всех товаров в заказе в валюте магазина',
            'deliveryTotal':'Стоимость доставки в валюте заказа',
            'subsidyTotal':'Общее вознаграждение партнеру за скидки по всем товарам в заказе',
            'totalWithSubsidy':'Сумма стоимости всех товаров в заказе и вознаграждения за них в валюте магазина (сумма параметров total и subsidyTotal)',
            'buyerItemsTotal':'Стоимость всех товаров в заказе в валюте покупателя',
            'buyerTotal':'Стоимость всех товаров в заказе в валюте покупателя',
            'buyerItemsTotalBeforeDiscount':'Стоимость всех товаров в заказе в валюте покупателя',
            'buyerTotalBeforeDiscount':'Стоимость всех товаров в заказе в валюте покупателя',
            'paymentType':'Тип оплаты заказа',
            'paymentMethod':'Способ оплаты заказа',
            '_offerName':'Название товара',
            '_buyerPrice':'Цена товара в валюте покупателя. В цене уже учтены скидки по: (акциям; купонам; промокодам',
            '_buyerPriceBeforeDiscount':'Стоимость товара в валюте покупателя до применения скидок',
            '_count':'Количество товара',
            '_shopSku':'Ваш SKU',
            '_subsidy':'Общее вознаграждение партнеру от Маркета за все акции Маркета, в которых участвует товар',
            'delivery.dates.fromDate':'Ближайшая дата доставки',
            'delivery.shipments':'День, в который нужно отгрузить заказы службе доставки',
            'subsidies':'Размер субсидии',
            }, 
        inplace = True 
    )
    # Заливаем DataFrame в гугл таблицу
    set_with_dataframe(worksheet, df_new)
    time.sleep(3)

    # Закрепляем первую строку
    set_frozen(worksheet, rows=1)

    set_row_height(worksheet, '1', 40)
    set_row_height(worksheet, '2:1000', 22)

    # Переменная со стилями для строки заголовков
    fmt = gsf.cellFormat(
            backgroundColor=gsf.color(211/255, 211/255, 211/255),
            textFormat=gsf.textFormat(bold=True, foregroundColor=gsf.color(0, 0, 0)),
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
    
    # requests1 = []
    # Ширина столбцов
    set_column_width(worksheet, 'A', 120) # Идентификатор заказа
    set_column_width(worksheet, 'B', 140) # Дата и время оформления заказа
    set_column_width(worksheet, 'C', 110) # Ваш SKU
    set_column_width(worksheet, 'D', 310) # Название товара
    set_column_width(worksheet, 'E', 90) # Количество товара
    set_column_width(worksheet, 'F', 60) # Цена товара
    set_column_width(worksheet, 'G', 90) # Статус заказа
    set_column_width(worksheet, 'H', 120) # Статус заказа
    set_column_width(worksheet, 'I', 90) # Статус заказа



    body2 = {
        'requests': {
            "autoResizeDimensions": {
                "dimensions": {
                    "sheetId": campaingId[0],
                    "dimension": "ROWS",
                }
            },
        }
    }
    sh.batch_update(body2)





