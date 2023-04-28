import requests
import time
from datetime import datetime

today = datetime.now()

day = f'{today.day:02}'
month = f'{today.month:02}'
year = today.year
date_today = f'{day}-{month}-{year}'

valuesGroup = ['🛴Запчасти', 'компы', 'аывыавы', 'ываыывава', 'ывасываы']
valuesName = ['колесо', 'принтер', 'ноутбук', 'монитор', 'мышь']
valuesSeller = ['Петя', 'Петя', 'Вася', 'Коля', 'Вася']
valuesCount = ['2', '3', '4', '54', '23']

allOrders = list(zip(valuesGroup, valuesName, valuesSeller,
                 valuesCount))

arrSellers = set(valuesSeller[1:])

total = {}


for seller in arrSellers:
    total[seller] = []
    for order in allOrders:
        if order[2] == seller and order[0] != '🛴Запчасти':
            total[seller].append((order[1], order[3]))

# print(total)
TOKEN = "6157124843:AAGf3oET2gja01Vgxg9n7n6a6UxR1SUAK4M"
chat_id = "-933813412"


message = '🔔 СПИСОК ЗАКАЗОВ НА:\n' + str(date_today)
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
