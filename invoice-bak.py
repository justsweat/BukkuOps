import ops as o
from sales_order import read_sales_order
from delivery_order import read_delivery_order
# ! Phase 4 - need both SO and DO


def create_base_params(ivm_item, contact_id):
    id_str = str(contact_id)
    contact_info = o.open_file("contacts_bukku")
    billing_party = contact_info[id_str]["billing_party"]

    base_params = {
        "payment_mode": "credit",
        "contact_id": contact_id,
        "number": ivm_item["doc_no"],
        "date": ivm_item["doc_date"],
        "currency_code": "MYR",
        "exchange_rate": 1,
        "billing_party": billing_party,
        "term_items": [{
            "term_id": 8,
            "payment_due": "100%"
        }],
        "tag_ids": [ivm_item["invoice_type"]],
        "tax_mode": "exclusive",
        "status": "ready",
        "myinvois_action": "NORMAL",
        "customs_form_no": None,
        "customs_k2_form_no": None,
        "incoterms": None
    }

    # Myinvois EXTERNAL for shopee and tictok
    external = ["JSHP", "JTTK"]
    if ivm_item["card_id"] in external:
        base_params["myinvois_action"] = "EXTERNAL"

    return base_params


def get_unique_sos(ivd_item, sales_orders):
    sos = []
    for item in ivd_item:
        so_no = item.get("so_no")
        if so_no and so_no in sales_orders:
            so_id = sales_orders[item["so_no"]]["id"]
            if so_id not in sos:
                sos.append(so_id)
    return sos


def get_unique_dos(ivd_item, delivery_orders):
    dos = []
    for item in ivd_item:
        do_no = item.get("do_no")
        if do_no and do_no in delivery_orders:
            do_id = delivery_orders[item["do_no"]]["id"]
            if do_id not in dos:
                dos.append(do_id)
    return dos


def build_form_with_so(ivd_item, sos, products):
    # Get all sos from bukku and parse by stock_id
    stocks = {}
    for so in sos:
        items = read_sales_order(so)
        for item in items["transaction"]["form_items"]:
            item_no = str(item["line"])
            sku = item["product_sku"]
            key = sku  #!temp
            # key = item_no + sku  #! use this if there's dup sku in SO
            stocks[key] = {
                "transfer_id": item["id"],
                "product_id": item["product_id"],
                "product_sku": sku
            }
        so_no = items["transaction"]["number"]

    # Match products with sales order items
    form_items = []
    printed_warning = False
    #print(stocks)  #!enable to troubleshoot and see what's in SO
    #print(ivd_item)  #!enable to troubleshoot
    for item in ivd_item:
        stock_id = item["stock_id"]
        stock = stocks.get(stock_id)
        if not stock:
            if not printed_warning:
                print(f"There's changes in SO {so_no} for {item['doc_no']}")
                printed_warning = True

        #key = str(
        #    item["so_itemno"]) + stock_id  #! use this if there's dup sku in SO
        stock_id = o.clean_glass_id(stock_id)
        key = stock_id  #! temp
        #print(key)  #!enable to troubleshoot keyerror
        transfer_id = stocks[key].get("transfer_id")
        #print(transfer_id)  #!enable to troubleshoot keyerror
        product_id = products[stock_id]["id"]
        form_item = {
            "transfer_item_id": transfer_id,
            "type": None,
            "account_id": 20,
            "description": item["remark"],
            "product_id": product_id,
            "unit_price": item["price"],
            "quantity": item["qty"],
            "discount": item["disc_amt"],
            "classification_code": "022",
        }
        form_items.append(form_item)
    return form_items


def build_form_with_do(ivd_item, dos, products):
    # Get all dos from bukku and parse by stock_id
    stocks = {}
    for do in dos:
        items = read_delivery_order(do)
        for item in items["transaction"]["form_items"]:
            sku = item["product_sku"]
            stocks[sku] = {
                "transfer_id": item["id"],
                "product_id": item["product_id"],
                "product_sku": sku
            }

    # Match products with sales order items
    form_items = []
    for item in ivd_item:
        stock_id = item["stock_id"]
        transfer_id = stocks[stock_id]["transfer_id"]
        stock_id = o.clean_glass_id(stock_id)

        product_id = products[stock_id]["id"]
        form_item = {
            "transfer_item_id": transfer_id,
            "type": None,
            "account_id": 20,
            "description": item["remark"],
            "product_id": product_id,
            "unit_price": item["price"],
            "quantity": item["qty"],
            "discount": item["disc_amt"],
            "classification_code": "022",
        }
        form_items.append(form_item)
    return form_items


