import pyodbc
import ops as o

db_server = pyodbc.connect("DSN=JunLee_Asoft")
cursor = db_server.cursor()


def get_cim():
    print("Getting invoices from asoft...")
    sql = f"""
    SELECT DOC_NO, DOC_DATE, CARD_ID, ENTRY_TYPE, INV_TYPE,
    REF_PO, CURR_ID, CURR_RATE, SM_ID, AMOUNT, AMOUNT_RM,
    DATE_ADD
    FROM CIM
    WHERE DOC_DATE >= DATEADD(-12 DAY TO CURRENT_TIMESTAMP)
    ORDER BY DOC_NO
    """

    cursor.execute(sql)
    rows = cursor.fetchall()
    cim = {}
    for row in rows:
        # Putting all together
        invoice = {
            "doc_no": row[0],
            "doc_date": o.convert_date(row[1]),
            "card_id": row[2],
            "entry_type": row[3],
            "invoice_type": o.clean_doc_type(row[4]),
            "ref_po": row[5],
            "currency_id": o.clean_currency_id(row[6]),
            "currency_rate": row[7],
            "sm_id": o.clean_agent(row[8]),
            "amount": row[9],
            "amount_rm": row[10],
        }

        cim[row[0]] = invoice
    o.save_file("ivm_asoft", cim)
    print(f"Total ivm: {len(cim)}")


def get_cid():
    sql = f"""
    SELECT CID.DOC_NO, ITEM_NO, STOCk_ID, CID.REMARK, QTY,
    PRICE, SO_NO, SO_ITEMNO, DO_NO, DO_ITEMNO, CID.DISC_AMT
    FROM CID
    LEFT JOIN CIM ON CID.DOC_NO = CIM.DOC_NO
    WHERE CIM.DOC_DATE >= DATEADD(-12 DAY TO CURRENT_TIMESTAMP)
    ORDER BY CID.DOC_NO
    """

    cursor.execute(sql)
    rows = cursor.fetchall()
    cid = {}
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
            "so_no": row[6],
            "so_itemno": row[7],
            "do_no": row[8],
            "do_itemno": row[9],
            "disc_amt": str(row[10]),
        }
        if doc_no not in cid:
            cid[doc_no] = []
        cid[doc_no].append(item)
    o.save_file("ivd_asoft", cid)
    print(f"Total ivd: {len(cid)}")


if __name__ == "__main__":
    get_cim()
    get_cid()
