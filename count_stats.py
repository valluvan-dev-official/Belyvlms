import json

try:
    with open('locations/countries+states+cities.json', 'r', encoding='utf-8') as f:
        data = json.load(f)

    countries = len(data)
    states = sum(len(c.get('states', [])) for c in data)
    cities = sum(len(s.get('cities', [])) for c in data for s in c.get('states', []))

    print(f"JSON_COUNTS|{countries}|{states}|{cities}")
except Exception as e:
    print(e)
