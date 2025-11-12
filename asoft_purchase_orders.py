import pyodbc
import ops as o

db_server = pyodbc.connect("DSN=JunLee_Asoft")
cursor = db_server.cursor()


# ! taking earlier than 12 days because reference can be earlier
def get_pom():
    print("Getting purchase orders from asoft...")
    sql = f"""
    SELECT DOC_NO, DOC_DATE, CARD_ID, CURR_ID, CURR_RATE,
    STATUS, AMOUNT, AMOUNT_RM, REMARK
    FROM POM
    WHERE DOC_DATE >= '1-Jan-2025'
    ORDER BY DOC_NO
    """

    cursor.execute(sql)
    rows = cursor.fetchall()
    pom = {}
    for row in rows:
        # Putting all together
        purchase_order = {
            "doc_no": row[0],
            "doc_date": o.convert_date(row[1]),
            "card_id": row[2],
            "currency_id": o.clean_currency_id(row[3]),
            "currency_rate": row[4],
            "status": row[5],
            "amount": row[6],
            "amount_rm": row[7],
            "remark": row[8],
        }

        pom[row[0]] = purchase_order
    o.save_file("pom_asoft", pom)
    print(f"Total pom: {len(pom)}")


def get_pod():
    sql = f"""
    SELECT POD.DOC_NO, ITEM_NO, STOCK_ID, POD.REMARK, QTY, PRICE
    FROM POD
    LEFT JOIN POM ON POD.DOC_NO = POM.DOC_NO
    WHERE POM.DOC_DATE >= '1-Jan-2025'
    ORDER BY POD.DOC_NO
    """

    cursor.execute(sql)
    rows = cursor.fetchall()
    pod = {}
    for row in rows:
        # Putting all together
        doc_no = row[0]
        item = {
            "doc_no": doc_no,
            "item_no": row[1],
            "stock_id": row[2],
            "remark": o.clean_remark(row[3]),
            "qty": row[4],
            "price": row[5],
        }
        if doc_no not in pod:
            pod[doc_no] = []
        pod[doc_no].append(item)
    o.save_file("pod_asoft", pod)
    print(f"Total pod: {len(pod)}")


if __name__ == "__main__":
    get_pom()
    get_pod()
