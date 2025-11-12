import pyodbc
import ops as o

db_server = pyodbc.connect("DSN=JunLee_Asoft")
cursor = db_server.cursor()


def clean_card_id(card_id):
    if card_id in ["", None]:
        return "OPBL"
    return card_id


# ! Supplier Payment = Purchase Payment in Bukku
# ! taking earlier than 12 days because reference can be earlier
def get_spm():
    print("Getting Supplier Payments from asoft...")
    sql = f"""
    SELECT DOC_NO, DOC_DATE, CARD_ID, CURR_ID, CURR_RATE,
    ENTRY_TYPE, AMOUNT, AMOUNT_RM, CHEQUE_NO,
    APPL_AMT, APPL_AMT_RM, DISC_AMT, DISC_AMT_RM,
    BANK_CHARGES, BANK_CHARGES_RM, GL_DESC
    FROM SPM
    WHERE DOC_DATE >= DATEADD(-70 DAY TO CURRENT_TIMESTAMP)
    ORDER BY DOC_NO
    """

    cursor.execute(sql)
    rows = cursor.fetchall()
    spm = {}
    for row in rows:
        # Putting all together
        supplier_payment = {
            "doc_no": row[0],
            "doc_date": o.convert_date(row[1]),
            "card_id": clean_card_id(row[2]),
            "currency_id": o.clean_currency_id(row[3]),
            "currency_rate": row[4],
            "entry_type": row[5],
            "amount": row[6],
            "amount_rm": row[7],
            "cheque_no": row[8],
            "apply_amount": row[9],
            "apply_amount_rm": row[10],
            "discount_amount": row[11],
            "discount_amount_rm": row[12],
            "bank_charges": row[13],
            "bank_charges_rm": row[14],
            "gl_desc": row[15],
        }

        spm[row[0]] = supplier_payment
    o.save_file("ppm_asoft", spm)
    print(f"Total ppm: {len(spm)}")


def get_spd():
    sql = f"""
    SELECT SPD.DOC_NO, ITEM_NO, SPD.REMARK, 
    MATCH_DATE, MATCH_TYPE, MATCH_DOC,
    SPD.CURR_ID, SPD.CURR_RATE, SPD.AMOUNT, SPD.AMOUNT_RM,
    SPD.APPL_AMT, SPD.APPL_AMT_RM, SPD.DISC_AMT, SPD.DISC_AMT_RM
    FROM SPD
    LEFT JOIN SPM ON SPD.DOC_NO = SPM.DOC_NO
    WHERE SPM.DOC_DATE >= DATEADD(-70 DAY TO CURRENT_TIMESTAMP)
    ORDER BY SPD.DOC_NO
    """

    cursor.execute(sql)
    rows = cursor.fetchall()
    spd = {}
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
        if doc_no not in spd:
            spd[doc_no] = []
        spd[doc_no].append(item)
    o.save_file("ppd_asoft", spd)
    print(f"Total ppd: {len(spd)}")


if __name__ == "__main__":
    get_spm()
    get_spd()
