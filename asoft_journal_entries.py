import pyodbc
import ops as o

db_server = pyodbc.connect("DSN=JunLee_Asoft")
cursor = db_server.cursor()


# ! taking earlier than 12 days because reference can be earlier
def get_jem():
    print("Getting journal entries from asoft...")
    sql = f"""
    SELECT DOC_NO, DOC_DATE, REMARK, TOTAL_DR, TOTAL_CR,
    TRX_NO, TRX_DATE
    FROM JEM
    WHERE DOC_DATE >= DATEADD(-60 DAY TO CURRENT_TIMESTAMP)
    ORDER BY DOC_NO
    """

    cursor.execute(sql)
    rows = cursor.fetchall()
    jem = {}
    for row in rows:
        # Putting all together
        journal_entry = {
            "doc_no": row[0],
            "doc_date": o.convert_date(row[1]),
            "remark": row[2],
            "total_dr": row[3],
            "total_cr": row[4],
            "trx_no": row[5],
            "trx_date": o.convert_date(row[6]),
        }

        jem[row[0]] = journal_entry
    o.save_file("jem_asoft", jem)
    print(f"Total jem: {len(jem)}")


def get_jed():
    sql = f"""
    SELECT JED.DOC_NO, ITEM_NO, GL_ACC, GL_DEPT, JED.REMARK, 
    DR_AMT, CR_AMT
    FROM JED
    LEFT JOIN JEM ON JED.DOC_NO = JEM.DOC_NO
    WHERE JEM.DOC_DATE >= DATEADD(-60 DAY TO CURRENT_TIMESTAMP)
    ORDER BY JED.DOC_NO
    """

    cursor.execute(sql)
    rows = cursor.fetchall()
    jed = {}
    for row in rows:
        # Putting all together
        doc_no = row[0]
        item = {
            "doc_no": doc_no,
            "item_no": row[1],
            "gl_acc": row[2],
            "gl_dept": row[3],
            "remark": row[4],
            "dr_amt": row[5],
            "cr_amt": row[6],
        }
        if doc_no not in jed:
            jed[doc_no] = []
        jed[doc_no].append(item)
    o.save_file("jed_asoft", jed)
    print(f"Total jed: {len(jed)}")


if __name__ == "__main__":
    get_jem()
    get_jed()
