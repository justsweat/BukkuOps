import json
import ops as o
# ! not in batch file


def delete_product(product_id):
    path = f"products/{product_id}"
    response = o.delete_response(path)
    return response


if __name__ == "__main__":
    with open("products_bukku.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    products = data["products"]
    for product in products:
        if "ARRIXON" in product["name"]:
            response = delete_product(product["id"])
            print(product["name"], "deleted")
