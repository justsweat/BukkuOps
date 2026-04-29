import ops as o
from contacts import read_contact


# ! Not in batch file
def update_contact_roles(contact_id, code):
    contact_res = read_contact(contact_id)
    if not contact_res or "contact" not in contact_res:
        print(code, "Failed to retrieve contact.")
        return False
        
    contact = contact_res["contact"]  
    
    # Add both roles if they don't already exist
    types = contact.get("types", [])
    if "customer" in types:
        types = ["customer", "supplier"]
        
    contact["types"] = types

    # updating deprecated attr
    if "display_name" in contact:
        contact["legal_name"] = contact["display_name"]
        del contact["display_name"]
    if "company_name" in contact:
        contact["other_name"] = contact["company_name"]
        del contact["company_name"]

    # Post response
    path = f"contacts/{contact_id}"
    response = o.put_response(path, contact)

    # Handle Response
    if "message" in response:
        print(code, "Error updating contact:", response["message"])
        return False

    if "errors" in response:
        print(code, "Error updating contact:", response["errors"])
        return False
        
    return True


def bulk_update_roles(bukku_contacts, contacts_updated):
    count = 0
    for key, contact_item in bukku_contacts.items():
        contact_id = str(contact_item["id"])
        
        # We try to use the code (other_name)
        code = contact_item.get("other_name") or key
        
        if o.check_doc_exists(code, contacts_updated):
            continue
            
        types = contact_item.get("types", [])
        if "supplier" in types and "customer" in types:
            # Already updated
            o.save_to_added_list(code, "contacts_roles_updated")
            continue

        updated = update_contact_roles(contact_id, code)
        if updated:
            print("Contact roles updated for:", code)
            o.save_to_added_list(code, "contacts_roles_updated")
            
        count += 1
        if count >= 30:
            print(len(contacts_updated))
            break


if __name__ == "__main__":
    bukku_contacts = o.open_file("contacts_bukku")
    contacts_updated = o.open_file("contacts_roles_updated_added")

    bulk_update_roles(bukku_contacts, contacts_updated)
