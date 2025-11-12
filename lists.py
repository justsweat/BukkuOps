import json
from ops import post_response, save_file
# ! Not in batch file

lists = [  #use this for reference
    "countries", "currencies", "contacts", "contact_addresses",
    "company_addresses", "contact_groups", "classification_code_list",
    "products", "product_list", "product", "product_groups", "accounts",
    "terms", "payment_methods", "price_levels", "tag_groups", "asset_types",
    "fields", "numberings", "form_designs", "locations", "stock_balances",
    "tax_codes", "settings", "limits", "users", "advisors", "state_list"
]


def get_lists(list):
    path = "v2/lists"
    params = {
        "lists": [list],  #! required
    }
    return post_response(path, params)


if __name__ == "__main__":
    list = "product_groups"  #TODO Change this to the desired list
    response = get_lists(list)
    if "errors" in response:
        print("Error:", response["errors"])
    else:
        save_file(list, response)
        print(f"{list} saved successfully.")
