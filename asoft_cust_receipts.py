import pyodbc
import ops as o

db_server = pyodbc.connect("DSN=JunLee_Asoft")
cursor = db_server.cursor()


# ! taking earlier than 12 days because reference can be earlier
def get_crm():
    print("Getting Customer Receipts from asoft...")
    sql = f"""
    SELECT DOC_NO, DOC_DATE, CARD_ID, CURR_ID, CURR_RATE,
    ENTRY_TYPE, AMOUNT, AMOUNT_RM, SM_ID, CHEQUE_NO,
    APPL_AMT, APPL_AMT_RM, DISC_AMT, DISC_AMT_RM,
    BANK_CHARGES, BANK_CHARGES_RM
    FROM CRM
    WHERE DOC_DATE >= DATEADD(-30 DAY TO CURRENT_TIMESTAMP)
    ORDER BY DOC_NO
    """

    cursor.execute(sql)
    rows = cursor.fetchall()
    crm = {}
    for row in rows:
        # Putting all together
        customer_receipt = {
            "doc_no": row[0],
            "doc_date": o.convert_date(row[1]),
            "card_id": row[2],
            "currency_id": o.clean_currency_id(row[3]),
            "currency_rate": row[4],
            "entry_type": row[5],
            "amount": row[6],
            "amount_rm": row[7],
            "sm_id": o.clean_agent(row[8]),
            "cheque_no": row[9],
            "apply_amount": row[10],
            "apply_amount_rm": row[11],
            "discount_amount": row[12],
            "discount_amount_rm": row[13],
            "bank_charges": row[14],
            "bank_charges_rm": row[15],
        }

        crm[row[0]] = customer_receipt
    o.save_file("cpm_asoft", crm)
    print(f"Total cpm: {len(crm)}")


def get_crd():
    sql = f"""
    SELECT CRD.DOC_NO, ITEM_NO, CRD.REMARK, 
    MATCH_DATE, MATCH_TYPE, MATCH_DOC,
    CRD.CURR_ID, CRD.CURR_RATE, CRD.AMOUNT, CRD.AMOUNT_RM,
    CRD.APPL_AMT, CRD.APPL_AMT_RM, CRD.DISC_AMT, CRD.DISC_AMT_RM
    FROM CRD
    LEFT JOIN CRM ON CRD.DOC_NO = CRM.DOC_NO
    WHERE CRM.DOC_DATE >= DATEADD(-30 DAY TO CURRENT_TIMESTAMP)
    ORDER BY CRD.DOC_NO
    """

    cursor.execute(sql)
    rows = cursor.fetchall()
    crd = {}
    for row in rows:
        # Putting all together
        doc_no = row[0]
        item = {
            "doc_no": doc_no,
            "item_no": row[1],
            "remark": row[2],
            "match_date": o.convert_date(row[3]),
            "match_type": row[4],
            "match_doc": row[5],
            "currency_id": o.clean_currency_id(row[6]),
            "currency_rate": row[7],
            "amount": row[8],
            "amount_rm": row[9],
            "apply_amount": row[10],
            "apply_amount_rm": row[11],
            "discount_amount": row[12],
            "discount_amount_rm": row[13],
        }
        if doc_no not in crd:
            crd[doc_no] = []
        crd[doc_no].append(item)
    o.save_file("cpd_asoft", crd)
    print(f"Total cpd: {len(crd)}")


if __name__ == "__main__":
    get_crm()
    get_crd()
