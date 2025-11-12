import pyodbc
import ops as o

db_server = pyodbc.connect("DSN=JunLee_Asoft")
cursor = db_server.cursor()


# ! taking earlier than 12 days because reference can be earlier
def get_sam():
    print("Getting Supplier CN from asoft...")
    sql = f"""
    SELECT DOC_NO, DOC_DATE, CARD_ID, ADJ_TYPE, 
    INV_NO, INV_DATE, CARd_ID,
    CURR_ID, CURR_RATE, AMOUNT, AMOUNT_RM, REMARK, TAX_AMT
    FROM SAM
    WHERE DOC_DATE >= DATEADD(-30 DAY TO CURRENT_TIMESTAMP)
    AND ENTRY_TYPE = 'C'
    ORDER BY DOC_NO
    """

    cursor.execute(sql)
    rows = cursor.fetchall()
    sam = {}
    for row in rows:
        # Putting all together
        supp_credit_note = {
            "doc_no": row[0],
            "doc_date": o.convert_date(row[1]),
            "card_id": row[2],
            "adj_type": o.clean_doc_type(row[3]),
            "inv_no": row[4],
            "inv_date": o.convert_date(row[5]),
            "card_id": row[6],
            "currency_id": o.clean_currency_id(row[7]),
            "currency_rate": row[8],
            "amount": row[9],
            "amount_rm": row[10],
            "remark": row[11],
            "tax_amt": row[12],
        }
        sam[row[0]] = supp_credit_note
    o.save_file("pcm_asoft", sam)
    print(f"Total pcm: {len(sam)}")


def get_sad():
    sql = f"""
    SELECT SAD.SEQ_NO, ITEM_NO, STOCK_ID, SAD.REMARK, QTY, PRICE,
    TAX_RATE, SAD.TAX_AMT
    FROM SAD
    LEFT JOIN SAM ON SAD.SEQ_NO = SAM.DOC_NO
    WHERE SAM.DOC_DATE >= DATEADD(-30 DAY TO CURRENT_TIMESTAMP)
    AND ENTRY_TYPE = 'C'
    ORDER BY SAD.SEQ_NO
    """

    cursor.execute(sql)
    rows = cursor.fetchall()
    sad = {}
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
            "tax_rate": row[6],
            "tax_amt": row[7],
        }
        if doc_no not in sad:
            sad[doc_no] = []
        sad[doc_no].append(item)
    o.save_file("pcd_asoft", sad)
    print(f"Total pcd: {len(sad)}")


if __name__ == "__main__":
    get_sam()
    get_sad()
