import ops as o
from sales_order import read_sales_order
from delivery_order import read_delivery_order
import csv
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

    # Myinvois EXTERNAL for shopee, lazada and tiktok
    external = ["JSHP", "JLZD", "JTTK"]
    if ivm_item["card_id"] in external:
        base_params["myinvois_action"] = "EXTERNAL"

    return base_params


def build_form_items(ivd_item, products):
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
    contact_id = contacts[ivm_item["card_id"]]["id"]
    doc_no = ivm_item["doc_no"]
    path = "sales/invoices"

    params = create_base_params(ivm_item, contact_id)
    form_items = build_form_items(ivd_item, products)
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

def read_invoices_last_14_days(csv_path="data/invoices_last_14_days.csv"):
    """Retrieve invoices from the past 14 days and save number & amount to a CSV file.

    Args:
        csv_path (str): Destination CSV file path.
    Returns:
        List[dict]: List of dictionaries with keys 'number' and 'amount'.
    """
    from datetime import datetime, timedelta
    today = datetime.now().date()
    date_to = today.isoformat()
    date_from = (today - timedelta(days=14)).isoformat()
    path = "sales/invoices"
    params = {
        "date_from": date_from,
        "date_to": date_to,
        "page_size": 30,
    }
    response = o.get_response(path, params)
    result = []
    for txn in response.get("transactions", []):
        result.append({"number": txn.get("number"), "amount": txn.get("amount")})
    # Write to CSV
    try:
        with open(csv_path, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["number", "amount"])
            for row in result:
                writer.writerow([row.get("number"), row.get("amount")])
    except Exception as e:
        print(f"Error writing CSV: {e}")
    return result


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