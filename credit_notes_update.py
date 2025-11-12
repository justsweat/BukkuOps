import ops as o
from credit_note import read_credit_note
# ! Not in batch file


def remove_none(d):
    if isinstance(d, dict):
        return {k: remove_none(v) for k, v in d.items() if v is not None}
    elif isinstance(d, list):
        return [remove_none(x) for x in d]
    else:
        return d


def update_credit_note(cn_id):
    cn_raw = read_credit_note(cn_id)
    cn_item = cn_raw["transaction"]
    form_items = cn_item["form_items"]

    # Update all items to 022
    for item in form_items:
        item["classification_code"] = '022'

    path = f"sales/credit_notes/{cn_id}"
    params = remove_none(cn_item)

    # Post response
    response = o.put_response(path, params)

    # Handle Response
    if "message" in response:
        print(cn_item["number"], "Error updating credit note:",
              response["message"])
        print(params)
        return False

    if "errors" in response:
        print(cn_item["number"], "Error updating credit note:",
              response["errors"])
        return False
    return True


def bulk_update_credit_note(credit_notes, credit_notes_updated):
    count = 0
    for cn in credit_notes:
        cn_id = credit_notes[cn]["id"]

        if o.check_doc_exists(cn, credit_notes_updated):
            continue

        updated = update_credit_note(cn_id)
        if updated:
            print("Credit note updated", cn)
            o.save_to_added_list(cn, "credit_notes_updated")

        count += 1
        if count >= 3:
            break


if __name__ == "__main__":
    credit_notes = o.open_file("credit_notes_bukku_ids")
    credit_notes_updated = o.open_file("credit_notes_updated_added")

    bulk_update_credit_note(credit_notes, credit_notes_updated)

    #print(read_contact("882"))
