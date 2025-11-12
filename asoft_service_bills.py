import pyodbc
import ops as o

db_server = pyodbc.connect("DSN=JunLee_Asoft")
cursor = db_server.cursor()


def get_svm():
    print("Getting service bills from asoft...")
    sql = f"""
    SELECT DOC_NO, DOC_DATE, CARD_ID, CURR_ID, CURR_RATE, AMOUNT
    FROM SVCBILLM
    WHERE DOC_DATE >= DATEADD(-12 DAY TO CURRENT_TIMESTAMP)
    ORDER BY DOC_NO
    """

    cursor.execute(sql)
    rows = cursor.fetchall()
    svm = {}
    for row in rows:
        # Putting all together
        service_bill = {
            "doc_no": row[0],
            "doc_date": o.convert_date(row[1]),
            "card_id": row[2],
            "currency_id": o.clean_currency_id(row[3]),
            "currency_rate": row[4],
            "amount": row[5],
            "invoice_type": o.clean_doc_type("SVC"),
        }
        svm[row[0]] = service_bill
    o.save_file("svm_asoft", svm)
    print(f"Total svm: {len(svm)}")


def get_svd():
    sql = f"""
    SELECT d.DOC_NO, ITEM_NO, STOCK_ID, d.REMARK, QTY,
    d.AMOUNT, SERIAL_NO
    FROM SVCBILLD d
    LEFT JOIN SVCBILLM m ON d.DOC_NO = m.DOC_NO
    WHERE m.DOC_DATE >= DATEADD(-12 DAY TO CURRENT_TIMESTAMP)
    ORDER BY d.DOC_NO
    """

    cursor.execute(sql)
    rows = cursor.fetchall()
    svd = {}
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
            "serial_no": row[6],
        }
        if doc_no not in svd:
            svd[doc_no] = []
        svd[doc_no].append(item)
    o.save_file("svd_asoft", svd)
    print(f"Total svd: {len(svd)}")


if __name__ == "__main__":
    get_svm()
    get_svd()
