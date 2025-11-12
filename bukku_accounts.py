import ops as o
# ! Not in batch file


def read_account_list():
    ref = "5000"
    path = "accounts"
    params = {
        # "page": 1,  # optional
        # "page_size": 10,  # optional
        "search": ref,  # optional # string
    }
    return o.get_response(path, params)





if __name__ == "__main__":
    # bukku_accounts = read_account_list()
    pass
