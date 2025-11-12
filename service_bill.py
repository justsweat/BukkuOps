import ops as o


def create_base_params(svm_item, contact_id):
    id_str = str(contact_id)
    contact_info = o.open_file("contacts_bukku")
    billing_party = contact_info[id_str]["billing_party"]

    base_params = {
        "payment_mode": "credit",
        "contact_id": contact_id,
        "number": svm_item["doc_no"],
        "date": svm_item["doc_date"],
        "currency_code": "MYR",
        "exchange_rate": 1,
        "billing_party": billing_party,
        "term_items": [{
            "term_id": 8,
            "payment_due": "100%"
        }],
        "tag_ids": [svm_item["invoice_type"]],
        "tax_mode": "exclusive",
        "status": "ready",
        "myinvois_action": "NORMAL",
        "customs_form_no": None,
        "customs_k2_form_no": None,
        "incoterms": None
    }

    return base_params


def create_form(svd_item, products):
    form_items = []
    for item in svd_item:
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
            "classification_code": "030",
        }
        form_items.append(form_item)
    return form_items


def create_invoice(svm_item, svd_item, products, contacts):
    contact_id = contacts[svm_item["card_id"]]["id"]
    doc_no = svm_item["doc_no"]
    path = "sales/invoices"

    # Base params
    params = create_base_params(svm_item, contact_id)
    form_items = create_form(svd_item, products)

    params["form_items"] = form_items

    # Post the invoice
    response = o.post_response(path, params)

    # Handle response
    if "The invoice number is used" in response.get("message", ""):
        print("Invoice number already exists:", doc_no)
        o.save_to_added_list(doc_no, "service_bills")
        return False
    if "message" in response:
        print(doc_no, "Error creating invoice:", response["message"])
        return False
    if "errors" in response:
        print(doc_no, "Error creating invoice:", response["errors"])
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


def bulk_create_invoice(svm_asoft, svd_asoft, sv_added):
    print("Importing Service Bill Invoices to Bukku...")
    products = o.open_file("products_bukku_ids")
    contacts = o.open_file("contacts_bukku_ids")

    count = 0
    for sv_id in svm_asoft:
        if o.check_doc_exists(sv_id, sv_added):
            continue

        svm_item = svm_asoft[sv_id]
        svd_item = svd_asoft[sv_id]

        # Skip 0 value service bill
        if svm_item["amount"] == 0:
            print(f"Skipped {svm_item['doc_no']} due to 0 value")
            o.save_to_added_list(sv_id, "service_bills")
            continue

        created = create_invoice(svm_item, svd_item, products, contacts)
        if created:
            print("Invoice created:", sv_id)
            count += 1
            o.save_to_added_list(sv_id, "service_bills")

        if count >= 20:
            break

    if count == 0:
        print("No new Service Bill to import.. exiting")
        exit()
    print(f"New Service Bill created: {count}")
    return True


if __name__ == "__main__":
    svd_asoft = o.open_file("svd_asoft")
    svm_asoft = o.open_file("svm_asoft")
    products = o.open_file("products_bukku_ids")
    contacts = o.open_file("contacts_bukku_ids")
    sv_added = o.open_file("service_bills_added")

    bulk_create_invoice(svm_asoft, svd_asoft, sv_added)
    o.read_tlist("invoices")

    #transaction_id = "2049"
    #o.save_file("invoice", read_invoice(transaction_id))
