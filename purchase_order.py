import ops as o
# ! Phase 3 - general import


def handle_spare_part(item):
    return {
        "account_id": 23,  # Cost of Goods
        "quantity": item["qty"],
        "unit_price": item["price"],
        "description": item["remark"],
    }


def create_purchase_order(pom_item, pod_item, products, contacts):
    contact_id = contacts[pom_item["card_id"]]["id"]
    # Assembling pom into params
    path = "purchases/orders"
    params = {
        "contact_id": contact_id,
        "number": pom_item["doc_no"],
        "date": pom_item["doc_date"],
        "currency_code": pom_item["currency_id"],
        "exchange_rate": pom_item["currency_rate"],
        "term_id": 1,  # COD
        "tax_mode": "exclusive",
        "status": "ready",
    }
    form_items = []
    for item in pod_item:
        item["stock_id"] = o.clean_glass_id(item["stock_id"])

        if item["stock_id"] in ["S/P", "PARTS2", "OTHERS"]:
            form_item = handle_spare_part(item)
            form_items.append(form_item)
            continue

        product_id = products[item["stock_id"]]["id"]
        form_item = {
            "product_id": product_id,
            "account_id": 5,  # Inventory
            "quantity": item["qty"],
            "unit_price": item["price"],
            "description": item["remark"],
        }
        form_items.append(form_item)
    params["form_items"] = form_items
    response = o.post_response(path, params)
    if "errors" in response:
        print(pom_item["doc_no"], "Error creating purchase order:",
              response["errors"])
        return False
    if "The purchase order number is used" in response.get("message", ""):
        print("Purchase order number already exists:", pom_item["doc_no"])
        o.save_to_added_list(pom_item["doc_no"], "purchase_orders")
        return False
    return True


def read_purchase_order_list():
    doc_num = ''
    contact_id = ''
    path = "purchases/orders"
    params = {
        # "page": 1,  # optional
        "page_size": 30,  # optional
    }
    if doc_num:
        params["search"] = doc_num

    if contact_id:
        params["contact_id"] = contact_id

    return o.get_response(path, params)


def read_purchase_order(transaction_id):
    path = f"purchases/orders/{transaction_id}"
    params = {}
    return o.get_response(path, params)


def bulk_create_purchase_order(pom_asoft, pod_asoft, po_added):
    print("Importing Purchase Orders to Bukku...")
    products = o.open_file("products_bukku_ids")
    contacts = o.open_file("contacts_bukku_ids")

    count = 0
    for po_id in pom_asoft:
        if o.check_doc_exists(po_id, po_added):
            continue

        pom_item = pom_asoft[po_id]
        pod_item = pod_asoft[po_id]

        created = create_purchase_order(pom_item, pod_item, products, contacts)
        if created:
            print("Product created:", po_id)
            count += 1
            o.save_to_added_list(po_id, "purchase_orders")

        if count >= 100:
            break

    if count == 0:
        print("No new purchase orders to import.. exiting")
        exit()
    print(f"New POs created: {count}")
    return True


if __name__ == "__main__":
    pod_asoft = o.open_file("pod_asoft")
    pom_asoft = o.open_file("pom_asoft")
    products = o.open_file("products_bukku_ids")
    contacts = o.open_file("contacts_bukku_ids")
    po_added = o.open_file("purchase_orders_added")

    bulk_create_purchase_order(pom_asoft, pod_asoft, po_added)
    o.read_tlist("purchase_orders")

    #transaction_id = "7"
    #save_file("purchase_order", read_purchase_order(transaction_id))
