import pyodbc
import re
import ops as o
import fdb

db_server = pyodbc.connect("DSN=JunLee_Asoft")
cursor = db_server.cursor()


def get_entity_type(country):
    replacements = {
        "MALAYSIA": "MALAYSIAN_COMPANY",
        "SINGAPORE": "FOREIGN_COMPANY",
        "BRUNEI": "FOREIGN_COMPANY",
        "HONG KONG": "FOREIGN_COMPANY",
        "INDONESIA": "FOREIGN_COMPANY",
        "SWITZERLAND": "FOREIGN_COMPANY",
        "CHINA": "FOREIGN_COMPANY",
    }
    return replacements.get(country, "MALAYSIAN_COMPANY")


def clean_contact(contact):
    if contact in ["", None]:
        return "Mr"
    return contact


def clean_country(country):
    replacements = {
        "MALAYSIA": "MY",
        "SINGAPORE": "SG",
        "BRUNEI": "BN",
        "HONG KONG": "HK",
        "INDONESIA": "ID",
        "SWITZERLAND": "CH",
        "CHINA": "CN"
    }
    return replacements.get(country, country)


def clean_state(state):
    state = state.title()
    replacements = {
        "N.Sembilan": "Negeri Sembilan",
        "Penang": "Pulau Pinang",
        "Kuala Lumpur": "Wilayah Persekutuan Kuala Lumpur",
        "Labuan": "Wilayah Persekutuan Labuan",
    }
    return replacements.get(state, state)


def clean_address(address):
    """Clean the address by removing None values and joining with commas."""
    if address in ["", None]:
        return False

    raw = [part for part in address if part != ""]

    cleaned_parts = []
    for part in raw:
        if re.match(r"^\d{5}\b", part.strip()):
            break
        cleaned_parts.append(part)

    joined = " ".join(cleaned_parts).strip(", ")
    return joined


def get_customer():
    print("Getting customers from asoft...")
    sql = """
    SELECT CODE, NAME, ADDR1, ADDR2, ADDR3,
    ADDR4, WEBSITE, POSTCODE, STATE, COUNTRY,
    TERRITORY, TEL1, CONTACT1, SM_ID, REMARK, 
    CARD_TYPE, STATUS, DATE_ADD
    FROM CARD c
    WHERE STATUS IN ('A', 'C')
    AND c.CARD_TYPE IN ('B', 'C', 'S')
    ORDER BY CODE
    """

    cursor.execute(sql)
    rows = cursor.fetchall()

    customers = {}
    count = 0
    for row in rows:
        address = clean_address([row[2], row[3], row[4], row[5]])
        phone_num = o.clean_phone(row[11])
        state = clean_state(row[8])
        country = clean_country(row[9])
        contact = clean_contact(row[12])
        agent = o.clean_agent(row[13])
        entity_type = get_entity_type(row[9])
        contact_type = row[15]

        customer = {
            "code": row[0],
            "name": row[1],
            "city": row[6],
            "postcode": row[7],
            "state": state,
            "country": country,
            "territory": row[10],
            "phone_num": phone_num,
            "contact": contact,
            "agent": agent,
            "remark": row[14],
            "entity_type": entity_type,
            "contact_type": contact_type,
            "status": row[16],
            "updated_on": o.convert_date(row[17]),
        }
        if address:
            customer["address"] = address

        customers[row[0]] = customer
        count += 1
    o.save_file("contacts_asoft", customers)
    print(f"Total customers: {count}")


if __name__ == "__main__":
    get_customer()
