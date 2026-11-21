import asyncio
import html
import logging

from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.filters import Command, CommandStart
from aiogram.types import (
    BotCommand,
    CallbackQuery,
    LinkPreviewOptions,
    Message,
    ReactionTypeEmoji,
)

from .apply import apply_by_email
from .cards import accepted_keyboard, job_keyboard, job_text, now_str
from .config import load_profile, load_settings
from .db import DB
from .pipeline import collect

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger("bot")

settings = load_settings()
db = DB(settings.db_path)
dp = Dispatcher()
_search_lock = asyncio.Lock()
EFFECT_PARTY = "5046509860389126442"  # 🎉 xabar effekti


def owner_id() -> int:
    """OWNER_ID berilmasa, botga birinchi /start yozgan odam egasi bo'ladi."""
    return settings.owner_id or int(db.kv_get("owner_id", "0"))


def owner_only(user_id: int) -> bool:
    return user_id == owner_id()


async def run_search(bot: Bot, chat_id: int, manual: bool = False) -> int:
    if _search_lock.locked():
        return -1
    async with _search_lock:
        profile = load_profile()
        jobs = await collect(settings, profile, db)
        for job in jobs:
            msg = await bot.send_message(
                chat_id,
                job_text(job, email_mode=settings.apply_mode == "email"),
                reply_markup=job_keyboard(job.uid, job.url),
                link_preview_options=LinkPreviewOptions(is_disabled=True),
            )
            db.set_message(job.uid, chat_id, msg.message_id)
            await asyncio.sleep(0.4)
        if manual and not jobs:
            await bot.send_message(chat_id, "🔎 Hozircha yangi mos e'lon yo'q. Keyinroq yana tekshiraman.")
        return len(jobs)


async def scheduler(bot: Bot) -> None:
    if not owner_id():
        log.warning("Egasi hali yo'q: botga Telegramda /start yozing")
    while True:
        chat_id = int(db.kv_get("chat_id", "0")) or owner_id()
        if chat_id and db.kv_get("paused") != "1":
            try:
                n = await run_search(bot, chat_id)
                log.info("qidiruv tugadi: %s ta yangi", n)
            except Exception:  # noqa: BLE001
                log.exception("qidiruvda xato")
        await asyncio.sleep(settings.interval_min * 60)


@dp.message(CommandStart())
async def start(m: Message) -> None:
    if not owner_id():
        db.kv_set("owner_id", str(m.from_user.id))
    if not owner_only(m.from_user.id):
        return await m.answer("Bu shaxsiy bot.")
    first = db.kv_get("chat_id") == ""
    db.kv_set("chat_id", str(m.chat.id))
    await m.answer(
        "👋 <b>Ish Topish</b> botiga xush kelibsiz!\n\n"
        "Men Wanted, Saramin va JobKorea'dan sizga mos ishlarni topib, shu yerga yuboraman.\n\n"
        "✅ <b>Topshirish</b> — e'lon belgilanadi va saytning 즉시지원 sahifasi tugmasi chiqadi\n"
        "✕ <b>Rad etish</b> — e'lon o'chib ketadi\n\n"
        "Bir e'lon bir nechta saytda bo'lsa ham, sizga faqat bir marta keladi.\n\n"
        "/search — hozir qidirish\n/stats — statistika\n/pause, /resume — to'xtatish va davom ettirish",
        message_effect_id=EFFECT_PARTY,
    )
    if first:
        await m.answer("🔎 Birinchi qidiruvni boshladim, bir necha daqiqada e'lonlar keladi.")
        asyncio.create_task(run_search(m.bot, m.chat.id, manual=True))


@dp.message(Command("search"))
async def cmd_search(m: Message) -> None:
    if not owner_only(m.from_user.id):
        return
    await m.answer("🔎 Qidiryapman... (1–3 daqiqa)")
    n = await run_search(m.bot, m.chat.id, manual=True)
    if n == -1:
        await m.answer("⏳ Qidiruv allaqachon ketyapti.")


