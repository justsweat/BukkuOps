import pyodbc
import ops as o

db_server = pyodbc.connect("DSN=JunLee_Asoft")
cursor = db_server.cursor()


# ! taking earlier than 12 days because reference can be earlier
def get_som():
    print("Getting sales orders from asoft...")
    sql = f"""
    SELECT DOC_NO, DOC_DATE, CARD_ID, CURR_ID, CURR_RATE,
    STATUS, SM_ID, AMOUNT, AMOUNT_RM, DATE_ADD
    FROM SOM
    WHERE DOC_DATE >= DATEADD(-50 DAY TO CURRENT_TIMESTAMP)
    ORDER BY DOC_NO
    """

    cursor.execute(sql)
    rows = cursor.fetchall()
    som = {}
    for row in rows:
        # Putting all together
        sales_order = {
            "doc_no": row[0],
            "doc_date": o.convert_date(row[1]),
            "card_id": row[2],
            "currency_id": o.clean_currency_id(row[3]),
            "currency_rate": row[4],
            "status": row[5],
            "sm_id": o.clean_agent(row[6]),
            "amount": row[7],
            "amount_rm": row[8],
            "updated_on": o.convert_date(row[9]),
        }

        som[row[0]] = sales_order
    o.save_file("som_asoft", som)
    print(f"Total som: {len(som)}")


def get_sod():
    sql = f"""
    SELECT SOD.DOC_NO, ITEM_NO, STOCK_ID, SOD.REMARK, QTY, PRICE, SOD.DISC_AMT 
    FROM SOD
    LEFT JOIN SOM ON SOD.DOC_NO = SOM.DOC_NO
    WHERE SOM.DOC_DATE >= DATEADD(-50 DAY TO CURRENT_TIMESTAMP)
    ORDER BY SOD.DOC_NO
    """

    cursor.execute(sql)
    rows = cursor.fetchall()
    sod = {}
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
            "disc_amt": str(row[6]),
        }
        if doc_no not in sod:
            sod[doc_no] = []
        sod[doc_no].append(item)
    o.save_file("sod_asoft", sod)
    print(f"Total sod: {len(sod)}")


if __name__ == "__main__":
    get_som()
    get_sod()
