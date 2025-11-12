import pyodbc
import ops as o

db_server = pyodbc.connect("DSN=JunLee_Asoft")
cursor = db_server.cursor()


# ! taking earlier than 12 days because reference can be earlier
def get_grm():
    print("Getting Goods Received from asoft...")
    sql = f"""
    SELECT DOC_NO, DOC_DATE, CARD_ID, CURR_ID, CURR_RATE,
    STATUS, AMOUNT, AMOUNT_RM, REMARK, DOC_TYPE, REF_DO,
    REF_DODATE, FREIGHT, HANDLING, DUTY
    FROM GRM
    WHERE DOC_DATE >= '1-Jan-2025'
    ORDER BY DOC_NO
    """

    cursor.execute(sql)
    rows = cursor.fetchall()
    grm = {}
    for row in rows:
        # Putting all together
        goods_received = {
            "doc_no": row[0],
            "doc_date": o.convert_date(row[1]),
            "card_id": row[2],
            "currency_id": o.clean_currency_id(row[3]),
            "currency_rate": row[4],
            "status": row[5],
            "amount": row[6],
            "amount_rm": row[7],
            "remark": row[8],
            "doc_type": row[9],
            "ref_do": row[10],
            "ref_dodate": o.convert_date(row[11]),
            "freight": row[12],
            "handling": row[13],
            "duty": row[14],
        }

        grm[row[0]] = goods_received
    o.save_file("grm_asoft", grm)
    print(f"Total grm: {len(grm)}")


def get_grd():
    sql = f"""
    SELECT GRD.DOC_NO, ITEM_NO, PO_NO, PO_ITEMNO, STOCK_ID,
    GRD.REMARK, QTY, BAL_QTY, BAL_AMT, COST, PRICE,
    TARRIF, DUTY_RATE, GRD.DUTY, SAL_RATE, GRD.SAL_TAX,
    GRD.FREIGHT
    FROM GRD
    LEFT JOIN GRM ON GRD.DOC_NO = GRM.DOC_NO
    WHERE GRM.DOC_DATE >= '1-Jan-2025'
    ORDER BY GRD.DOC_NO
    """

    cursor.execute(sql)
    rows = cursor.fetchall()
    grd = {}
    for row in rows:
        # Putting all together
        doc_no = row[0]
        item = {
            "doc_no": doc_no,
            "item_no": row[1],
            "po_no": row[2],
            "po_itemno": row[3],
            "stock_id": row[4],
            "remark": o.clean_remark(row[5]),
            "qty": row[6],
            "bal_qty": row[7],
            "bal_amt": row[8],
            "cost": row[9],
            "price": row[10],
            "tarrif": row[11],
            "duty_rate": row[12],
            "duty": row[13],
            "sal_rate": row[14],
            "sal_tax": row[15],
            "freight": row[16],
        }
        if doc_no not in grd:
            grd[doc_no] = []
        grd[doc_no].append(item)
    o.save_file("grd_asoft", grd)
    print(f"Total grd: {len(grd)}")


if __name__ == "__main__":
    get_grm()
    get_grd()
