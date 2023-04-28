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
import numpy as np

import requests


campaignIdArray = [
    # [263414250, '49039988', 'CWC'],
    # [1481585305, '48429880', 'LESH'],
    # [2138399644, '46655497', 'Int'],
    [1157524177, '52087697', 'poc-today']
]

# Указываем путь к JSON
gc = gspread.service_account(filename='keys/mypython-374908-4480952f882c.json')

# Открываем таблицу
sh = gc.open_by_url(
    'https://docs.google.com/spreadsheets/d/1Vx9RkLzxtsncULEkd7XsHQgVrcS-dzQSdocZjLp8Uw0/edit#gid=0')

worksheet = sh.worksheet('poc-today')
values_list = worksheet.col_values(1)
df_sheet_sku_data_base = pd.DataFrame.from_dict(values_list)

print("\nСТОЛБЕЦ ID ИЗ poc-today")
dfSkuColumn = df_sheet_sku_data_base[1:]
arrSkuExist = list(dfSkuColumn[0])
print(arrSkuExist)

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
# print(today.weekday()+1)

# Заголовки запроса к Яндексу
HEADERS = {
    'Authorization': f'OAuth oauth_token="{oauth_token}", oauth_client_id="{oauth_client_id}"',
    'Content-Type': 'application/json'
}


# Сегодня
response1 = requests.get(
    'https://api.partner.market.yandex.ru/v2/campaigns/' + '52087697' +
    '/orders.json?page=1&supplierShipmentDateFrom=' +
    date_today + '&supplierShipmentDateTo=' + date_today,
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
            str(i) + '&supplierShipmentDateFrom=' + date_today +
            '&supplierShipmentDateTo=' + date_today,
            headers=HEADERS
        ).json()
        # print("ВОТ ЭТО ",response2)
        data = data + response2['orders']

# Если сегодня понедельник, то берем вчера и позавчера
if today.weekday()+1 == 1:
    # Вчера и позавчера в статусе PROCESSING
    response2 = requests.get(
        'https://api.partner.market.yandex.ru/v2/campaigns/' + '52087697' + '/orders.json?page=1&supplierShipmentDateFrom=' +
        date_before_yesterday + '&supplierShipmentDateTo=' +
        date_yesterday,
        headers=HEADERS
    ).json()
    print("\nВсего заказов: ", response2['pager']['total'])
    print("Всего страниц: ", response2['pager']['pagesCount'])
else:
    # Вчера в статусе PROCESSING
    response2 = requests.get(
        'https://api.partner.market.yandex.ru/v2/campaigns/' + '52087697' + '/orders.json?page=1&supplierShipmentDateFrom=' +
        date_yesterday + '&supplierShipmentDateTo=' +
        date_yesterday,
        headers=HEADERS
    ).json()
    print("\nВсего заказов: ", response2['pager']['total'])
    print("Всего страниц: ", response2['pager']['pagesCount'])

# Количество страниц в ответе
pagesCount2 = response2['pager']['pagesCount']
# Переменная в которую соберу все заказы из всех страниц
data += response2['orders']

# Тут цикл в котором я забираю вообще все заказы с маркета
if pagesCount2 > 1:

    for i in range(2, pagesCount2+1):
        # Если сегодня понедельник, то берем вчера и позавчера
        if today.weekday()+1 == 1:
            # Вчера и позавчера в статусе PROCESSING
            response2 = requests.get(
                'https://api.partner.market.yandex.ru/v2/campaigns/' + '52087697' + '/orders.json?page=' +
                str(i) + '&supplierShipmentDateFrom=' + date_before_yesterday +
                '&supplierShipmentDateTo=' + date_yesterday,
                headers=HEADERS
            ).json()
            data = data + response2['orders']
        else:
            # Вчера в статусе PROCESSING
            response2 = requests.get(
                'https://api.partner.market.yandex.ru/v2/campaigns/' + '52087697' + '/orders.json?page=' +
                str(i) + '&supplierShipmentDateFrom=' + date_yesterday +
                '&supplierShipmentDateTo=' + date_yesterday,
                headers=HEADERS
            ).json()
            data = data + response2['orders']

# ДатаФрейм
dfGetFromYandex = pd.DataFrame(
    data, columns=['id', 'status']
)

# print(list(dfGetFromYandex['id']))
# print(list(dfGetFromYandex['status']))
arrActualStatus = list(
    zip(list(dfGetFromYandex['id']), list(dfGetFromYandex['status'])))
print("\nИз яндекса")
print(arrActualStatus)


def get_indices(lst, el):
    return [i for i in range(len(lst)) if lst[i] == el]


for i in arrActualStatus:
    if str(i[0]) in arrSkuExist:
        for j in get_indices(arrSkuExist, str(i[0])):
            arrSkuExist[j] = i[1]
print("\nИзмененый существующий с гугла")
print(arrSkuExist)
arrSkuExist.insert(
    0, f'=CONCATENATE("Обновленный статус заказа";CHAR(10);"{str(today).split(".")[0]}") ')
dfActualForGS = pd.DataFrame(arrSkuExist)

print(dfActualForGS)
# Очистить лист
sh.values_clear("'" + campaignIdArray[0][2] + "'!J1:J")
set_with_dataframe(worksheet, dfActualForGS,
                   include_column_header=False, col=10, row=1)


worksheet2 = sh.worksheet('poc-today')

valuesIdOffer = worksheet2.col_values(1)
valuesNames = worksheet2.col_values(4)
valuesCount = worksheet2.col_values(5)
valuesSku = worksheet2.col_values(6)
valuesFreshStatus = worksheet2.col_values(10)

allOrders = list(zip(valuesNames, valuesCount, valuesSku,
                 valuesFreshStatus, valuesIdOffer))

ordersCancelled = []

for i in allOrders[1:]:
    if i[3] != 'PROCESSING':
        ordersCancelled.append(i)

if not ordersCancelled:
    message = "✅ Отмененных заказов сегодня нет"
else:
    message = "❌ Отмененные заказы сегодня:\n\n" + \
        '\n\n'.join([f'Номер заказа: {i[4]}' + '\n1️⃣ ' + i[3] + '\n2️⃣ ' + i[0] + '\n3️⃣ ' +
                     i[2] + '\n4️⃣ ' + i[1] + ' шт.' for i in ordersCancelled])

print(ordersCancelled)


TOKEN = "6157124843:AAGf3oET2gja01Vgxg9n7n6a6UxR1SUAK4M"
chat_id = "-933813412"
url = f"https://api.telegram.org/bot{TOKEN}/sendMessage?chat_id={chat_id}&text={message}"
print(requests.get(url).json())  # Эта строка отсылает сообщение
