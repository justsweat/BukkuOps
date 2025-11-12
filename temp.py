import json
# ! Not in batch file

with open("product_groups.json", "r", encoding="utf-8") as f:
    f = json.load(f)

items = f["product_groups"]["items"]
for item in items:
    print(f'{item["name"]}: {item["id"]}')