def build_form_without_so(ivd_item, products):
    form_items = []
    for item in ivd_item:
        stock_id = item["stock_id"]
        stock_id = o.clean_glass_id(stock_id)
        product_id = products[stock_id]["id"]

        form_item = {
            "type": None,
            "account_id": 20,
            "description": item["remark"],
            "product_id": product_id,
            "unit_price": item["price"],
            "quantity": item["qty"],
            "discount": item["disc_amt"],
            "classification_code": "022",
        }
        form_items.append(form_item)
    return form_items


def create_invoice(ivm_item, ivd_item, products, contacts):
    sales_orders = o.open_file("sales_orders_bukku_ids")
    delivery_orders = o.open_file("delivery_orders_bukku_ids")

    contact_id = contacts[ivm_item["card_id"]]["id"]
    doc_no = ivm_item["doc_no"]
    path = "sales/invoices"

    # Base params
    params = create_base_params(ivm_item, contact_id)

    # Determine if there are SOs and DOs
    sos = get_unique_sos(ivd_item, sales_orders)
    dos = get_unique_dos(ivd_item, delivery_orders)

    if sos:
        form_items = build_form_with_so(ivd_item, sos, products)
    elif dos:
        form_items = build_form_with_do(ivd_item, dos, products)
    else:
        form_items = build_form_without_so(ivd_item, products)

    params["form_items"] = form_items

    # Post the invoice
    response = o.post_response(path, params)

    # Handle response
    if "The invoice number is used" in response.get("message", ""):
        print("Invoice number already exists:", doc_no)
        o.save_to_added_list(doc_no, "invoices")
        return False
    if "message" in response:
        print(doc_no, "[A]Error creating invoice:", response["message"])
        for idx, item in enumerate(form_items):
            print(idx, item["description"], item["quantity"],
                  item["unit_price"])

        return False
    if "errors" in response:
        print(doc_no, "[B]Error creating invoice:", response["errors"])
        return False
    return True


def read_invoice_list():
    doc_num = ''
    contact_id = ''
    path = "sales/invoices"
    params = {
        # "page": 1,  # optional
        "page_size": 30,  # optional
    }
    if doc_num:
        params["search"] = doc_num

    if contact_id:
        params["contact_id"] = contact_id

    return o.get_response(path, params)


def read_invoice(transaction_id):
    path = f"sales/invoices/{transaction_id}"
    params = {}
    return o.get_response(path, params)


def bulk_create_invoice(ivm_asoft, ivd_asoft, iv_added):
    print("Importing Invoices to Bukku...")
    products = o.open_file("products_bukku_ids")
    contacts = o.open_file("contacts_bukku_ids")

    count = 0
    for iv_id in ivm_asoft:
        if o.check_doc_exists(iv_id, iv_added):
            continue

        ivm_item = ivm_asoft[iv_id]
        ivd_item = ivd_asoft[iv_id]

        # Skip 0 value service bill
        if ivm_item["amount"] == 0:
            print(f"Skipped {ivm_item['doc_no']} due to 0 value")
            o.save_to_added_list(iv_id, "invoices")
            continue

        created = create_invoice(ivm_item, ivd_item, products, contacts)
        if created:
            print("Invoice created:", iv_id)
            count += 1
            o.save_to_added_list(iv_id, "invoices")

        if count >= 200:
            break

    if count == 0:
        print("No new invoices to import.. exiting")
        exit()
    print(f"New Invoices created: {count}")
    return True


if __name__ == "__main__":
    ivd_asoft = o.open_file("ivd_asoft")
    ivm_asoft = o.open_file("ivm_asoft")
    products = o.open_file("products_bukku_ids")
    contacts = o.open_file("contacts_bukku_ids")
    iv_added = o.open_file("invoices_added")

    bulk_create_invoice(ivm_asoft, ivd_asoft, iv_added)
    o.read_tlist("invoices")

    #transaction_id = "2049"
    #o.save_file("invoice", read_invoice(transaction_id))
