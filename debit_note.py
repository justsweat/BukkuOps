import ops as o


def create_base_params(dnm_item, contact_id):
    return {
        "payment_mode": "credit",
        "contact_id": contact_id,
        "number": dnm_item["doc_no"],
        "date": dnm_item["doc_date"],
        "currency_code": "MYR",
        "exchange_rate": 1,
        "term_items": [{
            "term_id": 8,
            "payment_due": "100%"
        }],
        "tag_ids": [dnm_item["invoice_type"]],
        "tax_mode": "exclusive",
        "status": "ready",
        "myinvois_action": "NORMAL",
        "customs_form_no": None,
        "customs_k2_form_no": None,
        "incoterms": None
    }


def create_form_item(ivd_item, products):
    form_items = []
    for item in ivd_item:
        stock_id = item["stock_id"]
        product_id = products[stock_id]["id"]

        form_item = {
            "type": None,
            "account_id": 20,
            "description": item["remark"],
            "product_id": product_id,
            "unit_price": item["price"],
            "quantity": item["qty"],
            "classification_code": "022",
        }
        form_items.append(form_item)
    return form_items


def create_debit_note(dnm_item, dnd_item, products, contacts):
    contact_id = contacts[dnm_item["card_id"]]["id"]
    doc_no = dnm_item["doc_no"]
    path = "sales/invoices"

    # Base params
    params = create_base_params(dnm_item, contact_id)
    form_items = create_form_item(dnd_item, products)

    params["form_items"] = form_items

    # Post the invoice
    response = o.post_response(path, params)

    # Handle response
    if "The debit note number is used" in response.get("message", ""):
        print("Debit note number already exists:", doc_no)
        o.save_to_added_list(doc_no, "debit_notes")
        return False
    if "message" in response:
        print(doc_no, "Error creating debit note:", response["message"])
        return False
    if "errors" in response:
        print(doc_no, "Error creating debit note:", response["errors"])
        return False
    return True


def read_debit_note(transaction_id):
    path = f"sales/invoices/{transaction_id}"
    params = {}
    return o.get_response(path, params)


def bulk_create_debit_note(dnm_asoft, dnd_asoft, iv_added):
    print("Importing Debit Notes to Bukku...")
    products = o.open_file("products_bukku_ids")
    contacts = o.open_file("contacts_bukku_ids")

    count = 0
    for dn_id in dnm_asoft:
        if o.check_doc_exists(dn_id, iv_added):
            continue

        dnm_item = dnm_asoft[dn_id]
        dnd_item = dnd_asoft[dn_id]

        created = create_debit_note(dnm_item, dnd_item, products, contacts)
        if created:
            print("Debit Note created:", dn_id)
            count += 1
            o.save_to_added_list(dn_id, "debit_notes")

        if count >= 50:
            break

    if count == 0:
        print("No new debit notes to import.. exiting")
        exit()
    print(f"New Debit Notes created: {count}")
    return True


if __name__ == "__main__":
    dnd_asoft = o.open_file("dnd_asoft")
    dnm_asoft = o.open_file("dnm_asoft")
    dn_added = o.open_file("debit_notes_added")

    bulk_create_debit_note(dnm_asoft, dnd_asoft, dn_added)
    o.read_tlist("debit_notes")

    #transaction_id = "7"
    #save_file("sales_order", read_sales_order(transaction_id))
