# 📱 NEET QuizBot — Complete Mobile Deployment Guide
### (Sirf Phone / Smartphone se Heroku & PostgreSQL par Bot Host karne ka Tareeqa)

> 💡 **Note for Client:** Is bot ko host karne ke liye aapko **kisi Laptop ya Computer ki koi zarurat nahi hai**. Aap apne phone ke **Chrome ya Safari browser** se ye saare steps 5 se 10 minute me complete kar sakte hain!

---

## 📑 Table of Contents
1. [Step 1: Telegram Bot Token & Settings (Mobile Telegram App)](#step-1-telegram-bot-token--settings)
2. [Step 2: Free PostgreSQL Database Setup (Mobile Browser)](#step-2-free-postgresql-database-setup)
3. [Step 3: Heroku par Bot Deploy karna (Mobile Browser)](#step-3-heroku-par-bot-deploy-karna)
4. [Step 4: 100% Free Alternative (Render.com Mobile Setup)](#step-4-100-free-alternative-rendercom)
5. [Step 5: Group me Bot ko Kaise Use Karein](#step-5-group-me-bot-ko-kaise-use-karein)
6. [Common Questions & Troubleshooting](#common-questions--troubleshooting)

---

## Step 1: Telegram Bot Token & Settings

Apne phone me Telegram app open karein:

### 1.1 Bot Token Lena
1. Telegram me search bar me type karein: `@BotFather` (Blue tick wala official account).
2. `Start` dabayein aur command bhejein: `/newbot`
3. Bot ka **Display Name** daalein (Jaise: *NEET Quiz Master*).
4. Bot ka **Username** daalein jo `bot` par khatm ho (Jaise: *NeetPhysicsMaster_bot*).
5. BotFather aapko ek **API Token** dega, jo is format me hoga:  
   `8927261665:AAFx8jnPyixX5MZfk1GJUcE5C0b9pOwg5O8`  
   👉 **Isko copy karke apne Notes me save kar lein.**

### 1.2 Privacy Mode DISABLE Karna (BOHOT ZARURI HAI)
Agar aap ye step nahi karenge, toh bot group ke polls aur quiz votes ko read nahi kar payega:
1. `@BotFather` ko command bhejein: `/setprivacy`
2. Apna bot choose karein.
3. **`Disable`** par tap karein. *(Aapko confirmation aayegi: "Privacy mode is now disabled")*.

### 1.3 Group Joining & Inline Mode Enable Karna
1. `@BotFather` ko command bhejein: `/setjoingroups` -> Bot select karein -> **`Enable`** karein.
2. `@BotFather` ko command bhejein: `/setinline` -> Bot select karein -> Placeholder me type karein: `Search quizzes...`

### 1.4 Apna Telegram Numeric ID Nikalna
1. Telegram me search karein: `@userinfobot`
2. `Start` dabayein.
3. Wo aapko aapki **Id** dega (Jaise: `687654321`).  
   👉 **Isko copy kar lein.** Is ID se aap bot ke Owner banenge aur `/stats` dekh payenge.

---

## Step 2: Free PostgreSQL Database Setup

> ❓ **MongoDB ya PostgreSQL?**  
> Ye bot **PostgreSQL** use karta hai kyunki quizzes, questions, negative marking, options aur live students ke scores aapas me deeply interconnected (Relational) hote hain. PostgreSQL me data **100% secure** rehta hai aur kabhi delete nahi hota.

Phone se 100% Free Lifetime PostgreSQL database banane ke 2 aasan tareeqe hain:

### Tareeqa A: [Neon.tech](https://neon.tech) (Sabse Best & 100% Free Forever)
1. Phone ke Chrome browser me **[https://neon.tech](https://neon.tech)** open karein.
2. **"Sign Up"** par tap karein aur apne **Google Account** ya **GitHub** se login karein. (Koi credit card nahi lagta).
3. **"Create Project"** button par tap karein:
   - Project Name me likhein: `quizbot-db`
   - Region: Asia ya Europe (default rehne dein)
   - **Create Project** dabayein.
4. Screen par aapko **Connection Details** dikhegi jisme ek link hogi:
   ```text
   postgresql://akash:password123@ep-cool-fog-1234.ap-southeast-1.aws.neon.tech/neondb?sslmode=require
   ```
5. Wahan bane **Copy** icon par tap karke is link ko copy kar lein!

---

## Step 3: Heroku par Bot Deploy karna (Mobile Browser)

Phone ke Chrome browser me ye steps follow karein:

> 📱 **Pro Tip:** Chrome browser me upar right corner ke **3 dots (⋮)** par click karke **"Desktop site"** tick kar lein. Isse screen computer jaisi saaf dikhai degi.

### 3.1 Heroku App Create Karein
1. **[https://www.heroku.com](https://www.heroku.com)** open karein aur login karein.
2. Dashboard par upar right corner me **"New"** button par tap karein aur **"Create new app"** select karein.
3. **App Name** daalein: Jaise `my-neet-quizbot` (jo name available ho).
4. Region me `United States` ya `Europe` select karein aur **"Create app"** par tap karein.

### 3.2 GitHub Repository Connect Karein
1. Upar ke tabs me se **"Deploy"** tab par tap karein.
2. **Deployment method** me **GitHub** ke icon par tap karein.
3. Apne GitHub account se connect karein aur search box me repo ka naam daalein: `neet-quizbot`.
4. Search result aane par **"Connect"** button dabayein.

### 3.3 Environment Variables (Config Vars) Daalein
1. Upar ke tabs me se **"Settings"** tab par tap karein.
2. Scroll karein aur **"Config Vars"** section ke andar **"Reveal Config Vars"** button dabayein.
3. Yahan aapko ek-ek karke **KEY** aur **VALUE** add karni hai:

| KEY | VALUE (Aapki Details) |
| :--- | :--- |
| `BOT_TOKEN` | BotFather se mila hua Token (e.g. `8927261665:AAFx8...`) |
| `BOT_USERNAME` | Aapka bot username bina `@` ke (e.g. `NeetPhysicsMaster_bot`) |
| `ADMIN_USER_IDS` | Step 1.4 me mila hua aapka Numeric Telegram ID (e.g. `687654321`) |
| `OWNER_USERNAME` | Aapka apna Telegram username bina `@` ke (e.g. `akashjhaji094`) |
| `SUPPORT_URL` | Aapka Support Group ya Channel link (e.g. `https://t.me/your_channel`) |
| `DATABASE_URL` | Neon.tech se copy kiya hua `postgresql://...` link |
| `ENVIRONMENT` | `production` |

*(Har entry ke baad **"Add"** button dabayein).*

### 3.4 Bot Build & Deploy Karein
1. Wapas upar **"Deploy"** tab par jayein.
2. Page ke bilkul neeche scroll karein, wahan **"Manual deploy"** section hoga.
3. Branch me `main` select rahega, bas **"Deploy Branch"** button par tap kar dein!
4. Screen par code install hona start hoga aur 1–2 minute me likha aayega: **"Your app was successfully deployed."**

### 3.5 Bot ko START (Turn ON) Karna
1. Upar ke tabs me se **"Resources"** tab par tap karein.
2. Wahan aapko **Dynos** dikhenge (`web` ya `worker`).
3. Uske aage bane **Pencil (Edit)** icon par tap karein.
4. Switch ko **ON (Blue)** karein aur **"Confirm"** dabayein!
5. **Mubarak ho! Aapka bot ab 24/7 Telegram par live chal raha hai!** 🎉

---

## Step 4: 100% Free Alternative (Render.com)
Agar Heroku par $5/month ka paid eco dyno plan nahi lena aur **bilkul ₹0 kharcha** chahiye, toh Render.com phone par sabse best hai:

1. Phone browser me **[https://render.com](https://render.com)** open karein aur GitHub se login karein.
2. **"New +"** -> **"Web Service"** -> Apni repo `neet-quizbot` connect karein.
3. Settings:
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `python -m app.main`
   - **Plan:** `Free`
4. **Environment Variables** me wahi saari keys add karein jo upar table me hain (`BOT_TOKEN`, `DATABASE_URL`, etc.).
5. **"Create Web Service"** dabayein.
6. 24/7 jagaye rakhne ke liye **[uptimerobot.com](https://uptimerobot.com)** par jakar apne Render app URL par 10-minute ka free ping laga dein.

---

## Step 5: Group me Bot ko Kaise Use Karein

1. **Group me Add Karein**:
   - Apne Telegram study/coaching group me jayein.
   - "Add Member" par tap karein aur apne bot ko add karein.
2. **Admin Banayein (Zaruri)**:
   - Group settings me jayein -> **Administrators** -> Bot ko Admin banayein.
   - Permissions me **"Send Messages"**, **"Pin Messages"**, aur **"Manage Topics"** ON rakhein.
3. **Quiz Start Karein**:
   - Group me command bhejein:  
     `/start quiz_CODE`  
     *(Ya bot me private chat me jakar quiz ke niche **'Start Quiz in Group'** button dabayein).*
   - Bot group me countdown ke sath timed questions (polls) bhejega.
   - Sabhi students ke live answers track honge.
   - Quiz khatam hote hi bot automatically **Ranked Leaderboard** post karega! 🏆

---

## ❓ Common Questions & Troubleshooting

#### Q1. Bot group me poll to bhej raha hai par student ke vote count nahi ho rahe?
👉 `@BotFather` me jaakar `/setprivacy` command se **Privacy Mode ko DISABLE** karein (Step 1.2 dekhein).

#### Q2. Kya phone se quiz banaya ja sakta hai?
👉 **Haan bilkul!** Telegram me bot ko private chat me `/newquiz` bhejein. Bot aapse Title, Question aur Options mangega. Aap phone se image/diagram bhi bhej sakte hain.

#### Q3. Kya phone switch off hone par bot band ho jayega?
👉 **Bilkul nahi!** Bot cloud (Heroku / Render) ke server par chal raha hai. Aapka phone switch off ho ya internet band ho, bot 24/7 active rahega.

#### Q4. Bot Statistics kaise check karein?
👉 Bot ko private chat me `/stats` bhejein. Agar aapka Telegram ID `ADMIN_USER_IDS` me add hai, toh aapko **Total Groups**, **Total Users**, aur **Total Quizzes** ka live data dikhega.

---
**Guide Created for:** NEET QuizBot Client Delivery  
**Support:** Contact Bot Owner / Developer
