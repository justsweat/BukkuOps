import ops as o
# ! Phase 3 - General Import


def create_credit_note(cnm_item, cnd_item, products, contacts):
    contact_id = contacts[cnm_item["card_id"]]["id"]
    # Assembling into params
    path = "sales/credit_notes"
    params = {
        "contact_id": contact_id,
        "number": cnm_item["doc_no"],
        "date": cnm_item["doc_date"],
        "currency_code": cnm_item["currency_id"],
        "exchange_rate": cnm_item["currency_rate"],
        "tag_ids": [cnm_item["adj_type"]],
        "tax_mode": "exclusive",
        "status": "ready",
        "myinvois_action": "NORMAL",
        "description": cnm_item["remark"],
        "customs_form_no": None,
        "customs_k2_form_no": None,
        "incoterms": None
    }

    # Myinvois EXTERNAL for shopee and tictok
    external = ["JSHP", "JTTK"]
    if cnm_item["card_id"] in external:
        params["myinvois_action"] = "EXTERNAL"

    form_items = []
    for item in cnd_item:
        item["stock_id"] = o.clean_glass_id(item["stock_id"])

        product_id = products[item["stock_id"]]["id"]
        form_item = {
            "product_id": product_id,
            "account_id": 20,  # Sales Income
            "quantity": item["qty"],
            "unit_price": item["price"],
            "description": item["remark"],
            "classification_code": "022"
        }
        form_items.append(form_item)
    params["form_items"] = form_items
    response = o.post_response(path, params)
    if "errors" in response:
        print(cnm_item["doc_no"], "Error creating credit note:",
              response["errors"])
        return False
    if "The credit note number is used" in response.get("message", ""):
        print("Credit note number already exists:", cnm_item["doc_no"])
        o.save_to_added_list(cnm_item["doc_no"], "credit_notes")
        return False
    return True


def read_credit_note_list():
    doc_num = ''
    contact_id = ''
    path = "sales/credit_notes"
    params = {
        # "page": 1,  # optional
        "page_size": 30,  # optional
    }
    if doc_num:
        params["search"] = doc_num

    if contact_id:
        params["contact_id"] = contact_id

    return o.get_response(path, params)


def read_credit_note(transaction_id):
    path = f"sales/credit_notes/{transaction_id}"
    params = {}
    return o.get_response(path, params)


def bulk_create_credit_note(cnm_asoft, cnd_asoft, cn_added):
    print("Importing Credit Note to Bukku...")
    products = o.open_file("products_bukku_ids")
    contacts = o.open_file("contacts_bukku_ids")

    count = 0
    for cn_id in cnm_asoft:
        if o.check_doc_exists(cn_id, cn_added):
            continue

        cnm_item = cnm_asoft[cn_id]
        cnd_item = cnd_asoft[cn_id]

        created = create_credit_note(cnm_item, cnd_item, products, contacts)
        if created:
            print("Credit Note created:", cn_id)
            count += 1
            o.save_to_added_list(cn_id, "credit_notes")

        if count >= 100:
            break

    if count == 0:
        print("No new credit notes to import.. exiting")
        exit()

    print(f"New CNs created: {count}")
    return True


if __name__ == "__main__":
    cnd_asoft = o.open_file("cnd_asoft")
    cnm_asoft = o.open_file("cnm_asoft")
    products = o.open_file("products_bukku_ids")
    contacts = o.open_file("contacts_bukku_ids")
    cn_added = o.open_file("credit_notes_added")

    #doc_no = "A2501111"
    #cnm_item = cnm_asoft[doc_no]
    #cnd_item = cnd_asoft[doc_no]
    #create_credit_note(cnm_item, cnd_item, products, contacts)

    bulk_create_credit_note(cnm_asoft, cnd_asoft, cn_added)
    o.read_tlist("credit_notes")

    #transaction_id = "7"
    #save_file("credit_note", read_credit_note(transaction_id))
