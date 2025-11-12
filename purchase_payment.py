import ops as o
from purchase_bill import read_purchase_bill
# ! Phase 4 - need purchase bill


def create_base_params(ppm_item, contact_id):
    return {
        "contact_id": contact_id,
        "number": ppm_item["doc_no"],
        "number2": ppm_item["cheque_no"],
        "date": ppm_item["doc_date"],
        "currency_code": ppm_item["currency_id"],
        "exchange_rate": ppm_item["currency_rate"],
        "amount": ppm_item["amount"],
        "description": ppm_item["gl_desc"],
        "status": "ready",
        "myinvois_action": "NORMAL",
        "customs_form_no": None,
        "customs_k2_form_no": None,
        "incoterms": None
    }


def create_items_cash(ppd_item, got_cheque):
    deposit_items = []
    for item in ppd_item:
        deposit_item = {
            "payment_method_id": 1,
            "account_id": 3,
            "amount": item["apply_amount"],
            "number": item["remark"][:50],
        }

        if got_cheque:
            deposit_item["payment_method_id"] = 5  # Cheque

        deposit_items.append(deposit_item)
    return deposit_items


def create_items_credit(ppd_item, got_cheque):
    deposit_items = []
    for item in ppd_item:
        deposit_item = {
            "payment_method_id": 1,
            "account_id": 3,
            "amount": item["amount"],
            "number": item["remark"],
        }

        if got_cheque:
            deposit_item["payment_method_id"] = 5  # Cheque

        deposit_items.append(deposit_item)
    return deposit_items


def create_link_items(ppd_item):
    purchase_bills = o.open_file("purchase_bills_bukku_ids")
    link_items = []
    for item in ppd_item:
        pb_no = item["match_doc"]
        pb_id = purchase_bills[pb_no]["id"]
        link_item = {
            "target_transaction_id": pb_id,
            "apply_amount": item["apply_amount"],
        }
        link_items.append(link_item)
    return link_items


def create_purchase_payment(ppm_item, ppd_item, products, contacts):
    contact_id = contacts[ppm_item["card_id"]]["id"]
    link_items = {}
    path = "purchases/payments"

    # Base params
    params = create_base_params(ppm_item, contact_id)

    # Create binary got checking cheque
    got_cheque = False
    if ppm_item["cheque_no"]:
        got_cheque = True

    # Determine payment mode and add in details
    if ppm_item["card_id"] == 'OPBL':
        params["payment_mode"] = "cash"
        deposit_items = create_items_cash(ppd_item, got_cheque)

    if ppm_item["card_id"] != 'OPBL':
        params["payment_mode"] = "credit"
        deposit_items = create_items_credit(ppd_item, got_cheque)
        link_items = create_link_items(ppd_item)

    params["deposit_items"] = deposit_items
    params["link_items"] = link_items

    # Post the invoice
    response = o.post_response(path, params)

    # Handle response
    if "message" in response:
        print(ppm_item["doc_no"], "Error creating purchase payment:",
              response["message"])
        return False
    if "errors" in response:
        print(ppm_item["doc_no"], "Error creating purchase payment:",
              response["errors"])
        return False
    if "The purchase payment is used" in response.get("message", ""):
        print("Purchase payment number already exists:", ppm_item["doc_no"])
        o.save_to_added_list(ppm_item["doc_no"], "purchase_payments")
        return False
    if "Deposit items total must be equal" in response.get("message", ""):
        print("Deposit items total must be equal to transaction total:",
              ppm_item["doc_no"])
        return False
    return True


def read_purchase_payment_list():
    doc_num = ''
    contact_id = ''
    path = "purchases/payments"
    params = {
        # "page": 1,  # optional
        "page_size": 30,  # optional
    }
    if doc_num:
        params["search"] = doc_num

    if contact_id:
        params["contact_id"] = contact_id

    return o.get_response(path, params)


def read_purchase_payment(transaction_id):
    path = f"purchases/payments/{transaction_id}"
    params = {}
    return o.get_response(path, params)


def bulk_create_purchase_payment(ppm_asoft, ppd_asoft, pp_added):
    print("Importing Purchase Payments to Bukku...")
    products = o.open_file("products_bukku_ids")
    contacts = o.open_file("contacts_bukku_ids")

    count = 0
    for pp_id in ppm_asoft:
        if o.check_doc_exists(pp_id, pp_added):
            continue

        ppm_item = ppm_asoft[pp_id]
        ppd_item = ppd_asoft[pp_id]

        created = create_purchase_payment(ppm_item, ppd_item, products,
                                          contacts)
        if created:
            print("Purchase payment created:", pp_id)
            count += 1
            o.save_to_added_list(pp_id, "purchase_payments")

        if count >= 10:
            break

    if count == 0:
        print("No new purchase payments to import.. exiting")
        exit()
    print(f"New Purchase Payments created: {count}")
    return True


if __name__ == "__main__":
    ppd_asoft = o.open_file("ppd_asoft")
    ppm_asoft = o.open_file("ppm_asoft")
    products = o.open_file("products_bukku_ids")
    contacts = o.open_file("contacts_bukku_ids")
    pp_added = o.open_file("purchase_payments_added")

    bulk_create_purchase_payment(ppm_asoft, ppd_asoft, pp_added)
    o.read_tlist("purchase_payments")

    #transaction_id = "405"
    #o.save_file("purchase_payment", read_purchase_payment(transaction_id))
