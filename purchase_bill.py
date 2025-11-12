import ops as o
from goods_received import read_goods_received

# ! Purchase bill = Supplier Invoice in asoft
# ! Phase 4 - as need Goods Received


def create_base_params(pbm_item, contact_id):
    return {
        "payment_mode": "credit",
        "contact_id": contact_id,
        "number": pbm_item["seq_no"],
        "number2": pbm_item["doc_no"],
        "date": pbm_item["doc_date"],
        "term_id": 3,
        "currency_code": pbm_item["currency_id"],
        "exchange_rate": pbm_item["currency_rate"],
        "description": pbm_item["remark"],
        "tax_mode": "exclusive",
        "status": "ready",
        "myinvois_action": "NORMAL",
        "customs_form_no": pbm_item["import_ref"],
        "customs_k2_form_no": None,
        "incoterms": None
    }


def get_classification_code(currency_id):
    if currency_id == 'MYR':
        return '022'

    if currency_id in ["USD", "HKD", "CNY"]:
        return '034'


def get_unique_grs(pbd_item, goods_receiveds):
    grs = []
    for item in pbd_item:
        gr_no = item.get("gr_no")
        if gr_no and gr_no in goods_receiveds:
            gr_id = goods_receiveds[item["gr_no"]]["id"]
            if gr_id not in grs:
                grs.append(gr_id)
    return grs


def build_form_with_gr(pbd_item, grs, products, pbm_item):
    # Get all grs from bukku and parse by stock_id
    stocks = {}
    for gr in grs:
        items = read_goods_received(gr)
        for item in items["transaction"]["form_items"]:
            item_no = str(item["line"])
            desc_snip = o.clean_remark(item["description"])[:15]
            sku = item["product_sku"]
            key = item_no + desc_snip  # cannot use SKU since got S/P
            stocks[key] = {
                "transfer_id": item["id"],
                "product_id": item["product_id"],
                "product_sku": sku
            }
    # Get currency id from pbm_item to pass for classification
    currency_id = pbm_item["currency_id"]

    # Match products with good received items
    form_items = []
    for item in pbd_item:
        stock_id = item["stock_id"]
        remark_snip = o.clean_remark(item["remark"])[:15]
        key = str(item["item_no"]) + remark_snip
        transfer_id = stocks[key].get("transfer_id")
        stock_id = o.clean_glass_id(stock_id)
        product_id = products[stock_id]["id"]
        form_item = {
            "transfer_item_id": transfer_id,
            "type": None,
            "account_id": 20,  # Sales Income
            "description": o.clean_remark(item["remark"]),
            "unit_price": item["price"],
            "quantity": item["qty"],
            "classification_code": get_classification_code(currency_id),
        }

        if stock_id not in ["S/P", "PARTS2", "OTHERS"]:
            form_item["product_id"] = product_id

        form_items.append(form_item)
    return form_items


def create_purchase_bill(pbm_item, pbd_item, products, contacts):
    goods_receiveds = o.open_file("goods_receiveds_bukku_ids")
    contact_id = contacts[pbm_item["card_id"]]["id"]
    path = "purchases/bills"

    # Base params
    params = create_base_params(pbm_item, contact_id)

    # Get all GRs
    grs = get_unique_grs(pbd_item, goods_receiveds)
    form_items = build_form_with_gr(pbd_item, grs, products, pbm_item)

    params["form_items"] = form_items

    # print(params)  # * for troubleshooting
    # Post the Purchase Bill
    response = o.post_response(path, params)

    # Handle response
    if "errors" in response:
        print(pbm_item["doc_no"], "Error creating purchase bill:",
              response["errors"])
        return False
    if "The purchase bill number is used" in response.get("message", ""):
        print("Purchase bill number already exists:", pbm_item["doc_no"])
        o.save_to_added_list(pbm_item["doc_no"], "purchase_bills")
        return False
    return True


def read_purchase_bill_list():
    doc_num = ''
    contact_id = ''
    path = "purchases/bills"
    params = {
        # "page": 1,  # optional
        "page_size": 30,  # optional
    }
    if doc_num:
        params["search"] = doc_num

    if contact_id:
        params["contact_id"] = contact_id

    return o.get_response(path, params)


def read_purchase_bill(transaction_id):
    path = f"purchases/bills/{transaction_id}"
    params = {}
    return o.get_response(path, params)


def bulk_create_purchase_bill(pbm_asoft, pbd_asoft, pb_added):
    print("Importing Purchase Bills to Bukku...")
    products = o.open_file("products_bukku_ids")
    contacts = o.open_file("contacts_bukku_ids")

    count = 0
    for pb_id in pbm_asoft:
        if o.check_doc_exists(pb_id, pb_added):
            continue

        pbm_item = pbm_asoft[pb_id]
        pbd_item = pbd_asoft[pb_id]

        created = create_purchase_bill(pbm_item, pbd_item, products, contacts)
        if created:
            print("Purchase bill created:", pb_id)
            count += 1
            o.save_to_added_list(pb_id, "purchase_bills")

        if count >= 100:
            break

    if count == 0:
        print("No new purchase bills to import.. exiting")
        exit()
    print(f"New Purchase Bills created: {count}")
    return True


if __name__ == "__main__":
    pbd_asoft = o.open_file("pbd_asoft")
    pbm_asoft = o.open_file("pbm_asoft")
    products = o.open_file("products_bukku_ids")
    contacts = o.open_file("contacts_bukku_ids")
    pb_added = o.open_file("purchase_bills_added")

    bulk_create_purchase_bill(pbm_asoft, pbd_asoft, pb_added)
    o.read_tlist("purchase_bills")

    #transaction_id = "7"
    #save_file("sales_order", read_sales_order(transaction_id))
