import os
import ops as o
import sys
import sqlite3
import csv
import logging
import time
from datetime import datetime, date, timedelta
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
INVOICES_ENDPOINT = f"{API_BASE_URL}/sales/invoices"
DB_FILE = "bukku.db"
EXPORT_DIR = r"\\storage\public\Data"
LOG_DIR = "log"
EXPORT_FILE = os.path.join(EXPORT_DIR, "bukku_invoices.csv")
LOG_FILE = os.path.join(LOG_DIR, "bukku_sync_log.txt")

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
    """Initializes SQLite database and creates invoices table if missing."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS invoices (
            id INTEGER PRIMARY KEY,
            number TEXT,
            number2 TEXT,
            date TEXT,
            contact_id INTEGER,
            contact_name TEXT,
            amount REAL,
            status TEXT,
            created_at TEXT,
            updated_at TEXT,
            myinvois_action TEXT,
            myinvois_document_uuid TEXT,
            myinvois_document_status TEXT,
            issued_at TEXT,
            validated_at TEXT,
            synced_at TEXT
        )
    ''')
    
    # Check if myinvois_action column already exists; if not, add it
    cursor.execute("PRAGMA table_info(invoices)")
    columns = [col[1] for col in cursor.fetchall()]
    if "myinvois_action" not in columns:
        logging.info("Adding 'myinvois_action' column to invoices table.")
        cursor.execute("ALTER TABLE invoices ADD COLUMN myinvois_action TEXT")
        
    conn.commit()
    return conn

def fetch_invoices_page(date_from, date_to, page=1, page_size=100):
    """Fetches a single page of invoices from Bukku API with retries."""
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Company-Subdomain": subdomain,
        "Accept": "application/json"
    }
    params = {
        "page": page,
        "page_size": page_size,
        "sort_by": "created_at",
        "sort_dir": "asc"
    }
    if date_from:
        params["date_from"] = date_from
    if date_to:
        params["date_to"] = date_to

    for attempt in range(1, 4):
        try:
            response = requests.get(INVOICES_ENDPOINT, headers=headers, params=params, timeout=30)
            response.raise_for_status()
            o.save_file("bukku_invoices.json", response.json())
            return response.json()
        except requests.exceptions.HTTPError as e:
            logging.error(f"HTTP Error on attempt {attempt}: {e.response.text}")
        except requests.exceptions.RequestException as e:
            logging.error(f"Network Error on attempt {attempt}: {e}")
        time.sleep(2 ** attempt)  # Exponential backoff
    
    raise Exception(f"Failed to fetch invoices from {date_from} to {date_to} on page {page} after 3 attempts.")

def upsert_invoices(conn, invoices):
    """Upserts invoices into SQLite using the UPSERT feature (SQLite 3.24.0+)."""
    if not invoices:
        return 0

    cursor = conn.cursor()
    synced_at = datetime.now().isoformat()
    
    upsert_sql = '''
        INSERT INTO invoices (
            id, number, number2, date, contact_id, contact_name, amount, status,
            created_at, updated_at, myinvois_action, myinvois_document_uuid, myinvois_document_status,
            issued_at, validated_at, synced_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
            number=excluded.number,
            number2=excluded.number2,
            date=excluded.date,
            contact_id=excluded.contact_id,
            contact_name=excluded.contact_name,
            amount=excluded.amount,
            status=excluded.status,
            created_at=excluded.created_at,
            updated_at=excluded.updated_at,
            myinvois_action=excluded.myinvois_action,
            myinvois_document_uuid=excluded.myinvois_document_uuid,
            myinvois_document_status=excluded.myinvois_document_status,
            issued_at=excluded.issued_at,
            validated_at=excluded.validated_at,
            synced_at=excluded.synced_at
    '''
    
    rows = []
    for inv in invoices:
        contact = inv.get("contact", {})
        contact_id = contact.get("id") if isinstance(contact, dict) else None
        contact_name = contact.get("name") if isinstance(contact, dict) else contact
        
        rows.append((
            inv.get("id"),
            inv.get("number"),
            inv.get("number2"),
            inv.get("date"),
            contact_id,
            contact_name,
            inv.get("amount"),
            inv.get("status"),
            inv.get("created_at"),
            inv.get("updated_at"),
            inv.get("myinvois_action"),
            inv.get("myinvois_document_uuid"),
            inv.get("myinvois_document_status"),
            inv.get("issued_at"),
            inv.get("validated_at"),
            synced_at
        ))
    cursor.executemany(upsert_sql, rows)
    conn.commit()
    return len(rows)

def sync_period(conn, date_from, date_to):
    """Fetches and syncs all invoices between date_from and date_to (handling pagination)."""
    page = 1
    total_synced = 0
    last_fetched_initial_time = None
    
    logging.info(f"Starting sync from {date_from} to {date_to}")
    
    while True:
        data = fetch_invoices_page(date_from, date_to, page=page)
        
        # Determine where invoices are within response JSON. 
        # Standard paginated REST API usually returns list in 'data' key or as the root.
        if isinstance(data, dict):
            invoices = data.get("transactions", data.get("data", []))
        elif isinstance(data, list):
            invoices = data
        else:
            raise Exception("Unexpected API response format.")
            
        if not invoices:
            break
            
        # Pagination safety: ensure no missing invoices if new invoices are created mid-sync
        # By comparing the first invoice created_at if sort_by=created_at and sort_dir=asc is used
        current_initial_time = invoices[0].get("created_at")
        if last_fetched_initial_time and current_initial_time == last_fetched_initial_time:
             # Possible page shift detected, but safe since we UPSERT. We just log it for awareness.
             logging.debug("Possible page shift detected during pagination.")
        last_fetched_initial_time = current_initial_time
        
        saved = upsert_invoices(conn, invoices)
        total_synced += saved
        logging.info(f"Synced {saved} invoices from page {page}")
        
        # Check if we've reached the end
        # Bukku API usually embeds pagination meta. If there's 'meta', we could use it, 
        # but safely we can just check if returned items < page_size.
        if len(invoices) < 100:
            break
            
        page += 1

    return total_synced

def full_backfill(conn):
    """Perform historical backfill monthly from Feb 2026 to today."""
    start_date = date(2025, 6, 1)
    end_date = date.today()
    
    current_start = start_date
    total_synced = 0
    
    while current_start <= end_date:
        # Calculate end of current month
        next_month = current_start.replace(day=28) + timedelta(days=4)
        current_end = next_month - timedelta(days=next_month.day)
        if current_end > end_date:
            current_end = end_date
            
        str_start = current_start.strftime("%Y-%m-%d")
        str_end = current_end.strftime("%Y-%m-%d")
        
        synced = sync_period(conn, str_start, str_end)
        total_synced += synced
        
        current_start = current_end + timedelta(days=1)
        
    logging.info(f"Full backfill completed. Total synced: {total_synced}")

def incremental_sync(conn):
    """Sync invoices since the last recorded date in DB, with a small overlap."""
    cursor = conn.cursor()
    cursor.execute("SELECT MAX(date) FROM invoices")
    max_date_str = cursor.fetchone()[0]
    
    date_to = date.today()
    if max_date_str:
        # Start from 10 days before the latest date found for safety
        base_date = datetime.strptime(max_date_str, "%Y-%m-%d").date()
        date_from = base_date - timedelta(days=10)
        logging.info(f"Incremental sync: Last invoice date in DB is {max_date_str}. Starting from {date_from}")
    else:
        date_from = date_to - timedelta(days=30)
        logging.info(f"Incremental sync: No records found. Starting from {date_from}")
    
    str_from = date_from.strftime("%Y-%m-%d")
    str_to = date_to.strftime("%Y-%m-%d")
    
    synced = sync_period(conn, str_from, str_to)
    logging.info(f"Incremental sync completed. Total synced: {synced}")

def export_to_csv(conn, days=None):
    """Exports invoices from the last X days to a CSV file. If days is None, exports all."""
    cursor = conn.cursor()
    
    if days:
        days_ago = (date.today() - timedelta(days=days)).strftime("%Y-%m-%d")
        query = '''
            SELECT id, number, number2, date, contact_id, contact_name, amount, status,
                   created_at, updated_at, myinvois_action, myinvois_document_uuid, myinvois_document_status,
                   issued_at, validated_at, synced_at
            FROM invoices
            WHERE date >= ?
            ORDER BY date DESC
        '''
        params = (days_ago,)
    else:
        query = '''
            SELECT id, number, number2, date, contact_id, contact_name, amount, status,
                   created_at, updated_at, myinvois_action, myinvois_document_uuid, myinvois_document_status,
                   issued_at, validated_at, synced_at
            FROM invoices
            ORDER BY date DESC
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
            
        logging.info(f"Successfully exported {len(rows)} invoices to {EXPORT_FILE}")
    except Exception as e:
        logging.error(f"Failed to export CSV: {e}")

def main():
    logging.info("--- Bukku Sync Started ---")
    try:
        conn = init_db()
        cursor = conn.cursor()
        
        # Check if database is populated to decide between backfill or incremental
        cursor.execute("SELECT COUNT(*) FROM invoices")
        count = cursor.fetchone()[0]
        
        force_backfill = False

        if force_backfill == True:
            logging.info("Force backfill enabled. Initiating historical backfill.")
            full_backfill(conn)
        elif count == 0:
            logging.info("Database is empty. Initiating historical backfill.")
            full_backfill(conn)
        else:
            logging.info(f"Database has {count} records. Initiating incremental sync.")
            incremental_sync(conn)
            
        export_to_csv(conn, days=None)
        
    except Exception as e:
        logging.error(f"An error occurred during sync: {e}")
        logging.error(traceback.format_exc())
    finally:
        if 'conn' in locals() and conn:
            conn.close()
            
    logging.info("--- Bukku Sync Finished ---")

if __name__ == "__main__":
    main()
