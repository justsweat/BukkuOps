import requests
import json
import pandas as pd
from datetime import datetime
from cred import api_headers
# ! not in batch file

# API Essentials
base = "https://api.bukku.my/"
subdomain = "jlsb"

root = "C:/Apps/BukkuOps/data/"


# Essential functions
def get_response(path, params):
    url = f"{base}{path}"
    response = requests.get(url, headers=api_headers, params=params)
    response_json = response.json()
    return response_json


def post_response(path, params):
    url = f"{base}{path}"
    response = requests.post(url, headers=api_headers, json=params)
    response_json = response.json()
    return response_json


def put_response(path, params):
    url = f"{base}{path}"
    response = requests.put(url, headers=api_headers, json=params)
    response_json = response.json()
    return response_json


def delete_response(path):
    url = f"{base}{path}"
    response = requests.delete(url, headers=api_headers)
    response_json = response.json()
    return response_json


def save_file(filename, data):
    with open(f"{root}{filename}.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


def open_file(filename):
    with open(f"{root}{filename}.json", "r", encoding="utf-8") as f:
        return json.load(f)


# Get functions
def read_tlist(category):
    #! Separate from products and contacts, because using transactions
    ref = {
        "sales_orders": "sales/orders",
        "delivery_orders": "sales/delivery_orders",
        "invoices": "sales/invoices",
        "credit_notes": "sales/credit_notes",
        "purchase_orders": "purchases/orders",
        "goods_receiveds": "purchases/goods_received_notes",
        "purchase_payments": "purchases/payments",
        "purchase_bills": "purchases/bills",
        "debit_notes": "sales/invoices"
    }
    path = ref[category]
    items = {}

    # Step 1: Get total number
    params = {'page_size': 1}
    response = get_response(path, params)
    total_items = response["paging"]["total"]

    current_page = 1
    page_size = 100
    total_pages = (total_items + page_size - 1) // page_size

    # Step 2: Loop through all pages and get data
    while current_page <= total_pages:
        params = {
            "page": current_page,
            "page_size": 100,
        }
        response = get_response(path, params)
        data_list = response.get("transactions", [])

        for item in data_list:
            item_id = item["id"]
            items[item_id] = item

        current_page += 1

    print(f"Total {category}: {total_items}")
    print(f"Total pages: {total_pages}")

    print(f"Total collected: {len(items)}")
    save_file(f"{category}_bukku", items)
    print(f"Saved {category}_bukku.json")
    parse_list(category)


def read_list(category):
    ref = {
        "contacts": "contacts",
        "products": "products",
    }
    path = ref[category]
    items = {}

    # Step 1: Get total number
    params = {'page_size': 1}
    response = get_response(path, params)
    total_items = response["paging"]["total"]

    current_page = 1
    page_size = 100
    total_pages = (total_items + page_size - 1) // page_size

    # Step 2: Loop through all pages and get contacts
    while current_page <= total_pages:
        params = {
            "page": current_page,
            "page_size": 100,
        }
        response = get_response(path, params)
        data_list = response.get(category, [])

        for item in data_list:
            item_id = item["id"]
            items[item_id] = item

        current_page += 1

    print(f"Total {category}: {total_items}")
    print(f"Total pages: {total_pages}")

    print(f"Total collected: {len(items)}")
    save_file(f"{category}_bukku", items)
    print(f"Saved {category}_bukku.json")
    parse_list(category)


def parse_list(category):
    ref = {
        "contacts": "company_name",
        "products": "sku",
        "purchase_bills": "number2"
    }
    key = ref.get(category, "number")

    items = open_file(f"{category}_bukku")
    parsed = {}
    skipped_items = ['None']

    for id in items:
        item = items[id]
        code = item[key]
        id = item["id"]
        updated_on = convert_date(item["updated_at"])

        if code in skipped_items:
            continue

        parsed[code] = {"id": id, "code": code, "updated_on": updated_on}

        if category == "invoices":
            parsed[code]["cust"] = item["contact_id"]

    save_file(f"{category}_bukku_ids", parsed)
    print(f"Saved {category}_bukku_ids.json")


def parse_agent_xlsx_to_json(filename):
    df = pd.read_excel(filename, dtype=str)
    # Drop rows where all columns are blank
    df = df.dropna(how='all')
    # Replace remaining NaN values with empty string
    df = df.fillna('')

    rows = df.to_dict(orient="records")
    etins = {}
    for row in rows:
        code = row.get("Code", "").strip()

        # Skip rows with no code or marked as Pending
        if not code or row.get("Status", "").strip() == "Pending":
            continue

        etin = {
            "code": code,
            "email": row["Email"],
            "contact_number": row["Contact Number"],
            "old_roc": row["OLD Roc"],
            "new_roc": row["New Roc"],
            "tin": row["Company TIN (Tax Identification Number)"],
        }
        etins[code] = etin
    json_data = json.dumps(etins, indent=4)
    with open(f"{root}etin.json", "w") as f:
        f.write(json_data)
    print(f"Parse excel to etin.json")


def parse_xlsx_to_json(filename):
    df = pd.read_excel(filename, dtype=str)
    # Drop rows where all columns are blank
    df = df.dropna(how='all')
    # Replace remaining NaN values with empty string
    df = df.fillna('')

    rows = df.to_dict(orient="records")
    etins = {}
    for row in rows:
        code = row.get("Code", "").strip()

        # Skip rows with no code or marked as Pending
        if not code or row.get("Status", "").strip() == "Pending":
            continue

        etin = {
            "code": code,
            "email": row["Email"],
            "contact_number": row["Contact Number"],
            "old_roc": row["OLD Roc"],
            "new_roc": row["New Roc"],
            "tin": row["Company TIN (Tax Identification Number)"],
        }
        etins[code] = etin
    json_data = json.dumps(etins, indent=4)
    with open(f"{root}etin.json", "w") as f:
        f.write(json_data)
    print(f"Parse excel to etin.json")


# Helper functions
def check_doc_exists(doc_id, doc_added):
    if doc_id in doc_added:
        return True
    return False


def save_to_added_list(category_id, category):
    category_added = open_file(f"{category}_added")

    if category_id not in category_added:
        category_added.append(category_id)
        save_file(f"{category}_added", category_added)
    return


# Asoft helper functions
def convert_date(obj):  # for Bukku as well
    if not obj:
        return None
    if isinstance(obj, datetime):
        return obj.strftime("%Y-%m-%d")
    if isinstance(obj, str):
        parsed = datetime.strptime(obj, "%Y-%m-%d %H:%M:%S")
        return parsed.strftime("%Y-%m-%d")


def clean_remark(remark):
    if remark is None:
        return ''
    remark = remark.replace('\r', '')  # remove \r
    remark = remark.replace('\n', '')  # remove \n
    remark = remark.strip()
    return remark


def clean_currency_id(currency):
    replacements = {"RM": "MYR", "RMB": "CNY"}
    return replacements.get(currency, currency)


def clean_agent(sm_id):
    replacements = {
        "202": "Kong",
        "203": "Kee",
        "205": "Lim",
        "206": "Yap",
    }
    return replacements.get(sm_id, sm_id)


def clean_doc_type(type):
    replacements = {
        "U2": 1,
        "ROS": 2,
        "BAT": 3,
        "GLA": 4,
        "NTA": 5,
        "INV": 6,
        "AUR": 7,
        "SVC": 8,
        "OTH": 9,
        "ARA": 9,
    }
    return replacements.get(type, "MIS")


def clean_phone(phone_num):
    phone_num = str(phone_num).replace("-", "")
    if phone_num.startswith("0"):
        phone_num = "6" + phone_num

    if phone_num == "None":
        return ""
    return phone_num


def clean_glass_id(item):
    replacements = {
        "131801": "131800",
        "1318011": "131800",
        "1313001": "131300",
    }
    return replacements.get(item, item)


if __name__ == "__main__":
    #parse_list("delivery_orders")
    #parse_xlsx_to_json("etin.xlsx")
    read_list("contacts")
    #read_tlist("sales_orders")
