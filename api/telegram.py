"""Vercel (bepul) funksiyasi: Telegram tugmalarini darhol ishlaydi.

✅ Topshirish -> xabar tepasiga "TOPSHIRILDI" belgisi, 🏆 reaksiya va saytning 즉시지원 tugmasi.
✕ Rad etish   -> xabar o'chadi.

Faqat Python standart kutubxonasi ishlatiladi, baza kerak emas.
Vercel'da faqat BOT_TOKEN o'zgaruvchisi kerak.
"""
import hashlib
import json
import os
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
    return os.environ.get("BOT_TOKEN", "")


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
        tg("sendMessage", {
            "chat_id": m["chat"]["id"],
            "parse_mode": "HTML",
            "text": (
                "🤖 Men har 30 daqiqada yangi mos ishlarni o'zim yuboraman.\n"
                f"Sizning chat ID: <code>{m['chat']['id']}</code>"
            ),
        })


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
