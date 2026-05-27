# Bərəkətli Telegram Bot

Order-taking bot for Bərəkətli — Lənkəran-to-Bakı village marketplace.

## What this bot does

1. Customer says hi → welcome + menu
2. Taps a product → sees the farmer (photo + story)
3. Picks a quantity → added to cart
4. Loops until they tap "Sifarişi tamamla"
5. Reviews cart → confirms / edits / cancels
6. Shares contact (one tap)
7. Shares Google Maps location (one tap)
8. Order saved to Google Sheet + you get a notification on Telegram

---

## Setup — first time (about 30 minutes)

### 1. Install Python 3.11 or newer

Check what you have:
```bash
python3 --version
```

If you don't have it, install from python.org.

### 2. Get the code

Put all these files in one folder on your computer:
- bot.py
- menu.py
- sheets.py
- photo_helper.py
- requirements.txt
- .env.example

### 3. Create the bot in Telegram

1. Open Telegram, search for `@BotFather`
2. Send `/newbot`
3. Give it a name (e.g., `Bərəkətli`)
4. Give it a username ending in `bot` (e.g., `barakatli_orders_bot`)
5. **Copy the token** BotFather gives you

### 4. Find your admin chat ID

So the bot can send YOU notifications when orders come in:
1. Open Telegram, search for `@userinfobot`
2. Send it `/start`
3. It shows your numeric ID — copy it

### 5. Configure the bot

Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```

Open `.env` in any text editor and fill in:
- `BOT_TOKEN` — from BotFather
- `ADMIN_CHAT_ID` — from @userinfobot
- (Leave Google Sheet stuff blank for now)

### 6. Install dependencies

```bash
cd barakatli_bot
python3 -m venv venv
source venv/bin/activate    # on Mac/Linux
# OR on Windows:
# venv\Scripts\activate
pip install -r requirements.txt
```

### 7. Run the bot

```bash
python bot.py
```

You should see: `🤖 Bərəkətli bot işə düşdü.`

### 8. Test it!

Open Telegram, find your bot, send `/start`. Try placing a test order.

---

## After basic version works

### Add farmer photos
1. Stop the bot (Ctrl+C)
2. Run: `python photo_helper.py`
3. Send a farmer photo to your bot
4. Copy the file_id it prints
5. Paste it into `menu.py` for the right farmer
6. Repeat for each photo

### Connect Google Sheets
Follow the instructions at the top of `sheets.py`.

### Edit menu
Open `menu.py` — change prices, add products, mark items inactive when out of stock.

---

## Daily workflow

- **Wednesday 6 PM:** orders close. Open your Google Sheet, see all orders for the week.
- **Need to take a product offline?** Edit `menu.py`, set `"active": False`. Restart the bot.
- **Need to update a price?** Edit `menu.py`. Restart the bot.

---

## Going live (when you're ready)

The bot only runs while your laptop is on. To run 24/7, deploy to Railway or Render (~15 min, free tier). Ask Claude when you're ready.
