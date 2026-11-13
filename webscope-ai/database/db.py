import sqlite3, json
from config import Config

def connect():
    c = sqlite3.connect(Config.DATABASE)
    c.row_factory = sqlite3.Row
    return c

def init_db():
    with connect() as c:
        c.execute("""CREATE TABLE IF NOT EXISTS reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT, url TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP, data TEXT NOT NULL)""")

def save_report(url, data):
    with connect() as c:
        cur = c.execute("INSERT INTO reports(url,data) VALUES(?,?)", (url, json.dumps(data)))
        return cur.lastrowid

def list_reports():
    with connect() as c:
        rows = c.execute("SELECT id,url,created_at FROM reports ORDER BY id DESC LIMIT 50").fetchall()
        return [dict(r) for r in rows]

def get_report(report_id):
    with connect() as c:
        r = c.execute("SELECT * FROM reports WHERE id=?", (report_id,)).fetchone()
        return {"id": r["id"], "url": r["url"], "created_at": r["created_at"], "data": json.loads(r["data"])} if r else None

def delete_report(report_id):
    with connect() as c: c.execute("DELETE FROM reports WHERE id=?", (report_id,))
