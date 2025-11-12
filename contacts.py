import ops as o
# ! Phase 2 - Core import
entity_type = [
    "MALAYSIAN_COMPANY", "MALAYSIAN_INDIVIDUAL", "FOREIGN_COMPANY",
    "FOREIGN_INDIVIDUAL", "EXEMPTED_PERSON"
]

types = [
    "customer",
    "supplier",
    "employee",
]


def get_types(contact):
    if contact["contact_type"] == "C":
        return ["customer"]

    if contact["contact_type"] == "B":
        return ["customer", "supplier"]

    if contact["contact_type"] == "S":
        return ["supplier"]


def create_contact(contact):
    contact_persons = [{
        "first_name": contact["contact"],
        "last_name": "",
        "is_default_billing": "true",
        "is_default_shipping": "true"
    }]

    if "address" in contact:
        addresses = [{
            "name": "Main Address",
            "street": contact["address"],
            "city": contact["city"],
            "state": contact["state"],
            "postcode": contact["postcode"],
            "country_code": contact["country"],
            "is_default_billing": "true",
            "is_default_shipping": "true"
        }]
    agent = {"field_id": 2, "value": contact["agent"]}

    # Assembling into params
    path = "contacts"
    params = {
        "entity_type": contact["entity_type"],
        "legal_name": contact["name"],
        "other_name": contact["code"],
        "reg_no": "000000000000",  # Temp reg no
        "reg_no_type": "BRN",
        "tax_id_no": "000000000000",  # Temp tax id
        "contact_persons": contact_persons,
        "phone_no": contact["phone_num"],
        "types": get_types(contact),
        "default_currency_code": "MYR",
        "default_term_id": 8,
        "receive_monthly_statement": "true",
        "receive_invoice_reminder": "false",
        "remarks": contact["remark"],
        "fields": [agent],
    }
    if "address" in contact:
        params["addresses"] = addresses

    # Post response
    response = o.post_response(path, params)

    # Handle Response
    if "message" in response:
        print(contact["code"], "[A] Error creating contact:",
              response["message"])
        print(params)
        return False

    if "errors" in response:
        print(contact["code"], "[B] Error creating contact:",
              response["errors"])
        return False
    return True


def read_contact_list(page=1, page_size=30):
    code = "MABC"
    path = "contacts"
    params = {
        "page": page,  # optional
        "page_size": page_size,  # optional
        "search": code,  # optional # string
    }
    return o.get_response(path, params)


def read_contact_by_code(code):
    contacts = o.open_file("contacts_bukku_ids")
    id = contacts[code]["id"]

    path = f"contacts/{id}"
    params = {}
    return o.get_response(path, params)


def read_contact(contact_id):
    path = f"contacts/{contact_id}"
    params = {}
    return o.get_response(path, params)


def bulk_create_contacts(asoft_contacts, contacts_added):
    print("Importing Contacts to Bukku...")
    special_contacts = ["NYMT"]  # Closed but still need to be in system

    count = 0
    for contact in asoft_contacts:
        contact_id = asoft_contacts[contact]["code"]
        status = asoft_contacts[contact]["status"]

        # Allow special contact
        if status == "C" and contact_id not in special_contacts:
            continue

        if o.check_doc_exists(contact_id, contacts_added):
            continue

        created = create_contact(asoft_contacts[contact])
        if created:
            print("Contact created:", contact_id)
            count += 1
            o.save_to_added_list(contact_id, "contacts")

        if count >= 100:
            break

    if count == 0:
        print("No new contacts to import.. exiting")
        return
    o.read_list("contacts")


def bulk_update_contacts(asoft_contacts):
    bukku_contact_ids = o.open_file("contacts_bukku_ids")

    print("Updating Contacts to Bukku...")
    special_contacts = ["NYMT"]  # Closed but still need to be in system

    count = 0
    for contact in asoft_contacts:
        contact_id = asoft_contacts[contact]["code"]
        status = asoft_contacts[contact]["status"]
        updated_on_asoft = asoft_contacts[contact]["updated_on"]

        # Allow special contact
        if status == "C" and contact_id not in special_contacts:
            continue

        updated_on_bukku = bukku_contact_ids[contact_id]["updated_on"]

        if updated_on_asoft >= updated_on_bukku:
            print("got update", contact)
        continue
        created = create_contact(asoft_contacts[contact])
        if created:
            print("Contact created:", contact_id)
            count += 1
            o.save_to_added_list(contact_id, "contacts")

        if count >= 100:
            break

    if count == 0:
        print("No new contacts to import.. exiting")
        return
    o.read_list("contacts")


if __name__ == "__main__":
    asoft_contacts = o.open_file("contacts_asoft")
    bukku_contacts = o.open_file("contacts_bukku")
    contacts_added = o.open_file("contacts_added")

    #bulk_update_contacts(asoft_contacts) #! KIV on updating contacts because TIN is not inside asoft
    bulk_create_contacts(asoft_contacts, contacts_added)
    #o.read_list("contacts")

    #code = "SAQL"
    #print(read_contact_by_code(code))
