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

today = datetime.now()

day = f'{today.day:02}'
month = f'{today.month:02}'
year = today.year
date_today = f'{day}-{month}-{year}'

campaignIdArray = [
    # [263414250, '49039988', 'CWC'],
    # [1481585305, '48429880', 'LESH'],
    # [2138399644, '46655497', 'Int'],
    [1157524177, '52087697', 'poc-today-pivot']
]

# Указываем путь к JSON
gc = gspread.service_account(filename='keys/mypython-374908-4480952f882c.json')

# Открываем таблицу
sh = gc.open_by_url(
    'https://docs.google.com/spreadsheets/d/1Vx9RkLzxtsncULEkd7XsHQgVrcS-dzQSdocZjLp8Uw0/edit#gid=0')

worksheet2 = sh.worksheet('poc-today-pivot')

valuesGroup = worksheet2.col_values(1)
valuesName = worksheet2.col_values(2)
valuesSeller = worksheet2.col_values(9)
valuesCount = worksheet2.col_values(11)

allOrders = list(zip(valuesGroup, valuesName, valuesSeller,
                 valuesCount))

allOrders = list(zip(valuesGroup, valuesName, valuesSeller,
                 valuesCount))

arrSellers = set(valuesSeller[1:])

total = {}


for seller in arrSellers:
    total[seller] = []
    for order in allOrders:
        if order[2] == seller and order[0] != '🛴Запчасти':
            total[seller].append((order[1], order[3]))

print(total)

# message = '🛒 Список закупок на сегодня'


TOKEN = "6157124843:AAGf3oET2gja01Vgxg9n7n6a6UxR1SUAK4M"
chat_id = "-933813412"


message = '🔔 Список закупок на сегодня:\n' + '🛒 ' + str(date_today)
url = f"https://api.telegram.org/bot{TOKEN}/sendMessage?chat_id={chat_id}&text={message}"
print(requests.get(url).json())

message = ''

for t in total:
    message += '♻️ Продавец: ' + t

    for index, i in enumerate(total.get(t)):

        if len(message) < 2000:
            message += '\n' + str(index+1) + ') ' + \
                i[0] + ' (' + i[1] + ' шт.)'
        else:
            url = f"https://api.telegram.org/bot{TOKEN}/sendMessage?chat_id={chat_id}&text={message}"
            print(requests.get(url).json())
            message = '⚠️ ПРОДОЛЖЕНИЕ ПРЕДЫДУЩЕГО ПОСТАВЩИКА' + '\n\n' + str(index+1) + ') ' + \
                i[0] + ' (' + i[1] + ' шт.)'

    # print(message)
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage?chat_id={chat_id}&text={message}"
    print(requests.get(url).json())
    time.sleep(1*.8)
    message = ''

# message1 = 'ПРОДОЛЖЕНИЕ'
# message2 = 'ПРОДОЛЖЕНИЕ'

# TOKEN = "6157124843:AAGf3oET2gja01Vgxg9n7n6a6UxR1SUAK4M"
# chat_id = "-933813412"

# for t in total:
#     for index, i in enumerate(total.get(t)):
#         print(str(index+1) + ') ' + i[0] + ' (' + i[1] + ' шт.)')

    # # print('\nПродавец: ' + t)
    # if len(message) < 2000:

    #     message = message + '\n\n♻️ Продавец: ' + t + '\n' + \
    #         '\n'.join(
    #             [str(index+1) + ') ' + j[0] + ' (' + j[1] + ' шт.)' for index, j in enumerate([i for i in total.get(t)])])
    # else:
    #     message2 = message2 + '\n\n♻️ Продавец: ' + t + '\n' + \
    #         '\n'.join(
    #             [str(index+1) + ') ' + j[0] + ' (' + j[1] + ' шт.)' for index, j in enumerate([i for i in total.get(t)])])


# print(message)
# TOKEN = "6157124843:AAGf3oET2gja01Vgxg9n7n6a6UxR1SUAK4M"
# chat_id = "-933813412"


# if len(message) > 2000:
#     url = f"https://api.telegram.org/bot{TOKEN}/sendMessage?chat_id={chat_id}&text={message[:message.find('30) ')]}"
#     # Эта строка отсылает сообщение
#     print('message11 - ', requests.get(url).json())

#     url = f"https://api.telegram.org/bot{TOKEN}/sendMessage?chat_id={chat_id}&text={message[message.find('30) '):]}"
#     # Эта строка отсылает сообщение
#     print('message12 - ', requests.get(url).json())
# else:
#     url = f"https://api.telegram.org/bot{TOKEN}/sendMessage?chat_id={chat_id}&text={message}"
#     # Эта строка отсылает сообщение
#     print('message1 - ', requests.get(url).json())


# if message2:
#     url = f"https://api.telegram.org/bot{TOKEN}/sendMessage?chat_id={chat_id}&text={message2}"
#     # Эта строка отсылает сообщение
#     print('message2 - ', requests.get(url).json())
