import ops as o
# ! Phase 3 - order import


def build_so_form_items(sod_item):
    products = o.open_file("products_bukku_ids")

    form_items = []
    for item in sod_item:
        item["stock_id"] = o.clean_glass_id(item["stock_id"])
        product_id = products[item["stock_id"]]["id"]
        form_item = {
            "product_id": product_id,
            "account_id": 20,
            "quantity": item["qty"],
            "unit_price": item["price"],
            "description": item["remark"],
            "discount": item["disc_amt"]
        }
        form_items.append(form_item)
    return form_items


def build_so_params(som_item, form_items, contact_id):
    params = {
        "contact_id": contact_id,
        "number": som_item["doc_no"],
        "date": som_item["doc_date"],
        "currency_code": "MYR",
        "exchange_rate": 1,
        "term_id": 8,
        "tax_mode": "exclusive",
        "status": "ready",
    }
    params["form_items"] = form_items
    return params


def create_sales_order(params):
    doc_no = params["number"]
    path = "sales/orders"
    response = o.post_response(path, params)
    if "errors" in response:
        print(doc_no, "Error creating sales order:", response["errors"])
        return False
    if "The sales order number is used" in response.get("message", ""):
        print("Sales order number already exists:", doc_no)
        o.save_to_added_list(doc_no, "sales_orders")
        return False
    return True


def read_sales_order_list():
    doc_num = ''
    contact_id = ''
    path = "sales/orders"
    params = {
        # "page": 1,  # optional
        "page_size": 30,  # optional
    }
    if doc_num:
        params["search"] = doc_num

    if contact_id:
        params["contact_id"] = contact_id

    return o.get_response(path, params)


def read_sales_order(transaction_id):
    path = f"sales/orders/{transaction_id}"
    params = {}
    return o.get_response(path, params)


def build_sales_order(so_id):
    sod_asoft = o.open_file("sod_asoft")
    som_asoft = o.open_file("som_asoft")
    so_added = o.open_file("sales_orders_added")
    contacts = o.open_file("contacts_bukku_ids")

    if o.check_doc_exists(so_id, so_added):
        return False

    som_item = som_asoft[so_id]
    sod_item = sod_asoft[so_id]
    contact_id = contacts[som_item["card_id"]]["id"]

    form_items = build_so_form_items(sod_item)
    params = build_so_params(som_item, form_items, contact_id)
    return params


def bulk_create_sales_order(som_asoft):
    print("Importing Sales Orders to Bukku...")

    count = 0
    for so_id in som_asoft:
        params = build_sales_order(so_id)
        if not params:
            continue

        created = create_sales_order(params)
        if created:
            print("Sales Order created:", so_id)
            count += 1
            o.save_to_added_list(so_id, "sales_orders")

        if count >= 200:
            break

    if count == 0:
        print("No new sales orders to import.. exiting")
        return
    print(f"New SOs created: {count}")
    o.read_tlist("sales_orders")


if __name__ == "__main__":
    som_asoft = o.open_file("som_asoft")

    bulk_create_sales_order(som_asoft)
    # o.read_tlist("sales_orders")

    transaction_id = "3535"
    o.save_file("sales_order", read_sales_order(transaction_id))
