import pyodbc
import ops as o

db_server = pyodbc.connect("DSN=JunLee_Asoft")
cursor = db_server.cursor()


# ! taking earlier than 12 days because reference can be earlier
def get_cam():
    print("Getting DN from asoft...")
    sql = f"""
    SELECT DOC_NO, DOC_DATE, CARD_ID, ADJ_TYPE, SM_ID,
    CURR_ID, CURR_RATE, AMOUNT, AMOUNT_RM, REMARK
    FROM CAM
    WHERE DOC_DATE >= DATEADD(-90 DAY TO CURRENT_TIMESTAMP)
    AND ENTRY_TYPE = 'D'
    ORDER BY DOC_NO
    """

    cursor.execute(sql)
    rows = cursor.fetchall()
    cam = {}
    for row in rows:
        # Putting all together
        purchase_order = {
            "doc_no": row[0],
            "doc_date": o.convert_date(row[1]),
            "card_id": row[2],
            "adj_type": o.clean_doc_type(row[3]),
            "sm_id": o.clean_agent(row[4]),
            "currency_id": o.clean_currency_id(row[5]),
            "currency_rate": row[6],
            "amount": row[7],
            "amount_rm": row[8],
            "remark": row[9],
            "invoice_type": 6  #INV
        }
        cam[row[0]] = purchase_order
    o.save_file("dnm_asoft", cam)
    print(f"Total dnm: {len(cam)}")


def get_cad():
    sql = f"""
    SELECT CAD.DOC_NO, ITEM_NO, STOCK_ID, CAD.REMARK, QTY, PRICE
    FROM CAD
    LEFT JOIN CAM ON CAD.DOC_NO = CAM.DOC_NO
    WHERE CAM.DOC_DATE >= DATEADD(-90 DAY TO CURRENT_TIMESTAMP)
    AND ENTRY_TYPE = 'D'
    ORDER BY CAD.DOC_NO
    """

    cursor.execute(sql)
    rows = cursor.fetchall()
    cad = {}
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
        if doc_no not in cad:
            cad[doc_no] = []
        cad[doc_no].append(item)
    o.save_file("dnd_asoft", cad)
    print(f"Total dnd: {len(cad)}")


if __name__ == "__main__":
    get_cam()
    get_cad()
