# from flask import Flask, render_template, jsonify
# from pprint import pprint
# import requests
# import json
# import pandas as pd
# from gspread_dataframe import set_with_dataframe
# from flatten_json import flatten
# import gspread

# HEADERS = {
#     'Authorization': 'OAuth oauth_token="y0_AgAAAAAAlTLmAAj-3QAAAADZpmoQo0WqUwgUSnWwJkaEP7ujtPs0ufk", oauth_client_id="e765efd50206404b83e442e5f3a41fc6"',
#     'Content-Type': 'application/json'
#     }      

# response = requests.get('https://api.partner.market.yandex.ru/v2/campaigns/49039988/orders.json?page=1', headers=HEADERS).json()


# print("Всего заказов: ", response['pager']['total'])
# print("Всего страниц: ", response['pager']['pagesCount'])
# pagesCount = response['pager']['pagesCount']

# all_data = response['orders']

# if pagesCount > 1:
#     for i in range(2, pagesCount+1):
#         response = requests.get('https://api.partner.market.yandex.ru/v2/campaigns/49039988/orders.json?page=' + str(i), headers=HEADERS).json()
#         all_data = all_data + response['orders']



# # with open('responsePM.json',encoding='utf-8') as f:
# #     d = json.load(f)

# # d = three

# # data = d
# # data = d['orders']
# data = all_data
# dict_flattened = (flatten(record, '.') for record in data)
# df = pd.DataFrame(dict_flattened)
# print(df.head())



# # Указываем путь к JSON
# gc = gspread.service_account(filename='mypython-374908-4480952f882c.json')

# # Или, если вам лень извлекать этот ключ, вставьте url всей электронной таблицы
# sh = gc.open_by_url('https://docs.google.com/spreadsheets/d/1Vx9RkLzxtsncULEkd7XsHQgVrcS-dzQSdocZjLp8Uw0/edit#gid=0')

# #Открываем тестовую таблицу
# # sh = gc.open("YA | Заказы")

# worksheet = sh.worksheet("Заказы")

# #Выводим значение ячейки A1
# print(worksheet.get('A1'))
# set_with_dataframe(worksheet, df)
# # worksheet.update_cell(1, 2, 'Свекла')


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

print('asdasd')

# Указываем путь к JSON
gc = gspread.service_account(filename='mypython-374908-4480952f882c.json')
campaignIdArray = [49039988, 48371734, 48429880, 46655497]
HEADERS = {
    'Authorization': 'OAuth oauth_token="y0_AgAAAAAAlTLmAAj-3QAAAADZpmoQo0WqUwgUSnWwJkaEP7ujtPs0ufk", oauth_client_id="e765efd50206404b83e442e5f3a41fc6"',
    'Content-Type': 'application/json'
}      

# Получаю первый лист из которого вытяну сколько всего страниц и 1-50 заказы
response = requests.get('https://api.partner.market.yandex.ru/v2/campaigns/48371734/orders.json?page=1', headers=HEADERS).json()

print("Всего заказов: ", response['pager']['total'])
print("Всего страниц: ", response['pager']['pagesCount'])
pagesCount = response['pager']['pagesCount']
all_data = response['orders']

# if pagesCount > 1:
#     for i in range(2, pagesCount+1):
#         response = requests.get('https://api.partner.market.yandex.ru/v2/campaigns/49039988/orders.json?page=' + str(i), headers=HEADERS).json()
#         all_data = all_data + response['orders']

data = all_data

df = pd.json_normalize(
        data, 
        max_level=3,
        record_path=['items'],
        meta=[
            'id',
            'creationDate',
            'status',
            'paymentType',
            'substatus'
        ],
        record_prefix='_',
        errors='ignore'
)

# Это сглаживает все
# dict_flattened = (flatten(record, '.') for record in data)
# df = pd.DataFrame(dict_flattened)

