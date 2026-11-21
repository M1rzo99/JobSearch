import sqlite3
import time
from pathlib import Path

from .dedup import dedup_key, is_similar, norm_company
from .models import Job

SCHEMA = """
CREATE TABLE IF NOT EXISTS jobs (
    uid TEXT PRIMARY KEY,
    source TEXT, url TEXT, title TEXT, company TEXT, company_norm TEXT,
    dkey TEXT, score INTEGER, apply_email TEXT,
    status TEXT DEFAULT 'new',      -- new | sent | accepted | rejected | duplicate | skipped
    chat_id INTEGER, message_id INTEGER,
    created_at INTEGER, updated_at INTEGER
);
CREATE INDEX IF NOT EXISTS idx_dkey ON jobs(dkey);
CREATE INDEX IF NOT EXISTS idx_company ON jobs(company_norm);
CREATE TABLE IF NOT EXISTS kv (k TEXT PRIMARY KEY, v TEXT);
"""


class DB:
    def __init__(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(path)
        self.conn.row_factory = sqlite3.Row
        self.conn.executescript(SCHEMA)

    def find_duplicate(self, job: Job) -> sqlite3.Row | None:
        """Shu e'lon (yoki boshqa saytdagi nusxasi) oldin ko'rilganmi?"""
        row = self.conn.execute("SELECT * FROM jobs WHERE uid=?", (job.uid,)).fetchone()
        if row:
            return row
        dk = dedup_key(job.company, job.title)
        row = self.conn.execute("SELECT * FROM jobs WHERE dkey=?", (dk,)).fetchone()
        if row:
            return row
        cn = norm_company(job.company)
        if cn:
            for r in self.conn.execute(
                "SELECT * FROM jobs WHERE company_norm=? AND created_at>?",
                (cn, int(time.time()) - 60 * 86400),
            ):
                if is_similar(r["title"], job.title):
                    return r
        return None

    def add(self, job: Job, status: str) -> None:
        now = int(time.time())
        self.conn.execute(
            """INSERT OR IGNORE INTO jobs
               (uid, source, url, title, company, company_norm, dkey, score, apply_email, status, created_at, updated_at)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
            (job.uid, job.source, job.url, job.title, job.company, norm_company(job.company),
             dedup_key(job.company, job.title), job.score, job.apply_email, status, now, now),
        )
        self.conn.commit()

    def set_message(self, uid: str, chat_id: int, message_id: int) -> None:
        self.conn.execute(
            "UPDATE jobs SET chat_id=?, message_id=?, status='sent', updated_at=? WHERE uid=?",
            (chat_id, message_id, int(time.time()), uid),
        )
        self.conn.commit()

    def set_status(self, uid: str, status: str) -> None:
        self.conn.execute(
            "UPDATE jobs SET status=?, updated_at=? WHERE uid=?", (status, int(time.time()), uid)
        )
        self.conn.commit()

    def get(self, uid: str) -> sqlite3.Row | None:
        return self.conn.execute("SELECT * FROM jobs WHERE uid=?", (uid,)).fetchone()

    def stats(self) -> dict:
        rows = self.conn.execute("SELECT status, COUNT(*) c FROM jobs GROUP BY status").fetchall()
        return {r["status"]: r["c"] for r in rows}

    def kv_get(self, k: str, default: str = "") -> str:
        r = self.conn.execute("SELECT v FROM kv WHERE k=?", (k,)).fetchone()
        return r["v"] if r else default

    def kv_set(self, k: str, v: str) -> None:
        self.conn.execute("INSERT OR REPLACE INTO kv(k, v) VALUES (?,?)", (k, v))
        self.conn.commit()
