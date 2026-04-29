import os
import ops as o
import sys
import sqlite3
import csv
import logging
import time
from datetime import datetime
import traceback
import requests

# Set working directory to the script's directory for Task Scheduler
script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_dir)

# Import credentials (expecting api_key and subdomain)
try:
    import cred
    api_key = cred.api_key
    subdomain = cred.subdomain
except ImportError:
    print("Error: Could not import cred.py. Ensure cred.py exists with api_key and subdomain.")
    sys.exit(1)
except AttributeError:
    print("Error: cred.py must define 'api_key' and 'subdomain' variables.")
    sys.exit(1)

# Configurations
API_BASE_URL = "https://api.bukku.my"
CONTACTS_ENDPOINT = f"{API_BASE_URL}/contacts"
DB_FILE = "bukku.db"
EXPORT_DIR = r"\\storage\public\Data"
LOG_DIR = "log"
EXPORT_FILE = os.path.join(EXPORT_DIR, "bukku_contacts.csv")
LOG_FILE = os.path.join(LOG_DIR, "bukku_sync_contacts_log.txt")

# Setup directories
os.makedirs(EXPORT_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE, encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

def init_db():
    """Initializes SQLite database and creates contacts table if missing."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS contacts (
            id INTEGER PRIMARY KEY,
            legal_name TEXT,
            other_name TEXT,
            display_name TEXT,
            company_name TEXT,
            reg_no TEXT,
            old_reg_no TEXT,
            tax_id_no TEXT,
            entity_type TEXT,
            phone_no TEXT,
            email TEXT,
            types TEXT,
            group_names TEXT,
            created_at TEXT,
            updated_at TEXT,
            synced_at TEXT
        )
    ''')
    conn.commit()
    return conn

def fetch_contacts_page(page=1, page_size=100):
    """Fetches a single page of contacts from Bukku API with retries."""
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Company-Subdomain": subdomain,
        "Accept": "application/json"
    }
    params = {
        "page": page,
        "page_size": page_size,
    }

    for attempt in range(1, 4):
        try:
            response = requests.get(CONTACTS_ENDPOINT, headers=headers, params=params, timeout=30)
            response.raise_for_status()
            o.save_file("bukku_contacts.json", response.json())
            return response.json()
        except requests.exceptions.HTTPError as e:
            logging.error(f"HTTP Error on attempt {attempt}: {e.response.text}")
        except requests.exceptions.RequestException as e:
            logging.error(f"Network Error on attempt {attempt}: {e}")
        time.sleep(2 ** attempt)  # Exponential backoff
    
    raise Exception(f"Failed to fetch contacts on page {page} after 3 attempts.")

def upsert_contacts(conn, contacts):
    """Upserts contacts into SQLite using the UPSERT feature (SQLite 3.24.0+)."""
    if not contacts:
        return 0

    cursor = conn.cursor()
    synced_at = datetime.now().isoformat()
    
    upsert_sql = '''
        INSERT INTO contacts (
            id, legal_name, other_name, display_name, company_name, reg_no, 
            old_reg_no, tax_id_no, entity_type, phone_no, email, 
            types, group_names, created_at, updated_at, synced_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
            legal_name=excluded.legal_name,
            other_name=excluded.other_name,
            display_name=excluded.display_name,
            company_name=excluded.company_name,
            reg_no=excluded.reg_no,
            old_reg_no=excluded.old_reg_no,
            tax_id_no=excluded.tax_id_no,
            entity_type=excluded.entity_type,
            phone_no=excluded.phone_no,
            email=excluded.email,
            types=excluded.types,
            group_names=excluded.group_names,
            created_at=excluded.created_at,
            updated_at=excluded.updated_at,
            synced_at=excluded.synced_at
    '''
    
    rows = []
    for c in contacts:
        # types and group_names are lists, we join them as comma separated strings
        types_str = ",".join(c.get("types") or [])
        group_names_str = ",".join(c.get("group_names") or [])
        
        rows.append((
            c.get("id"),
            c.get("legal_name"),
            c.get("other_name"),
            c.get("display_name"),
            c.get("company_name"),
            c.get("reg_no"),
            c.get("old_reg_no"),
            c.get("tax_id_no"),
            c.get("entity_type"),
            c.get("phone_no"),
            c.get("email"),
            types_str,
            group_names_str,
            c.get("created_at"),
            c.get("updated_at"),
            synced_at
        ))
    cursor.executemany(upsert_sql, rows)
    conn.commit()
    return len(rows)

def full_sync(conn):
    """Fetches and syncs all contacts (handling pagination)."""
    page = 1
    total_synced = 0
    
    logging.info(f"Starting full contacts sync")
    
    while True:
        data = fetch_contacts_page(page=page)
        
        if isinstance(data, dict):
            contacts = data.get("contacts", [])
        elif isinstance(data, list):
            contacts = data
        else:
            raise Exception("Unexpected API response format.")
            
        if not contacts:
            break
            
        saved = upsert_contacts(conn, contacts)
        total_synced += saved
        logging.info(f"Synced {saved} contacts from page {page}")
        
        if len(contacts) < 100:
            break
            
        page += 1

    logging.info(f"Full sync completed. Total synced: {total_synced}")
    return total_synced

def export_to_csv(conn):
    """Exports contacts to a CSV file."""
    cursor = conn.cursor()
    
    query = '''
        SELECT id, legal_name, other_name, display_name, company_name, reg_no, 
               old_reg_no, tax_id_no, entity_type, phone_no, email, 
               types, group_names, created_at, updated_at, synced_at
        FROM contacts
        ORDER BY legal_name ASC
    '''
    params = ()

    cursor.execute(query, params)
    
    rows = cursor.fetchall()
    headers = [description[0] for description in cursor.description]
    
    try:
        # Generate CSV with UTF-8 BOM so Excel opens it with proper encoding automatically
        with open(EXPORT_FILE, mode='w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            writer.writerow(headers)
            writer.writerows(rows)
            
        logging.info(f"Successfully exported {len(rows)} contacts to {EXPORT_FILE}")
    except Exception as e:
        logging.error(f"Failed to export CSV: {e}")

def main():
    logging.info("--- Bukku Contacts Sync Started ---")
    try:
        conn = init_db()
        
        # We perform a full sync for contacts as they are typically low in volume
        full_sync(conn)

        # Export to CSV
        export_to_csv(conn)
        
    except Exception as e:
        logging.error(f"An error occurred during sync: {e}")
        logging.error(traceback.format_exc())
    finally:
        if 'conn' in locals() and conn:
            conn.close()
            
    logging.info("--- Bukku Contacts Sync Finished ---")

if __name__ == "__main__":
    main()
