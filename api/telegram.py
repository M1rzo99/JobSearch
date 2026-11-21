"""Vercel (bepul) funksiyasi: Telegram tugmalarini darhol ishlaydi.

✅ Topshirish -> xabar tepasiga "TOPSHIRILDI" belgisi, 🏆 reaksiya va saytning 즉시지원 tugmasi.
✕ Rad etish   -> xabar o'chadi.

Faqat Python standart kutubxonasi ishlatiladi, baza kerak emas.
Vercel'da faqat BOT_TOKEN o'zgaruvchisi kerak.
"""
import hashlib
import json
import os
import sqlite3
import tempfile
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from http.server import BaseHTTPRequestHandler

APPLY_LABEL = {
    "saramin": "🚀 Saramin'da 즉시지원",
    "jobkorea": "🚀 JobKorea'da 즉시지원",
    "wanted": "🚀 Wanted'da 지원하기",
}
KST = timezone(timedelta(hours=9))


def _token() -> str:
    t = os.environ.get("BOT_TOKEN", "").strip().strip('"').strip("'").strip()
    if t.lower().startswith("bot") and ":" in t[3:]:
        t = t[3:]
    return t


def webhook_secret(token: str) -> str:
    # app/run_once.py dagi bilan bir xil bo'lishi shart
    return hashlib.sha256(f"ishtopish:{token}".encode()).hexdigest()[:48]


def tg(method: str, payload: dict) -> dict:
    req = urllib.request.Request(
        f"https://api.telegram.org/bot{_token()}/{method}",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return json.loads(r.read())
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "error": str(e)}


def utf16_len(s: str) -> int:
    return len(s.encode("utf-16-le")) // 2


def find_url(markup: dict | None) -> str:
    for row in (markup or {}).get("inline_keyboard", []):
        for b in row:
            if b.get("url"):
                return b["url"]
    return ""


def accepted_edit(message: dict, source: str, now: datetime) -> dict:
    """Xabar matnini qayta yozmasdan, tepasiga belgi qo'shish (entity offsetlarini suramiz)."""
    stamp = now.strftime("%d.%m.%Y %H:%M")
    head = "✅ TOPSHIRILDI"
    prefix = f"{head} · {stamp}\n\n"
    shift = utf16_len(prefix)
    entities = [{"type": "bold", "offset": 0, "length": utf16_len(head)}]
    for e in message.get("entities") or []:
        e = dict(e)
        e["offset"] = e["offset"] + shift
        entities.append(e)
    url = find_url(message.get("reply_markup"))
    markup = {"inline_keyboard": [[{"text": APPLY_LABEL.get(source, "🔗 E'lonni ochish"), "url": url}]]} if url else None
    out = {
        "chat_id": message["chat"]["id"],
        "message_id": message["message_id"],
        "text": prefix + (message.get("text") or ""),
        "entities": entities,
        "link_preview_options": {"is_disabled": True},
    }
    if markup:
        out["reply_markup"] = markup
    return out


def handle_update(update: dict) -> None:
    cq = update.get("callback_query")
    if cq:
        data = cq.get("data") or ""
        msg = cq.get("message") or {}
        action, _, uid = data.partition("|")
        if not msg or action not in ("acc", "rej"):
            tg("answerCallbackQuery", {"callback_query_id": cq["id"]})
            return
        chat_id, mid = msg["chat"]["id"], msg["message_id"]
        if action == "rej":
            tg("answerCallbackQuery", {"callback_query_id": cq["id"], "text": "Rad etildi"})
            r = tg("deleteMessage", {"chat_id": chat_id, "message_id": mid})
            if not r.get("ok"):  # 48 soatdan eski xabarni o'chirib bo'lmaydi
                tg("editMessageReplyMarkup", {"chat_id": chat_id, "message_id": mid})
            return
        if (msg.get("text") or "").startswith("✅ TOPSHIRILDI"):
            tg("answerCallbackQuery", {"callback_query_id": cq["id"], "text": "Allaqachon belgilangan ✅"})
            return
        tg("answerCallbackQuery", {"callback_query_id": cq["id"], "text": "Pastdagi 🚀 tugmani bosing — 즉시지원 sahifasi ochiladi"})
        tg("editMessageText", accepted_edit(msg, uid.split(":", 1)[0], datetime.now(KST)))
        tg("setMessageReaction", {"chat_id": chat_id, "message_id": mid, "reaction": [{"type": "emoji", "emoji": "🏆"}]})
        return

    m = update.get("message")
    if m and (m.get("text") or "").startswith("/"):
        handle_command(m)


