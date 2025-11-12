import ops as o
import json
# ! Phase 2 - Core Import


def clean_prices(product):
    price_level_id = {
        "wholesale": 1,
        "retail": 2,
        "WMM1": 3,
        "NONG": 4,
        "50_Off": 5,
    }

    sale_prices = []
    if product["wholesale_price"] > 0:
        price = {
            "price_level_id": 1,
            "minimum_quantity": 0,
            "product_unit_id": 1,
            "currency_code": "MYR",
            "unit_price": product["wholesale_price"],
        }
        sale_prices.append(price)

    if product["retail_price"] > 0:
        price = {
            "price_level_id": 2,
            "minimum_quantity": 0,
            "product_unit_id": 1,
            "currency_code": "MYR",
            "unit_price": product["retail_price"],
        }
        sale_prices.append(price)

    if product["wmm1_price"] > 0:
        price = {
            "price_level_id": 3,
            "minimum_quantity": 0,
            "product_unit_id": 1,
            "currency_code": "MYR",
            "unit_price": product["wmm1_price"],
        }
        sale_prices.append(price)

    if product["nong_price"] > 0:
        price = {
            "price_level_id": 4,
            "minimum_quantity": 0,
            "product_unit_id": 1,
            "currency_code": "MYR",
            "unit_price": product["nong_price"],
        }
        sale_prices.append(price)

    if product["50_Off_price"] > 0:
        price = {
            "price_level_id": 5,
            "minimum_quantity": 0,
            "product_unit_id": 1,
            "currency_code": "MYR",
            "unit_price": product["50_Off_price"],
        }
        sale_prices.append(price)

    return sale_prices


def build_product_units_update(product_id):
    product = read_product(product_id)
    units = product["product"]["units"][0]
    return [{
        "id": units["id"],
        "label": units["label"],
        "rate": units["rate"],
        "sale_price": units["sale_price"],
        "purchase_price": units["purchase_price"],
    }]


def build_product_units_create(product):
    return [{
        "label": "unit",
        "rate": 1,
        "sale_price": product["dealer_price"],
        "purchase_price": product["purchase_price"],
        "is_base": "true",
        "is_sale_default": "true",
        "is_purchase_default": "true",
    }]


def build_product_params(product, units):
    sale_prices = clean_prices(product)

    # Assembling into params

    params = {
        "name": product["name"],
        "sku": product["sku"],
        "classification_code": product["classification_code"],
        "is_selling": "true",
        "sale_account_id": 20,
        "is_buying": "true",
        "purchase_account_id": 23,
        "track_inventory": "true",
        "inventory_account_id": 5,
        "group_ids": product["group_ids"],
        "bin_location": product.get("bin_location", None),
        "remarks": product["remark"],
        "units": units,
        "sale_prices": sale_prices,
    }
    if product["group"] in ["Non-stock", "Other"]:
        params["is_buying"] = "false"
        params["track_inventory"] = "false"

    return params


def create_product(params):
    sku = params['sku']
    path = "products"
    response = o.post_response(path, params)
    if "errors" in response:
        print(sku, "Error creating product:", response["errors"])

        if "sku" in response["errors"]:
            o.save_to_added_list(sku, "products")

        return False
    return True


def update_product(params, product_id):
    sku = params['sku']
    path = f"products/{product_id}"
    response = o.put_response(path, params)
    if "errors" in response:
        print(sku, "Error updating product:", response["errors"])
        return False
    return True


def read_product_list():
    sku = "E46938"
    path = "products"
    params = {
        # "page": 1,  # optional
        "page_size": 100,  # optional
        # "search": sku,  # optional # string
    }
    return o.get_response(path, params)


def read_product(product_id):
    path = f"products/{product_id}"
    params = {}
    return o.get_response(path, params)


def bulk_create_products(asoft_products, products_added):
    print("Importing products to Bukku...")
    count = 0
    for product in asoft_products:
        current_product = asoft_products[product]
        product_sku = asoft_products[product]["sku"]
        if o.check_doc_exists(product_sku, products_added):
            continue

        #! Skip some groups for testing
        #if "Roscani" not in current["group"]:
        #    continue

        units = build_product_units_create(current_product)
        params = build_product_params(current_product, units)
        created = create_product(params)
        if created:
            print("Product created:", product_sku)
            count += 1
            o.save_to_added_list(product_sku, "products")

        if count >= 150:
            break

    if count == 0:
        print("No new products to import.. exiting")
        return
    o.read_list("products")


def bulk_update_products(asoft_products):
    wallets = ["W0002", "W0003R", "W0004R"]
    products = o.open_file("products_bukku_ids")

    print("Updating products to Bukku...")
    count = 0
    for product in asoft_products:
        if product in wallets:
            continue

        product_sku = asoft_products[product]["sku"]
        product_id = products[product_sku]["id"]
        updated_on_asoft = asoft_products[product]["updated_on"]
        updated_on_bukku = products[product_sku]["updated_on"]

        # Skip products that has no changes
        if updated_on_bukku >= updated_on_asoft:
            continue

        units = build_product_units_update(product_id)
        params = build_product_params(asoft_products[product], units)
        updated = update_product(params, product_id)
        if updated:
            print("Product updated:", product_sku)
            count += 1

        if count >= 120:
            break

    if count == 0:
        print("No new products to update.. exiting")
        return
    o.read_list("products")


if __name__ == "__main__":
    asoft_products = o.open_file("products_asoft")
    products_added = o.open_file("products_added")

    bulk_create_products(asoft_products, products_added)
    bulk_update_products(asoft_products)
    #o.read_list("products")
    # create_contact()

    #product_id = "9575"
    #print(json.dumps(read_product(product_id), indent=2))
