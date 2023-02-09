# body1 = [
#     { "id": 190010120},
# ]

status = {
    'CANCELLED':'Заказ отменен',
    "DELIVERED":"Заказ получен покупателем",
    "DELIVERY":"Заказ передан в службу доставки",
    "PICKUP":"Заказ доставлен в пункт самовывоза",
    "PROCESSING":" Заказ находится в обработке",
    "UNPAID":"Заказ оформлен, но еще не оплачен (если выбрана оплата при оформлении)",
}

try:
    print(status["CANCELLED"])
except:
    print("yt y")


# for i in range(2, 5):
#     print(i)

# result = body1 + body2
# print(result)