@dp.message(Command("stats"))
async def cmd_stats(m: Message) -> None:
    if not owner_only(m.from_user.id):
        return
    s = db.stats()
    await m.answer(
        "📊 <b>Statistika</b>\n\n"
        f"Ko'rib chiqilgan e'lonlar: <b>{sum(s.values())}</b>\n"
        f"Sizga yuborilgan: <b>{s.get('sent', 0) + s.get('accepted', 0) + s.get('rejected', 0)}</b>\n"
        f"✅ Topshirilgan: <b>{s.get('accepted', 0)}</b>\n"
        f"✕ Rad etilgan: <b>{s.get('rejected', 0)}</b>\n"
        f"Mos kelmagan yoki dublikat: <b>{s.get('skipped', 0) + s.get('new', 0)}</b>"
    )


@dp.message(Command("pause"))
async def cmd_pause(m: Message) -> None:
    if owner_only(m.from_user.id):
        db.kv_set("paused", "1")
        await m.answer("⏸ Avtomatik qidiruv to'xtatildi. /resume bilan davom ettiring.")


@dp.message(Command("resume"))
async def cmd_resume(m: Message) -> None:
    if owner_only(m.from_user.id):
        db.kv_set("paused", "0")
        await m.answer("▶️ Avtomatik qidiruv davom etyapti.")


@dp.callback_query(F.data.startswith("rej|"))
async def on_reject(c: CallbackQuery) -> None:
    if not owner_only(c.from_user.id):
        return await c.answer()
    db.set_status(c.data.split("|", 1)[1], "rejected")
    try:
        await c.message.delete()
    except Exception:  # noqa: BLE001  (48 soatdan eski xabarni bot o'chira olmaydi)
        await c.message.edit_reply_markup(reply_markup=None)
    await c.answer("Rad etildi")


@dp.callback_query(F.data.startswith("acc|"))
async def on_accept(c: CallbackQuery) -> None:
    if not owner_only(c.from_user.id):
        return await c.answer()
    uid = c.data.split("|", 1)[1]
    row = db.get(uid)
    if not row:
        return await c.answer("E'lon topilmadi", show_alert=True)
    if row["status"] == "accepted":
        return await c.answer("Allaqachon topshirilgan ✅")
    url, source = row["url"], row["source"]
    if settings.apply_mode == "email" and row["apply_email"]:
        await c.answer("Topshirilyapti...")
        try:
            await apply_by_email(settings, load_profile(), row["apply_email"], row["company"], row["title"])
            note = f"{now_str()} · 📧 {row['apply_email']}"
        except Exception as e:  # noqa: BLE001
            log.exception("email apply failed")
            await c.message.reply(f"⚠️ Email yuborilmadi: {html.escape(str(e))}\nPastdagi tugma orqali sayt ichida topshiring.")
            note = f"{now_str()} · sayt orqali"
    else:
        # Sayt qoidalariga mos: bot faqat 즉시지원 sahifasini ochib beradi, tugmani o'zingiz bosasiz
        await c.answer("Pastdagi 🚀 tugmani bosing — 즉시지원 sahifasi ochiladi")
        note = now_str()

    db.set_status(uid, "accepted")
    body = c.message.html_text
    await c.message.edit_text(
        f"✅ <b>TOPSHIRILDI</b> · {html.escape(note)}\n\n{body}",
        reply_markup=accepted_keyboard(url, source),
        link_preview_options=LinkPreviewOptions(is_disabled=True),
    )
    try:
        await c.bot.set_message_reaction(c.message.chat.id, c.message.message_id, [ReactionTypeEmoji(emoji="🏆")])
    except Exception:  # noqa: BLE001
        pass


async def main() -> None:
    if not settings.bot_token:
        raise SystemExit("BOT_TOKEN .env faylida yo'q")
    bot = Bot(settings.bot_token, default=DefaultBotProperties(parse_mode="HTML"))
    await bot.set_my_commands([
        BotCommand(command="search", description="Hozir qidirish"),
        BotCommand(command="stats", description="Statistika"),
        BotCommand(command="pause", description="Avtomatik qidiruvni to'xtatish"),
        BotCommand(command="resume", description="Davom ettirish"),
    ])
    asyncio.create_task(scheduler(bot))
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
