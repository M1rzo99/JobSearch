# Ish Topish bot

Wanted, Saramin va JobKorea'dan koreys-o'zbek tarjimonlik va O'zbekiston–Koreya hamkorlik kompaniyalaridagi ishlarni topib, Telegramga chiroyli xabar qilib yuboradigan bot.

## Qanday ishlaydi
- Har 10 daqiqada (`SEARCH_INTERVAL_MIN`) `profile.yaml` dagi so'zlar bilan 3 ta saytda qidiradi.
- Har bir e'lonni moslik bo'yicha baholaydi (★ yulduzlar), past ballilarni yubormaydi.
- Bir e'lon bir nechta saytda bo'lsa (kompaniya + lavozim nomi o'xshash), faqat bir marta keladi.
- **✅ Topshirish**: xabar tepasiga `✅ TOPSHIRILDI` belgisi va 🏆 reaksiya qo'yiladi, tugmalar o'rniga bitta katta `🚀 Saramin'da 즉시지원` (JobKorea / Wanted) tugmasi chiqadi. Uni bossangiz e'lon sahifasi ochiladi, saytdagi o'z CV'ingiz bilan 즉시지원 ni o'zingiz bosasiz. Bot hech qachon akkauntingizga kirmaydi.
- Ixtiyoriy `APPLY_MODE=email`: e'londa email bo'lsa, `data/files/` dagi rezyume koreyscha xat bilan Gmail'dan o'zi yuboriladi.
- **✕ Rad etish**: xabar o'chib ketadi.
- Telegram imkoniyatlari: yig'iladigan (expandable) tavsif bloki, reaksiyalar, xabar effekti, buyruqlar menyusi.

## Ishga tushirish (bepul)
Oddiy qadamlar: [QOLLANMA.md](QOLLANMA.md).

- `.github/workflows/search.yml` — GitHub Actions har 10 daqiqada `python -m app.run_once` ni ishga tushiradi.
  Qaysi e'lonlar yuborilgani `bot-state` branchidagi `jobs.db` da saqlanadi (dublikat kelmasligi uchun).
- `api/telegram.py` — Vercel funksiyasi, Telegram webhook: tugmalarni darhol ishlaydi.
- `app/bot.py` — muqobil: o'z serveringizda doimiy ishlaydigan versiya (`python -m app.bot` yoki Docker).

## Buyruqlar (faqat server versiyasida)
`/search` hozir qidirish · `/stats` statistika · `/pause` / `/resume`

## Testlar
`pip install pytest && python -m pytest -q tests`

## Maslahat: saytlarga bir marta kirish yetadi
Telegram havolalarni o'z ichki brauzerida ochsa, u yerda saytga qayta kirish so'ralishi mumkin.
Telegram > Sozlamalar > Chat sozlamalari > "Havolalarni ichki brauzerda ochish"ni o'chiring.
Shunda tugma Chrome/Safari'da ochiladi, u yerda esa siz allaqachon kirgansiz.
