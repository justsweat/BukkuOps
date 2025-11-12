import pyodbc
import ops as o

db_server = pyodbc.connect("DSN=JunLee_Asoft")
cursor = db_server.cursor()


# ! converts to Purchase Bill in Bukku
# ! taking at the start of this year
def get_sim():
    print("Getting Supplier Invoices from asoft...")
    sql = f"""
    SELECT SEQ_NO, DOC_NO, DOC_DATE, CARD_ID, INV_TYPE,
    CURR_ID, CURR_RATE, AMOUNT, AMOUNT_RM, REMARK, IMPORT_REF
    FROM SIM
    WHERE DOC_DATE >= '1-Jan-2025'
    ORDER BY DOC_NO
    """

    cursor.execute(sql)
    rows = cursor.fetchall()
    sim = {}
    for row in rows:
        # Putting all together
        supplier_invoice = {
            "seq_no": row[0],
            "doc_no": row[1],
            "doc_date": o.convert_date(row[2]),
            "card_id": row[3],
            "inv_type": o.clean_doc_type(row[4]),
            "currency_id": o.clean_currency_id(row[5]),
            "currency_rate": row[6],
            "amount": row[7],
            "amount_rm": row[8],
            "remark": row[9],
            "import_ref": row[10],
        }

        sim[row[0]] = supplier_invoice
    o.save_file("pbm_asoft", sim)
    print(f"Total pbm: {len(sim)}")


def get_sid():
    sql = f"""
    SELECT SID.SEQ_NO, ITEM_NO, 
    STOCK_ID, SID.REMARK, QTY, PRICE, 
    GR_NO, GR_ITEMNO, REF_DO
    FROM SID
    LEFT JOIN SIM ON SID.SEQ_NO = SIM.SEQ_NO
    WHERE SIM.DOC_DATE >= '1-Jan-2025'
    ORDER BY SID.SEQ_NO
    """

    cursor.execute(sql)
    rows = cursor.fetchall()
    sid = {}
    for row in rows:
        # Putting all together
        seq_no = row[0]
        item = {
            "seq_no": seq_no,
            "item_no": row[1],
            "stock_id": row[2],
            "remark": row[3],
            "qty": row[4],
            "price": row[5],
            "gr_no": row[6],
            "gr_itemno": row[7],
            "ref_do": row[8],
        }
        if seq_no not in sid:
            sid[seq_no] = []
        sid[seq_no].append(item)
    o.save_file("pbd_asoft", sid)
    print(f"Total pbd: {len(sid)}")


if __name__ == "__main__":
    get_sim()
    get_sid()
