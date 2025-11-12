import pyodbc
import ops as o

db_server = pyodbc.connect("DSN=JunLee_Asoft")
cursor = db_server.cursor()


# ! taking earlier than 12 days because reference can be earlier
def get_dom():
    print("Getting DO from asoft...")
    sql = f"""
    SELECT DOC_NO, DOC_DATE, CARD_ID, CURR_ID, CURR_RATE,
    STATUS, SM_ID, AMOUNT, AMOUNT_RM
    FROM DOM
    WHERE DOC_DATE >= DATEADD(-30 DAY TO CURRENT_TIMESTAMP)
    ORDER BY DOC_NO
    """

    cursor.execute(sql)
    rows = cursor.fetchall()
    dom = {}
    for row in rows:
        # Putting all together
        delivery_order = {
            "doc_no": row[0],
            "doc_date": o.convert_date(row[1]),
            "card_id": row[2],
            "currency_id": o.clean_currency_id(row[3]),
            "currency_rate": row[4],
            "status": row[5],
            "sm_id": o.clean_agent(row[6]),
            "amount": row[7],
            "amount_rm": row[8],
        }

        dom[row[0]] = delivery_order
    o.save_file("dom_asoft", dom)
    print(f"Total dom: {len(dom)}")


def get_dod():
    sql = f"""
    SELECT DOD.DOC_NO, ITEM_NO, STOCK_ID, DOD.REMARK, QTY, PRICE
    FROM DOD
    LEFT JOIN DOM ON DOD.DOC_NO = DOM.DOC_NO
    WHERE DOM.DOC_DATE >= DATEADD(-30 DAY TO CURRENT_TIMESTAMP)
    ORDER BY DOD.DOC_NO
    """

    cursor.execute(sql)
    rows = cursor.fetchall()
    dod = {}
    for row in rows:
        # Putting all together
        doc_no = row[0]
        item = {
            "doc_no": doc_no,
            "item_no": row[1],
            "stock_id": row[2],
            "remark": row[3],
            "qty": row[4],
            "price": row[5],
        }
        if doc_no not in dod:
            dod[doc_no] = []
        dod[doc_no].append(item)
    o.save_file("dod_asoft", dod)
    print(f"Total dod: {len(dod)}")


if __name__ == "__main__":
    get_dom()
    get_dod()
