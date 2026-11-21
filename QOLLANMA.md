# Botni bepul ishga tushirish (15 daqiqa, 0 so'm)

Bot ikki bepul xizmatda ishlaydi, kompyuteringiz o'chiq bo'lsa ham:

- **GitHub Actions** har 30 daqiqada saytlardan yangi ishlarni qidirib, Telegramga yuboradi.
- **Vercel** ✅ Topshirish va ✕ Rad etish tugmalarini darhol ishlatadi.

Ikkalasi ham bepul, karta so'ramaydi va GitHub akkauntingiz bilan kiriladi.

---

## 1-qadam. Bot yaratish (Telegram)
1. **@BotFather** > `/newbot` > nom > username (oxiri `bot` bilan tugasin).
2. Bergan **token**ni nusxalab qo'ying (`123456789:AAH...`). Hech kimga yubormang.
3. ❗ O'z botingizni oching va **Start** bosing. Busiz bot sizga yoza olmaydi.

## 2-qadam. Telegram ID raqamingiz
1. Telegramda **@userinfobot** ni oching, **Start** bosing.
2. U ko'rsatgan `Id: 123456789` raqamini nusxalab qo'ying.

## 3-qadam. Vercel (tugmalar uchun)
1. https://vercel.com/signup > **Hobby** (bepul) > **Continue with GitHub**.
2. **Add New...** > **Project** > ro'yxatdan **JobSearch** ni topib **Import** bosing.
   (Ko'rinmasa: **Adjust GitHub App Permissions** > JobSearch ga ruxsat bering.)
3. **Environment Variables** bo'limini oching:
   Key: `BOT_TOKEN`, Value: 1-qadamdagi token. **Add** bosing.
4. **Deploy** bosing va 1 daqiqa kuting.
5. Tayyor bo'lgach, **Domains** ostidagi manzilni nusxalang, masalan `jobsearch-abc.vercel.app`.

## 4-qadam. GitHub'ga 3 ta maxfiy qiymat
1. https://github.com/M1rzo99/JobSearch/settings/secrets/actions sahifasini oching.
2. **New repository secret** tugmasi bilan quyidagi 3 tasini birma-bir qo'shing:

| Name | Secret |
|---|---|
| `BOT_TOKEN` | 1-qadamdagi token |
| `CHAT_ID` | 2-qadamdagi ID raqam |
| `WEBHOOK_URL` | 3-qadamdagi Vercel manzili |

## 5-qadam. Ishga tushirish
1. https://github.com/M1rzo99/JobSearch/actions sahifasini oching.
   Agar "Workflows aren't being run" chiqsa, yashil **I understand... enable them** tugmasini bosing.
2. Chapda **Ish qidirish** > o'ngda **Run workflow** > yana **Run workflow**.
3. 2–3 daqiqada Telegramga "👋 Ish Topish ishga tushdi!" xabari, keyin e'lonlar keladi.

Shundan keyin bot har 30 daqiqada o'zi ishlaydi. Hech narsa bosish shart emas.

---

### Saytlar uchun bir martalik tayyorgarlik
- Saramin, JobKorea va Wanted'da CV'ingizni to'ldiring.
- Telefoningizdagi Chrome yoki Safari'da shu 3 saytga kirib qo'ying.
- Telegram > Sozlamalar > Chat sozlamalari > **ichki brauzerda ochish**ni o'chiring.
  Shunda 🚀 tugma sahifani o'sha brauzerda ochadi va qayta login so'ramaydi.

### Bilib qo'ying
- JobSearch repo **public** (hammaga ochiq). Shu sababli GitHub Actions cheksiz bepul.
  Kodda shaxsiy ma'lumot yo'q, token esa Secrets'da yashirin turadi. `profile.yaml` ga telefon raqam yozmang.
- GitHub 60 kun repoda o'zgarish bo'lmasa avtomatik ishni to'xtatib, email yuboradi.
  Shunda Actions sahifasida **Enable workflow** ni bir marta bosasiz.

### Biror narsa ishlamasa
Actions sahifasida qizil ❌ bo'lgan ishni oching, ekranni rasmga olib menga yuboring.
