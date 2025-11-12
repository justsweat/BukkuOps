import ops as o

# ! not a priority since it does not affect e-invoice
# ! also because in asoft, there's no card_id but bukku has


# ! Not change yet
def create_journal_entry(jem_item, jed_item, products, contacts):
    contact_id = contacts[jem_item["card_id"]]["id"]
    # Assembling pom into params
    path = "purchases/orders"
    params = {
        "contact_id": contact_id,
        "number": jem_item["doc_no"],
        "date": jem_item["doc_date"],
        "currency_code": jem_item["currency_id"],
        "exchange_rate": jem_item["currency_rate"],
        "term_id": 1,  # COD
        "tax_mode": "exclusive",
        "status": "ready",
    }
    form_items = []
    for item in jed_item:
        item["stock_id"] = o.clean_glass_id(item["stock_id"])
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
        print(jem_item["doc_no"], "Error creating sales order:",
              response["errors"])
        return False
    if "The journal entry number is used" in response.get("message", ""):
        print("Journal entry number already exists:", jem_item["doc_no"])
        o.save_to_added_list(jem_item["doc_no"], "sales_orders")
        return False
    return True


# ! Not change yet
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


# ! Not change yet
def read_purchases_order(transaction_id):
    path = f"purchases/orders/{transaction_id}"
    params = {}
    return o.get_response(path, params)


# ! Not change yet
def bulk_create_purchase_order(pom_asoft, pod_asoft, po_added):
    products = o.open_file("products_bukku_ids")
    contacts = o.open_file("contacts_bukku_ids")

    count = 0
    for po_id in pom_asoft:
        if o.check_doc_exists(po_id, po_added):
            continue

        pom_item = pom_asoft[po_id]
        pod_item = pod_asoft[po_id]

        created = create_journal_entry(pom_item, pod_item, products, contacts)
        if created:
            print("Product created:", po_id)
            o.save_to_added_list(po_id, "sales_orders")

        count += 1
        if count >= 20:
            break


# ! Not change yet
if __name__ == "__main__":
    pod_asoft = o.open_file("pod_asoft")
    pom_asoft = o.open_file("pom_asoft")
    products = o.open_file("products_bukku_ids")
    contacts = o.open_file("contacts_bukku_ids")
    po_added = o.open_file("purchase_orders_added")

    #doc_no = "A2501111"
    #pom_item = pom_asoft[doc_no]
    #pod_item = pod_asoft[doc_no]
    #create_purchase_order(pom_item, pod_item, products, contacts)

    bulk_create_purchase_order(pom_asoft, pod_asoft, po_added)
    #o.read_tlist("purchase_orders")

    #transaction_id = "7"
    #save_file("sales_order", read_sales_order(transaction_id))