print(df.head(30))
df.drop(
        columns = [
            '_vat',
            '_partnerWarehouseId',
            '_promos',
            '_buyerPrice',
            '_buyerPriceBeforeDiscount',
            '_offerId',
            '_instances',
            '_subsidy',
            '_feedCategoryId',
            '_feedId',
            '_id'
        ],
        axis = 1, 
        inplace=True
)

# Открываем таблицу
sh = gc.open_by_url('https://docs.google.com/spreadsheets/d/1Vx9RkLzxtsncULEkd7XsHQgVrcS-dzQSdocZjLp8Uw0/edit#gid=0')

# Очистить лист
sh.values_clear("'49039988'!A1:Z")

# Лист, в который вставляем
worksheet = sh.worksheet("49039988")
# Меняем колонки местами
df_new = pd.DataFrame(
    df, 
    columns=[
        'id', 
        'creationDate', 
        '_shopSku',
        '_offerName',
        '_count',
        '_price',
        'status',
        'substatus',
        'paymentType'
    ]
)
# Переводим заголовки на русский
df_new.rename(
    columns = {
        'id':'Идентификатор заказа', 
        'creationDate':'Дата и время оформления заказа',
        '_shopSku':'Ваш SKU',
        '_offerName':'Название товара',
        '_count':'Количество товара',
        '_price':'Цена товара',
        'status':'Статус заказа',
        'substatus':'Этап обработки заказа',
        'paymentType':'Тип оплаты заказа',
        }, 
    inplace = True 
)
# Заливаем DataFrame в гугл таблицу
set_with_dataframe(worksheet, df_new)
# Закрепляем первую строку
set_frozen(worksheet, rows=1)

# set_row_height(worksheet, '1', 40)
# set_row_height(worksheet, '2:1000', 22)

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
        backgroundColor=gsf.color(211/255, 211/255, 211/255),
        wrapStrategy='WRAP'
)
format_cell_range(worksheet, 'D', fmt2)

# Авторесайз строк и столбцов
requests = []
requests.append({
      "autoResizeDimensions": {
        "dimensions": {
          "sheetId": 263414250,
          "dimension": "ROWS",
        }
      }
    })

# requests.append({
#       "autoResizeDimensions": {
#         "dimensions": {
#           "sheetId": 263414250,
#           "dimension": "COLUMNS",
#         }
#       }
#     })

body = {
    'requests': requests
}

sh.batch_update(body)

# Ширина столбцов
set_column_width(worksheet, 'A', 120) # Идентификатор заказа
# set_column_width(worksheet, 'B', 140) # Дата и время оформления заказа
# set_column_width(worksheet, 'C', 140) # Ваш SKU
set_column_width(worksheet, 'D', 310) # Название товара
set_column_width(worksheet, 'E', 90) # Количество товара
set_column_width(worksheet, 'F', 60) # Цена товара
set_column_width(worksheet, 'G', 90) # Статус заказа



# =================================================
# 48371734
# response = requests.get('https://api.partner.market.yandex.ru/v2/campaigns/48371734/orders.json?page=1', headers=HEADERS).json()

# print("Всего заказов: ", response['pager']['total'])
# print("Всего страниц: ", response['pager']['pagesCount'])
# pagesCount = response['pager']['pagesCount']
# all_data = response['orders']

# if pagesCount > 1:
#     for i in range(2, pagesCount+1):
#         response = requests.get('https://api.partner.market.yandex.ru/v2/campaigns/48371734/orders.json?page=' + str(i), headers=HEADERS).json()
#         all_data = all_data + response['orders']

# data = all_data
# dict_flattened = (flatten(record, '.') for record in data)
# df = pd.DataFrame(dict_flattened)
# print(df.head())

# sh = gc.open_by_url('https://docs.google.com/spreadsheets/d/1Vx9RkLzxtsncULEkd7XsHQgVrcS-dzQSdocZjLp8Uw0/edit#gid=0')
# worksheet = sh.worksheet("48371734")
# set_with_dataframe(worksheet, df)
