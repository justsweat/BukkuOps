import pyodbc
import ops as o

db_server = pyodbc.connect("DSN=JunLee_Asoft")
cursor = db_server.cursor()


def get_group_ids(group, extra_groups):
    reference = {
        "Arrixon": 11,
        "Battery": 2,
        "Glass": 3,
        "Japan": 9,
        "Non-stock": 17,
        "Original": 6,
        "Other": 14,
        "Postage": 4,
        "Promo": 7,
        "Raw": 10,
        "Renata": 13,
        "Roscani": 1,
        "Spron": 8,
        "Strap": 15,
        "U2": 5,
        "Wallet": 16,
        "Aurafit": 18
    }
    group_ids = []
    if group in reference:
        group_ids.append(reference[group])

    group_ids.extend(reference[g] for g in (extra_groups or [])
                     if g in reference)

    return group_ids


def gen_battery_groups(NAME):
    if "JAPAN" in NAME:
        return ["Japan"]

    if "SPRON" in NAME:
        return ["Spron"]

    if "RAW" in NAME:
        return ["Raw"]


def gen_watch_groups(CODE, SEC_CODE, PROMO):
    groups = []
    if CODE == PROMO:
        groups.append("Promo")

    if CODE == SEC_CODE:
        groups.append("Original")

    return groups


def gen_watch_bin(SEC_CODE, PROMO):
    if not PROMO:
        return
    return f"{SEC_CODE}-{PROMO}"


def clean_special_id(product):
    if product[0] == "131801":
        product[0] = "131800"
        return product


def clean_category(category):
    replacements = {
        "BATT": "Battery",
        "GLAS": "Glass",
        "POS": "Postage",
        "ROSC": "Roscani",
        "U2": "U2",
        "NTA": "Renata",
        "OTH": "Other",
        "WLET": "Aurafit",
        "-": "Non-stock"
    }
    return replacements.get(category, category)


def get_products():
    print("Getting products from asoft...")
    omit_list = ['ARA', 'ARX', 'BLY', 'STP']
    omit_string = ', '.join(f"'{item}'" for item in omit_list)
    special_id = ['131801']

    sql = f"""
    SELECT CODE, DESCRIPTION, SEC_CODE, STOCK_TYPE, CATEGORY,
    STK_GROUP, STDCOST, AVGCOST, PRICE1, PRICE2, 
    PRICE3, PRICE5, PRICE6, PRICE10, ACC_SET,
    REMARK, PROMO, DATE_ADD
    FROM STK
    WHERE STATUS = 'A'
    AND CATEGORY NOT IN ({omit_string})
    ORDER BY CODE
    """

    cursor.execute(sql)
    rows = cursor.fetchall()
    products = {}
    omit_product_ids = o.open_file("product_ids_omit_asoft")
    count = 0
    for row in rows:
        # Skip omitted products
        if row[0] in omit_product_ids:
            continue

        # Clean special case
        if row[0] in special_id:
            row = clean_special_id(row)

        # Cleaning the data
        group = clean_category(row[4])
        extra_groups = []
        if group in ["Roscani", "U2"]:
            extra_groups = gen_watch_groups(row[0], row[2], row[16])
            bin = gen_watch_bin(row[2], row[16])

        if group in ["Battery"]:
            extra_groups = gen_battery_groups(row[1])
            bin = row[2]

        group_ids = get_group_ids(group, extra_groups)

        # Putting all together
        product = {
            "sku": row[0],
            "name": row[1],
            "classification_code": "022",
            "dealer_price": row[8],
            "retail_price": row[9],
            "wholesale_price": row[10],  # for battery, glass, etc
            "wmm1_price": row[11],  # for wmm1 only
            "50_Off_price": row[12],  # for watches only
            "nong_price": row[13],  # for nong only
            "purchase_price": row[7],
            "group": group,
            "group_ids": group_ids,
            "remark": row[15],
            "updated_on": o.convert_date(row[17])
        }
        if group in ["Roscani", "U2", "Battery", "Aurafit"]:
            product["bin_location"] = bin

        products[row[0]] = product
        count += 1
    o.save_file("products_asoft", products)
    print(f"Total products: {count}")


if __name__ == "__main__":
    get_products()
