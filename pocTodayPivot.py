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
# Указываем путь к JSON
gc = gspread.service_account(filename='keys/mypython-374908-4480952f882c.json')


# Открываем таблицу
sh = gc.open_by_url(
    'https://docs.google.com/spreadsheets/d/1Vx9RkLzxtsncULEkd7XsHQgVrcS-dzQSdocZjLp8Uw0/edit#gid=0')
# Лист, в который вставляем
worksheetget = sh.worksheet('poc-today').get_all_records()
df_sheet_sku_data_base = pd.DataFrame.from_dict(worksheetget)

print("\nТАБЛИЦА СО SKU ИЗ ГУГЛА")
# print(df_sheet_sku_data_base.head())

# Перевожу таблицу экспорта из яндекса в DataFrame для сводной таблицы
df = df_sheet_sku_data_base

df_pivot = df.pivot_table(
    values=["Количество товара"],
    index=['Группа', 'Ваш SKU', 'Название товара'],
    aggfunc=np.sum
).reset_index()

print("СВОДНАЯ ТАБЛИЦА ИТОГОВ ДЛЯ PDF")
print(df_pivot.head(100))

SKUArr = list(df_pivot.iloc[:, 2])
print(len(SKUArr))

imageArr = []
for i in range(2, len(SKUArr)+2):
    imageArr.append(f"=if(VLOOKUP(D{i};" + "'" + "SKU от Виталия" + "'" +
                    f'!A:F;6;0)="";CONCATENATE("😨";CHAR(10);"Картинки нет");IMAGE(VLOOKUP(D{i};' + "'" + "SKU от Виталия" + "'" + "!A:F;6;0);4;80;80))")
df_pivot["Картинка"] = imageArr


df_pivot["Заказал"] = ["FALSE" for i in range(2, len(SKUArr)+2)]
df_pivot["Оплатил"] = ["FALSE" for i in range(2, len(SKUArr)+2)]
df_pivot["Забрал"] = ["FALSE" for i in range(2, len(SKUArr)+2)]
df_pivot["Поставщик"] = ["-" for i in range(2, len(SKUArr)+2)]


# Меняем колонки местами
df_pivot = pd.DataFrame(
    df_pivot,
    columns=[
        'Группа',
        'Картинка',
        'Название товара',
        'Ваш SKU',
        'Количество товара',
        'Заказал',
        'Оплатил',
        'Забрал',
        'Поставщик'
    ]
)

worksheetpush = sh.worksheet('poc-today-pivot')

# Очистить лист
sh.values_clear('poc-today-pivot!A1:E')
sh.values_clear('poc-today-pivot!I1:I')

# Заливаем DataFrame в гугл таблицу
set_with_dataframe(worksheetpush, df_pivot)

# Закрепляем первую строку
set_frozen(worksheetpush, rows=1)

set_row_height(worksheetpush, '1', 72)
set_row_height(worksheetpush, '2:1000', 80)

formatBottomWrapLeft = gsf.cellFormat(
    wrapStrategy='WRAP',
    verticalAlignment='MIDDLE',
    horizontalAlignment='LEFT'
)
format_cell_range(worksheetpush, 'C2:C', formatBottomWrapLeft)

formatCenter = gsf.cellFormat(
    wrapStrategy='WRAP',
    verticalAlignment='MIDDLE',
    horizontalAlignment='CENTER'
)
format_cell_range(worksheetpush, 'A2:A', formatCenter)
format_cell_range(worksheetpush, 'B2:B', formatCenter)
format_cell_range(worksheetpush, 'D2:D', formatCenter)
format_cell_range(worksheetpush, 'E2:E', formatCenter)
format_cell_range(worksheetpush, 'F2:F', formatCenter)
format_cell_range(worksheetpush, 'G2:G', formatCenter)
format_cell_range(worksheetpush, 'H2:H', formatCenter)
format_cell_range(worksheetpush, 'I2:I', formatCenter)

# Переменная со стилями для строки заголовков
fmt = gsf.cellFormat(
    backgroundColor=gsf.color(211/255, 211/255, 211/255),
    textFormat=gsf.textFormat(
        bold=True, foregroundColor=gsf.color(0, 0, 0)),
    horizontalAlignment='CENTER',
    verticalAlignment='MIDDLE',
    wrapStrategy='WRAP'
)
format_cell_range(worksheetpush, '1', fmt)

sheetId_poc_today_pivot = 953887231

body = {
    'requests':
        [
            # Группа
            {
                "updateDimensionProperties": {
                    "range": {
                        "sheetId": sheetId_poc_today_pivot,
                        "dimension": "COLUMNS",  # COLUMNS - потому что столбец
                        "startIndex": 0,         # Столбцы нумеруются с нуля
                        "endIndex": 2            # startIndex берётся включительно, endIndex - НЕ включительно,
                    },
                    "properties": {
                        "pixelSize": 95     # размер в пикселях
                    },
                    # нужно задать только pixelSize и не трогать другие параметры столбца
                    "fields": "pixelSize"
                },
            },
            # Название товара
            {
                "updateDimensionProperties": {
                    "range": {
                        "sheetId": sheetId_poc_today_pivot,
                        "dimension": "COLUMNS",  # COLUMNS - потому что столбец
                        "startIndex": 2,         # Столбцы нумеруются с нуля
                        "endIndex": 3            # startIndex берётся включительно, endIndex - НЕ включительно,
                    },
                    "properties": {
                        "pixelSize": 300     # размер в пикселях
                    },
                    # нужно задать только pixelSize и не трогать другие параметры столбца
                    "fields": "pixelSize"
                },
            },
            # Ваш SKU
            {
                "updateDimensionProperties": {
                    "range": {
                        "sheetId": sheetId_poc_today_pivot,
                        "dimension": "COLUMNS",  # COLUMNS - потому что столбец
                        "startIndex": 3,         # Столбцы нумеруются с нуля
                        "endIndex": 4            # startIndex берётся включительно, endIndex - НЕ включительно,
                    },
                    "properties": {
                        "pixelSize": 200     # размер в пикселях
                    },
                    # нужно задать только pixelSize и не трогать другие параметры столбца
                    "fields": "pixelSize"
                },
            },
            # Количество товара
            {
                "updateDimensionProperties": {
                    "range": {
                        "sheetId": sheetId_poc_today_pivot,
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
            # Заказал - Оплатил - Забрал
            {
                "updateDimensionProperties": {
                    "range": {
                        "sheetId": sheetId_poc_today_pivot,
                        "dimension": "COLUMNS",  # COLUMNS - потому что столбец
                        "startIndex": 5,         # Столбцы нумеруются с нуля
                        "endIndex": 8            # startIndex берётся включительно, endIndex - НЕ включительно,
                    },
                    "properties": {
                        "pixelSize": 85     # размер в пикселях
                    },
                    # нужно задать только pixelSize и не трогать другие параметры столбца
                    "fields": "pixelSize"
                },
            },
            # Поставщик
            {
                "updateDimensionProperties": {
                    "range": {
                        "sheetId": sheetId_poc_today_pivot,
                        "dimension": "COLUMNS",  # COLUMNS - потому что столбец
                        "startIndex": 8,         # Столбцы нумеруются с нуля
                        "endIndex": 9            # startIndex берётся включительно, endIndex - НЕ включительно,
                    },
                    "properties": {
                        "pixelSize": 150     # размер в пикселях
                    },
                    # нужно задать только pixelSize и не трогать другие параметры столбца
                    "fields": "pixelSize"
                },
            }
        ]

}

sh.batch_update(body)

requests1 = []
