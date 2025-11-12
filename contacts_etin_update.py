import ops as o
from contacts import read_contact


# ! Not in batch file
def update_etin(contact_item, contact_id):
    contact_res = read_contact(contact_id)
    contact = contact_res["contact"]

    path = f"contacts/{contact_id}"
    # Update contact
    contact["reg_no_type"] = "BRN"
    contact["old_reg_no"] = contact_item["old_roc"]
    contact["reg_no"] = contact_item["new_roc"]
    contact["tax_id_no"] = contact_item["tin"]
    contact["email"] = contact_item["email"]
    contact["phone_no"] = o.clean_phone(contact_item["contact_number"])
    # updating deprecated attr
    contact["legal_name"] = contact["display_name"]
    contact["other_name"] = contact["company_name"]
    del contact["display_name"]
    del contact["company_name"]

    #Fill in city for melaka
    state = contact["addresses"][0]["state"]
    city = contact["addresses"][0]["city"]
    if state == "Melaka" and city in ["", None]:
        contact["addresses"][0]["city"] = "Melaka"

    # Post response
    response = o.put_response(path, contact)

    # Handle Response
    if "message" in response:
        print(contact_item["code"], "Error updating contact:",
              response["message"])
        return False

    if "errors" in response:
        print(contact_item["code"], "Error updating contact:",
              response["errors"])
        return False
    return True


def bulk_update_etin(contacts, contacts_updated):
    etins = o.open_file("etin")
    count = 0
    for code in etins:
        contact_id = contacts[code]["id"]
        contact_item = etins[code]

        if o.check_doc_exists(code, contacts_updated):
            continue

        updated = update_etin(contact_item, contact_id)
        if updated:
            print("Contact updated", code)
            o.save_to_added_list(code, "contacts_updated")

        count += 1
        if count >= 20:
            break


if __name__ == "__main__":
    asoft_contacts = o.open_file("contacts_asoft")
    contacts = o.open_file("contacts_bukku_ids")
    contacts_updated = o.open_file("contacts_updated_added")

    #o.parse_xlsx_to_json("etin.xlsx")
    bulk_update_etin(contacts, contacts_updated)
    #o.read_list("contacts")

    #print(read_contact("882"))
