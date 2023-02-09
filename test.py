need = [
    'b',
    'c',
    'd',

]

needDrop = [
    'a',
    'b',
]

result = list(set(need) & set(needDrop))
print(result)
