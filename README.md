# Ish Topish bot

Wanted, Saramin va JobKorea'dan koreys-o'zbek tarjimonlik va O'zbekiston–Koreya hamkorlik kompaniyalaridagi ishlarni topib, Telegramga chiroyli xabar qilib yuboradigan bot.

## Qanday ishlaydi
- Har 30 daqiqada (`SEARCH_INTERVAL_MIN`) `profile.yaml` dagi so'zlar bilan 3 ta saytda qidiradi.
- Har bir e'lonni moslik bo'yicha baholaydi (★ yulduzlar), past ballilarni yubormaydi.
- Bir e'lon bir nechta saytda bo'lsa (kompaniya + lavozim nomi o'xshash), faqat bir marta keladi.
- **✅ Topshirish**: xabar tepasiga `✅ TOPSHIRILDI` belgisi va 🏆 reaksiya qo'yiladi, tugmalar o'rniga bitta katta `🚀 Saramin'da 즉시지원` (JobKorea / Wanted) tugmasi chiqadi. Uni bossangiz e'lon sahifasi ochiladi, saytdagi o'z CV'ingiz bilan 즉시지원 ni o'zingiz bosasiz. Bot hech qachon akkauntingizga kirmaydi.
- Ixtiyoriy `APPLY_MODE=email`: e'londa email bo'lsa, `data/files/` dagi rezyume koreyscha xat bilan Gmail'dan o'zi yuboriladi.
- **✕ Rad etish**: xabar o'chib ketadi.
- Telegram imkoniyatlari: yig'iladigan (expandable) tavsif bloki, reaksiyalar, xabar effekti, buyruqlar menyusi.

## Ishga tushirish
1. `.env.example` ni `.env` ga nusxalang va to'ldiring (bot token, Telegram ID; Gmail faqat email rejimi uchun).
2. `profile.yaml` dagi qidiruv so'zlari va ballarni tekshiring (rezyume PDF faqat email rejimi uchun kerak).
3. Saramin, JobKorea va Wanted'da CV'ingizni to'ldirib, telefoningiz brauzerida akkauntlarga kirib qo'ying.
4. `pip install -r requirements.txt && python -m app.bot` yoki `docker build -t ishtopish . && docker run -d --restart=always --env-file .env -v $PWD/data:/app/data ishtopish`
5. Telegramda botga `/start` yozing.

## Buyruqlar
`/search` hozir qidirish · `/stats` statistika · `/pause` / `/resume`

## Testlar
`pip install pytest && python -m pytest -q tests`

## Maslahat: saytlarga bir marta kirish yetadi
Telegram havolalarni o'z ichki brauzerida ochsa, u yerda saytga qayta kirish so'ralishi mumkin.
Telegram > Sozlamalar > Chat sozlamalari > "Havolalarni ichki brauzerda ochish"ni o'chiring.
Shunda tugma Chrome/Safari'da ochiladi, u yerda esa siz allaqachon kirgansiz.
