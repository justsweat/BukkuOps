import ops as o
from purchase_order import read_purchase_order
# ! Phase 4 - as need PO first


def build_base_params(grm_item, contact_id):
    return {
        "contact_id": contact_id,
        "number": grm_item["doc_no"],
        "date": grm_item["doc_date"],
        "currency_code": grm_item["currency_id"],
        "exchange_rate": grm_item["currency_rate"],
        "tax_mode": "exclusive",
        "status": "ready",
    }


def get_unique_pos(grd_item, purchase_orders):
    pos = []
    for item in grd_item:
        po_no = item.get("po_no")
        if po_no and po_no in purchase_orders:
            po_id = purchase_orders[item["po_no"]]["id"]
            if po_id not in pos:
                pos.append(po_id)
    return pos


def handle_spare_part(item):
    return {
        "account_id": 20,
        "unit_price": item["price"],
        "quantity": item["qty"],
        "description": item["remark"],
        "classification_code": "022"
    }


def build_form_with_po(grd_item, pos, products):
    # Get all pos from bukku and parse by stock_id
    stocks = {}
    for po in pos:
        items = read_purchase_order(po)
        for item in items["transaction"]["form_items"]:
            item_no = str(item["line"])
            desc = item["description"]
            sku = item["product_sku"]
            stocks[item_no + desc] = {
                "item_no": item_no,
                "transfer_id": item["id"],
                "product_id": item["product_id"],
                "product_sku": sku
            }

    # Match products with purchase order items
    form_items = []
    for item in grd_item:
        stock_id = item["stock_id"]
        key = str(item["item_no"]) + item['remark']
        transfer_id = stocks[key]["transfer_id"]
        stock_id = o.clean_glass_id(stock_id)

        if stock_id in ['S/P', 'PARTS2', 'OTHERS']:
            form_item = handle_spare_part(item)
            form_items.append(form_item)
            continue

        product_id = products[stock_id]["id"]
        form_item = {
            "transfer_item_id": transfer_id,
            "type": None,
            "account_id": 20,
            "description": item["remark"],
            "product_id": product_id,
            "unit_price": item["price"],
            "quantity": item["qty"],
            "classification_code":
            "022",  # ! might no need, not in documentation
        }
        form_items.append(form_item)
    return form_items


def build_form_without_po(grd_item, products):
    form_items = []
    for item in grd_item:
        stock_id = item["stock_id"]
        stock_id = o.clean_glass_id(stock_id)

        if stock_id in ['S/P', 'PARTS2']:
            form_item = handle_spare_part(item)
            form_items.append(form_item)
            continue

        product_id = products[stock_id]["id"]

        form_item = {
            "type": None,
            "account_id": 20,
            "description": item["remark"],
            "product_id": product_id,
            "unit_price": item["price"],
            "quantity": item["qty"],
            "classification_code":
            "022",  # ! might no need, not in documentation
        }
        form_items.append(form_item)
    return form_items


def create_goods_received(grm_item, grd_item, products, contacts):
    purchase_orders = o.open_file("purchase_orders_bukku_ids")
    contact_id = contacts[grm_item["card_id"]]["id"]
    path = "purchases/goods_received_notes"

    # Base params
    params = build_base_params(grm_item, contact_id)

    # Determine if there are POs
    pos = get_unique_pos(grd_item, purchase_orders)

    if pos:
        print("Creating GR with POs")
        form_items = build_form_with_po(grd_item, pos, products)

    if not pos:
        print("Creating GR without POs")
        form_items = build_form_without_po(grd_item, products)

    params["form_items"] = form_items
    # ! print(params)
    # Post
    response = o.post_response(path, params)

    # Handle response
    if "errors" in response:
        print(grm_item["doc_no"], "Error creating goods received:",
              response["errors"])
        return False
    if "The goods received number is used" in response.get("message", ""):
        print("Goods received number already exists:", grm_item["doc_no"])
        o.save_to_added_list(grm_item["doc_no"], "goods_receiveds")
        return False
    if "There isn't enough item quantity" in response.get("message", ""):
        print("Not enough item quantity from PO:", grm_item["doc_no"])
        return False
    return True


def read_goods_received_list():
    doc_num = ''
    contact_id = ''
    path = "purchases/goods_received_notes"
    params = {
        # "page": 1,  # optional
        "page_size": 30,  # optional
    }
    if doc_num:
        params["search"] = doc_num

    if contact_id:
        params["contact_id"] = contact_id

    return o.get_response(path, params)


def read_goods_received(transaction_id):
    path = f"purchases/goods_received_notes/{transaction_id}"
    params = {}
    return o.get_response(path, params)


def bulk_create_good_received(grm_asoft, grd_asoft, gr_added):
    print("Importing Goods Received to Bukku...")
    products = o.open_file("products_bukku_ids")
    contacts = o.open_file("contacts_bukku_ids")

    count = 0
    for gr_id in grm_asoft:
        if o.check_doc_exists(gr_id, gr_added):
            continue

        grm_item = grm_asoft[gr_id]
        grd_item = grd_asoft[gr_id]

        created = create_goods_received(grm_item, grd_item, products, contacts)
        if created:
            print("Good received created:", gr_id)
            count += 1
            o.save_to_added_list(gr_id, "goods_receiveds")

        if count >= 100:
            break

    if count == 0:
        print("No new goods received to import.. exiting")
        exit()
    print(f"New GRs created: {count}")
    return True


if __name__ == "__main__":
    grd_asoft = o.open_file("grd_asoft")
    grm_asoft = o.open_file("grm_asoft")
    products = o.open_file("products_bukku_ids")
    contacts = o.open_file("contacts_bukku_ids")
    gr_added = o.open_file("goods_receiveds_added")

    bulk_create_good_received(grm_asoft, grd_asoft, gr_added)
    o.read_tlist("goods_receiveds")

    #transaction_id = "7"
    #save_file("sales_order", read_sales_order(transaction_id))
