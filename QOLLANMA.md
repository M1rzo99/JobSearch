# Botni Telegramda ishga tushirish (15 daqiqa)

Bot **Railway** degan xizmatda kechayu kunduz ishlaydi. Kompyuteringiz o'chiq bo'lsa ham ishlayveradi.
Narxi: birinchi oy bepul sinov krediti beriladi, keyin oyiga taxminan **5 dollar** (Hobby tarif).

---

## 1-qadam. Bot yaratish (Telegram, 2 daqiqa)
1. Telegramda **@BotFather** ni oching va **Start** bosing.
2. `/newbot` yozing.
3. Botga nom bering, masalan: `Ish Topish`.
4. Username bering, oxiri `bot` bilan tugashi shart, masalan: `mijoo_ish_bot`.
5. BotFather sizga uzun **token** beradi (`123456789:AAH...` ko'rinishida). Uni nusxalab qo'ying.
   ⚠️ Bu tokenni hech kimga, hatto chatga ham yubormang. Faqat 4-qadamda Railway'ga qo'yasiz.

## 2-qadam. GitHub repo (2 daqiqa)
1. https://github.com/new sahifasini oching.
2. **Repository name**: `JobSearch` (✅ bajarilgan)
3. **Private** ni tanlang.
4. Boshqa hech narsani belgilamang, **Create repository** bosing.
5. Menga "repo tayyor" deb yozing. Kodni o'zim joylayman.

## 3-qadam. Railway'ga ulash (5 daqiqa, kod joylangandan keyin)
1. https://railway.com sahifasiga kiring, **Login** > **Login with GitHub**.
2. **New Project** > **Deploy from GitHub repo** > `JobSearch` ni tanlang.
   (Railway GitHub'ga ruxsat so'rasa, **Install & Authorize** bosing.)
3. Loyiha ochiladi. Birinchi ishga tushish xato berishi normal, chunki token hali yo'q.

## 4-qadam. Tokenni qo'yish (1 daqiqa)
1. Loyihadagi xizmat kartochkasini bosing > **Variables** bo'limi > **New Variable**.
2. Name: `BOT_TOKEN`, Value: 1-qadamdagi token. **Add** bosing.

## 5-qadam. Xotira qo'shish (1 daqiqa)
Bot qaysi e'lonlarni ko'rsatganini eslab qolishi uchun (dublikat kelmasligi shu bilan ishlaydi):
1. Xizmat kartochkasida o'ng tugma (yoki **⌘K / Ctrl+K**) > **Attach Volume**.
2. **Mount path**: `/app/data` deb yozing va saqlang.

## 6-qadam. Hudud (ixtiyoriy, 30 soniya)
Xizmat > **Settings** > **Region** > **Southeast Asia (Singapore)**. Koreyaga eng yaqin hudud.

Oxirida yuqoridagi **Deploy** (yoki binafsha **Apply changes**) tugmasini bosing.

## 7-qadam. Boshlash
Telegramda o'z botingizni oching va **/start** bosing. Birinchi /start bosgan odam botning egasi bo'ladi,
boshqalar undan foydalana olmaydi. Bir necha daqiqada birinchi e'lonlar keladi.

---

### Saytlar uchun bir martalik tayyorgarlik
- Saramin, JobKorea va Wanted'da CV'ingizni to'ldiring.
- Telefoningizdagi Chrome yoki Safari'da shu 3 saytga kirib qo'ying.
- Telegram > Sozlamalar > Chat sozlamalari > **ichki brauzerda ochish**ni o'chiring.
  Shunda 🚀 tugma sahifani o'sha brauzerda ochadi va qayta login so'ramaydi.

### Biror narsa ishlamasa
Railway'da xizmat > **Deployments** > oxirgisi > **View logs**. Ekranni rasmga olib menga yuboring.
