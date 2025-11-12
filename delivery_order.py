import ops as o
# ! Phase 3 - General Import


def create_delivery_order(dom_item, dod_item, products, contacts):
    contact_id = contacts[dom_item["card_id"]]["id"]
    doc_no = dom_item["doc_no"]
    # Assembling dom into params
    path = "sales/delivery_orders"
    params = {
        "contact_id": contact_id,
        "number": doc_no,
        "date": dom_item["doc_date"],
        "currency_code": dom_item["currency_id"],
        "exchange_rate": dom_item["currency_rate"],
        "term_id": 8,
        "tax_mode": "exclusive",
        "status": "ready",
        "inventory_check_confirm": True,
    }
    form_items = []
    for item in dod_item:
        item["stock_id"] = o.clean_glass_id(item["stock_id"])

        product_id = products[item["stock_id"]]["id"]
        form_item = {
            "product_id": product_id,
            "account_id": 20,
            "quantity": item["qty"],
            "unit_price": item["price"],
            "description": item["remark"],
        }
        form_items.append(form_item)
    params["form_items"] = form_items
    response = o.post_response(path, params)
    if "errors" in response:
        print(doc_no, "Error creating delivery order:", response["errors"])
        return False
    if "The delivery order number is used" in response.get("message", ""):
        print("Delivery order number already exists:", doc_no)
        o.save_to_added_list(doc_no, "delivery_orders")
        return False
    if "Inventory not able to fulfill order" in response.get("message", ""):
        print("Inventory not able to fulfill order:", doc_no)
        return False
    return True


def read_delivery_order_list():
    doc_num = ''
    contact_id = ''
    path = "sales/delivery_orders"
    params = {
        # "page": 1,  # optional
        "page_size": 30,  # optional
    }
    if doc_num:
        params["search"] = doc_num

    if contact_id:
        params["contact_id"] = contact_id

    return o.get_response(path, params)


def read_delivery_order(transaction_id):
    path = f"sales/delivery_orders/{transaction_id}"
    params = {}
    return o.get_response(path, params)


def bulk_create_delivery_order(dom_asoft, dod_asoft, do_added):
    print("Importing Delivery Orders to Bukku...")
    products = o.open_file("products_bukku_ids")
    contacts = o.open_file("contacts_bukku_ids")

    count = 0
    for do_id in dom_asoft:
        if o.check_doc_exists(do_id, do_added):
            continue

        dom_item = dom_asoft[do_id]
        dod_item = dod_asoft[do_id]

        created = create_delivery_order(dom_item, dod_item, products, contacts)
        if created:
            print("Delivery order created:", do_id)
            count += 1
            o.save_to_added_list(do_id, "delivery_orders")

        if count >= 100:
            break

    if count == 0:
        print("No new delivery orders to import.. exiting")
        exit()
    print(f"New DOs created: {count}")
    return True


if __name__ == "__main__":
    dod_asoft = o.open_file("dod_asoft")
    dom_asoft = o.open_file("dom_asoft")
    products = o.open_file("products_bukku_ids")
    contacts = o.open_file("contacts_bukku_ids")
    do_added = o.open_file("delivery_orders_added")

    bulk_create_delivery_order(dom_asoft, dod_asoft, do_added)
    o.read_tlist("delivery_orders")

    #transaction_id = "7"
    #save_file("delivery_order", read_delivery_order(transaction_id))
