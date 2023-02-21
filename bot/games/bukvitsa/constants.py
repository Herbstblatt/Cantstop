import json

LETTER_PROBABILITY_DISTRIBUTION = {
    'а': 10,
    'б': 4,
    'в': 7,
    'г': 4,
    'д': 6,
    'е': 10,
    'ё': 2,
    'ж': 3,
    'з': 4,
    'и': 9,
    'й': 2,
    'к': 7,
    'л': 7,
    'м': 7,
    'н': 8,
    'о': 10,
    'п': 7,
    'р': 8,
    'с': 8,
    'т': 8,
    'у': 5,
    'ф': 3,
    'х': 2,
    'ц': 1,
    'ч': 4,
    'ш': 3,
    'щ': 2,
    'ъ': 1,
    'ы': 2,
    'ь': 3,
    'э': 3,
    'ю': 2,
    'я': 4
}

with open('bot/games/bukvitsa/dictionary.json') as r:
    DICTIONARY = set(json.load(r))
