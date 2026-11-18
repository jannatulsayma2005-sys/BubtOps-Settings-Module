import os
import sqlite3
import hashlib
import secrets
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "bubt_ops.db")

def connect_db():
    return sqlite3.connect(DB_PATH)

def create_tables():
    with connect_db() as con:
        cur = con.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS assets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                asset_id TEXT UNIQUE NOT NULL,
                asset_name TEXT NOT NULL,
                category TEXT NOT NULL,
                quantity INTEGER NOT NULL DEFAULT 1,
                location TEXT,
                status TEXT DEFAULT 'Available',
                description TEXT,
                created_at TEXT NOT NULL
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS app_settings (
                setting_key TEXT PRIMARY KEY,
                setting_value TEXT
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS admin (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                admin_name TEXT NOT NULL,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT,
                password_salt TEXT
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS asset_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                asset_id TEXT NOT NULL,
                asset_name TEXT NOT NULL,
                action_type TEXT NOT NULL,
                previous_info TEXT,
                updated_info TEXT,
                performed_by TEXT,
                action_time TEXT NOT NULL
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS backup_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_path TEXT NOT NULL,
                backup_time TEXT NOT NULL
            )
        """)
        defaults = {
            "application_name": "BUBT-OPS",
            "language": "English",
            "date_format": "DD-MM-YYYY",
            "default_dashboard": "Dashboard",
            "theme": "Light",
            "font_size": "10",
        }
        for key, value in defaults.items():
            cur.execute("INSERT OR IGNORE INTO app_settings VALUES (?, ?)", (key, value))
        cur.execute("""
            INSERT OR IGNORE INTO admin
            (id, admin_name, username, password_hash, password_salt)
            VALUES (1, 'Administrator', 'admin', '', '')
        """)
        con.commit()

def get_setting(key, default=""):
    with connect_db() as con:
        row = con.execute("SELECT setting_value FROM app_settings WHERE setting_key=?", (key,)).fetchone()
    return row[0] if row else default

def save_setting(key, value):
    with connect_db() as con:
        con.execute("""
            INSERT INTO app_settings(setting_key, setting_value) VALUES (?, ?)
            ON CONFLICT(setting_key) DO UPDATE SET setting_value=excluded.setting_value
        """, (key, str(value)))
        con.commit()

def get_admin():
    with connect_db() as con:
        return con.execute("SELECT admin_name, username, password_hash, password_salt FROM admin WHERE id=1").fetchone()

def update_admin(admin_name, username):
    with connect_db() as con:
        con.execute("UPDATE admin SET admin_name=?, username=? WHERE id=1", (admin_name, username))
        con.commit()

def set_password(password):
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 200_000).hex()
    with connect_db() as con:
        con.execute("UPDATE admin SET password_hash=?, password_salt=? WHERE id=1", (digest, salt))
        con.commit()

def verify_password(password):
    row = get_admin()
    if not row or not row[2] or not row[3]:
        return False
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), row[3].encode("utf-8"), 200_000).hex()
    return secrets.compare_digest(digest, row[2])

def asset_info(values):
    return " | ".join(f"{k}: {v}" for k, v in values.items())

def add_asset(asset_id, asset_name, category, quantity, location, status, description, performed_by="Admin"):
    created = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    data = {
        "Asset ID": asset_id, "Asset Name": asset_name, "Category": category,
        "Quantity": quantity, "Location": location, "Status": status,
        "Description": description
    }
    with connect_db() as con:
        con.execute("""
            INSERT INTO assets(asset_id, asset_name, category, quantity, location, status, description, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (asset_id, asset_name, category, quantity, location, status, description, created))
        con.execute("""
            INSERT INTO asset_history
            (asset_id, asset_name, action_type, previous_info, updated_info, performed_by, action_time)
            VALUES (?, ?, 'Added', '', ?, ?, ?)
        """, (asset_id, asset_name, asset_info(data), performed_by, created))
        con.commit()

def update_asset(asset_id, asset_name, category, quantity, location, status, description, performed_by="Admin"):
    with connect_db() as con:
        old = con.execute("""
            SELECT asset_name, category, quantity, location, status, description
            FROM assets WHERE asset_id=?
        """, (asset_id,)).fetchone()
        if not old:
            raise ValueError("Asset ID was not found.")
        previous = {
            "Asset Name": old[0], "Category": old[1], "Quantity": old[2],
            "Location": old[3], "Status": old[4], "Description": old[5]
        }
        updated = {
            "Asset Name": asset_name, "Category": category, "Quantity": quantity,
            "Location": location, "Status": status, "Description": description
        }
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        con.execute("""
            UPDATE assets SET asset_name=?, category=?, quantity=?, location=?, status=?, description=?
            WHERE asset_id=?
        """, (asset_name, category, quantity, location, status, description, asset_id))
        con.execute("""
            INSERT INTO asset_history
            (asset_id, asset_name, action_type, previous_info, updated_info, performed_by, action_time)
            VALUES (?, ?, 'Updated', ?, ?, ?, ?)
        """, (asset_id, asset_name, asset_info(previous), asset_info(updated), performed_by, now))
        con.commit()

def delete_asset(asset_id, performed_by="Admin"):
    with connect_db() as con:
        row = con.execute("""
            SELECT asset_name, category, quantity, location, status, description
            FROM assets WHERE asset_id=?
        """, (asset_id,)).fetchone()
        if not row:
            raise ValueError("Asset ID was not found.")
        info = {
            "Asset Name": row[0], "Category": row[1], "Quantity": row[2],
            "Location": row[3], "Status": row[4], "Description": row[5]
        }
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        con.execute("""
            INSERT INTO asset_history
            (asset_id, asset_name, action_type, previous_info, updated_info, performed_by, action_time)
            VALUES (?, ?, 'Deleted', ?, '', ?, ?)
        """, (asset_id, row[0], asset_info(info), performed_by, now))
        con.execute("DELETE FROM assets WHERE asset_id=?", (asset_id,))
        con.commit()

def list_assets(search_text=""):
    with connect_db() as con:
        if search_text:
            pattern = f"%{search_text}%"
            return con.execute("""
                SELECT asset_id, asset_name, category, quantity, location, status, description
                FROM assets
                WHERE asset_id LIKE ? OR asset_name LIKE ? OR category LIKE ? OR location LIKE ?
                ORDER BY id DESC
            """, (pattern, pattern, pattern, pattern)).fetchall()
        return con.execute("""
            SELECT asset_id, asset_name, category, quantity, location, status, description
            FROM assets ORDER BY id DESC
        """).fetchall()

def list_history(search_text="", action_type="All"):
    sql = """SELECT id, asset_id, asset_name, action_type, previous_info,
                    updated_info, performed_by, action_time FROM asset_history WHERE 1=1"""
    params = []
    if search_text:
        p = f"%{search_text}%"
        sql += " AND (asset_id LIKE ? OR asset_name LIKE ?)"
        params += [p, p]
    if action_type != "All":
        sql += " AND action_type=?"
        params.append(action_type)
    sql += " ORDER BY id DESC"
    with connect_db() as con:
        return con.execute(sql, params).fetchall()

def delete_history(history_id):
    with connect_db() as con:
        con.execute("DELETE FROM asset_history WHERE id=?", (history_id,))
        con.commit()