# ---------------- Buyruqlar ----------------

def _repo() -> str:
    owner = os.environ.get("VERCEL_GIT_REPO_OWNER")
    slug = os.environ.get("VERCEL_GIT_REPO_SLUG")
    return os.environ.get("GITHUB_REPO") or (f"{owner}/{slug}" if owner and slug else "M1rzo99/JobSearch")


def gh(method: str, path: str, body: dict | None = None) -> tuple[int, dict]:
    """GitHub API. GH_TOKEN bo'lmasa faqat ochiq (o'qish) so'rovlar ishlaydi."""
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "ish-topish-bot"}
    tok = os.environ.get("GH_TOKEN", "").strip()
    if tok:
        headers["Authorization"] = f"Bearer {tok}"
    data = json.dumps(body).encode() if body is not None else None
    if data:
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(f"https://api.github.com/repos/{_repo()}{path}", data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            raw = r.read()
            return r.status, (json.loads(raw) if raw else {})
    except urllib.error.HTTPError as e:
        return e.code, {}
    except Exception:  # noqa: BLE001
        return 0, {}


def load_db() -> sqlite3.Connection | None:
    """bot-state branchidagi bazani o'qish (repo ochiq)."""
    try:
        url = f"https://raw.githubusercontent.com/{_repo()}/bot-state/jobs.db"
        with urllib.request.urlopen(url, timeout=10) as r:
            path = os.path.join(tempfile.gettempdir(), "jobs.db")
            with open(path, "wb") as f:
                f.write(r.read())
        return sqlite3.connect(path)
    except Exception:  # noqa: BLE001
        return None


def owner_chat(db: sqlite3.Connection | None) -> int | None:
    if not db:
        return None
    try:
        row = db.execute("SELECT v FROM kv WHERE k='chat_id'").fetchone()
        if row and row[0]:
            return int(row[0])
        row = db.execute("SELECT chat_id FROM jobs WHERE chat_id IS NOT NULL LIMIT 1").fetchone()
        return int(row[0]) if row else None
    except Exception:  # noqa: BLE001
        return None


def is_paused() -> bool | None:
    code, data = gh("GET", "/actions/variables/PAUSED")
    if code == 200:
        return str(data.get("value", "")).lower() == "true"
    if code == 404 and os.environ.get("GH_TOKEN"):
        return False
    return None


def set_paused(value: bool) -> bool:
    body = {"name": "PAUSED", "value": "true" if value else "false"}
    code, _ = gh("PATCH", "/actions/variables/PAUSED", body)
    if code == 404:
        code, _ = gh("POST", "/actions/variables", body)
    return code in (200, 201, 204)


NEED_TOKEN = (
    "⚙️ Bu buyruq uchun Vercel'da <code>GH_TOKEN</code> kerak.\n"
    "Qo'llanma: QOLLANMA.md > \"Bot buyruqlari\"."
)

COMMANDS = [
    {"command": "search", "description": "🔎 Hoziroq qidirish"},
    {"command": "status", "description": "🤖 Bot holati"},
    {"command": "stats", "description": "📊 Statistika"},
    {"command": "pause", "description": "⏸ Qidiruvni to'xtatish"},
    {"command": "resume", "description": "▶️ Davom ettirish"},
    {"command": "help", "description": "❓ Yordam"},
]

HELP = (
    "🤖 <b>Ish Topish</b> — buyruqlar\n\n"
    "/search — hoziroq qidirish\n"
    "/status — bot holati va oxirgi qidiruv\n"
    "/stats — statistika\n"
    "/pause — avtomatik qidiruvni to'xtatish\n"
    "/resume — davom ettirish\n"
    "/help — shu ro'yxat\n\n"
    "Bot har 10 daqiqada o'zi qidiradi (GitHub ba'zan 5–15 daqiqa kechiktiradi)."
)


def _fmt_time(iso: str) -> str:
    try:
        dt = datetime.fromisoformat(iso.replace("Z", "+00:00")).astimezone(KST)
        return dt.strftime("%d.%m %H:%M")
    except Exception:  # noqa: BLE001
        return iso or "—"


def handle_command(m: dict) -> None:
    chat_id = m["chat"]["id"]
    cmd = (m.get("text") or "").split()[0].split("@")[0].lower()
    send = lambda text: tg("sendMessage", {"chat_id": chat_id, "text": text, "parse_mode": "HTML",
                                           "link_preview_options": {"is_disabled": True}})
    db = load_db()
    owner = owner_chat(db)
    if owner and chat_id != owner:
        send("Bu shaxsiy bot.")
        return

    if cmd in ("/start", "/help"):
        tg("setMyCommands", {"commands": COMMANDS})
        tg("setChatMenuButton", {"chat_id": chat_id, "menu_button": {"type": "commands"}})
        send(HELP)
    elif cmd == "/search":
        code, _ = gh("POST", "/actions/workflows/search.yml/dispatches", {"ref": "main"})
        if code == 204:
            send("🔎 Qidiruv boshlandi. 2–4 daqiqada yangi e'lonlar keladi (agar topilsa).")
        elif code in (401, 403, 404) or not os.environ.get("GH_TOKEN"):
            send(NEED_TOKEN)
        else:
            send(f"⚠️ Qidiruvni boshlab bo'lmadi (GitHub javobi: {code}).")
    elif cmd in ("/pause", "/resume"):
        if not os.environ.get("GH_TOKEN"):
            send(NEED_TOKEN)
        elif set_paused(cmd == "/pause"):
            send("⏸ Avtomatik qidiruv to'xtatildi. /resume bilan yoqasiz." if cmd == "/pause"
                 else "▶️ Avtomatik qidiruv yoqildi, har 10 daqiqada ishlaydi.")
        else:
            send("⚠️ O'zgartirib bo'lmadi. GH_TOKEN ruxsatlarini tekshiring (Variables: Read and write).")
    elif cmd == "/status":
        code, data = gh("GET", "/actions/workflows/search.yml/runs?per_page=1")
        runs = data.get("workflow_runs") or []
        paused = is_paused()
        state = {True: "⏸ to'xtatilgan", False: "▶️ ishlayapti", None: "▶️ ishlayapti"}[paused]
        lines = [f"🤖 <b>Holat:</b> {state}", "⏱ Har 10 daqiqada qidiradi"]
        if runs:
            r = runs[0]
            res = {"success": "✅", "failure": "❌", "cancelled": "⏹"}.get(r.get("conclusion") or "", "⏳")
            lines.append(f"🕒 Oxirgi qidiruv: {_fmt_time(r.get('created_at', ''))} {res}")
        if db:
            try:
                total = db.execute("SELECT COUNT(*) FROM jobs").fetchone()[0]
                sent = db.execute("SELECT COUNT(*) FROM jobs WHERE message_id IS NOT NULL").fetchone()[0]
                lines.append(f"📨 Yuborilgan e'lonlar: <b>{sent}</b> (ko'rib chiqilgan: {total})")
            except Exception:  # noqa: BLE001
                pass
        send("\n".join(lines))
    elif cmd == "/stats":
        if not db:
            send("📊 Hali statistika yo'q.")
            return
        try:
            rows = db.execute(
                "SELECT source, COUNT(*), SUM(message_id IS NOT NULL) FROM jobs GROUP BY source"
            ).fetchall()
            day = int(datetime.now(KST).replace(hour=0, minute=0, second=0).timestamp())
            today = db.execute(
                "SELECT COUNT(*) FROM jobs WHERE message_id IS NOT NULL AND created_at>=?", (day,)
            ).fetchone()[0]
        except Exception:  # noqa: BLE001
            send("📊 Statistikani o'qib bo'lmadi.")
            return
        names = {"wanted": "🟦 Wanted", "saramin": "🟩 Saramin", "jobkorea": "🟪 JobKorea"}
        lines = ["📊 <b>Statistika</b>", f"Bugun yuborilgan: <b>{today}</b>", ""]
        for src, total, sent in rows:
            lines.append(f"{names.get(src, src)}: {int(sent or 0)} yuborilgan / {total} ko'rilgan")
        send("\n".join(lines))
    else:
        send(HELP)


class handler(BaseHTTPRequestHandler):  # Vercel shu nomni qidiradi
    def do_POST(self):  # noqa: N802
        if self.headers.get("X-Telegram-Bot-Api-Secret-Token") != webhook_secret(_token()):
            self.send_response(401)
            self.end_headers()
            return
        length = int(self.headers.get("Content-Length") or 0)
        try:
            handle_update(json.loads(self.rfile.read(length) or b"{}"))
        except Exception:  # noqa: BLE001
            pass
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"ok")

    def do_GET(self):  # noqa: N802
        self.send_response(200)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.end_headers()
        self.wfile.write("Ish Topish bot ishlayapti ✅".encode())
