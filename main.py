import asyncio
import json
import logging
import random
import sqlite3
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command

# 1. ቦቱን እና ባለቤቱን መለየት
API_TOKEN = '8392060519:AAFMzK7HGRsZ-BkajlD6wcQ9W6Bq8BqkzNM'
# ማሳሰቢያ፡ ይህ ID ካንተ ID ጋር መመሳሰሉን አረጋግጥ
ADMIN_ID = 8394878208 

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# 2. የዳታቤዝ ዝግጅት
conn = sqlite3.connect('quiz_final.db', check_same_thread=False)
cursor = conn.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS scores 
                  (user_id INTEGER PRIMARY KEY, name TEXT, points INTEGER DEFAULT 0)''')
conn.commit()

# 3. የጥያቄዎች ፋይል
try:
    with open('questions.json', 'r', encoding='utf-8') as f:
        questions = json.load(f)
except:
    questions = []

active_loops = {}
poll_map = {}

def save_score(user_id, name, points):
    cursor.execute("SELECT points FROM scores WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    if row:
        cursor.execute("UPDATE scores SET points = points + ?, name = ? WHERE user_id = ?", (row[0] + points, name, user_id))
    else:
        cursor.execute("INSERT INTO scores (user_id, name, points) VALUES (?, ?, ?)", (user_id, name, points))
    conn.commit()

# --- ኮማንዶች ---

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    # አድሚን መሆንህን ቼክ ያደርጋል
    if message.from_user.id != ADMIN_ID:
        return await message.answer("ይህ ቦት ለአድሚን ብቻ የሚሰሩ ኮማንዶች አሉት።")
    
    chat_id = message.chat.id
    active_loops[chat_id] = True
    await message.answer("🚀 ውድድሩ ተጀምሯል! በየ 3 ደቂቃው ጥያቄ ይላካል።")
    asyncio.create_task(quiz_timer(chat_id))

@dp.message(Command("stop"))
async def cmd_stop(message: types.Message):
    if message.from_user.id != ADMIN_ID: return
    active_loops[message.chat.id] = False
    await message.answer("🛑 ውድድሩ ቆሟል።")

@dp.message(Command("rank"))
async def cmd_rank(message: types.Message):
    cursor.execute("SELECT name, points FROM scores ORDER BY points DESC LIMIT 10")
    rows = cursor.fetchall()
    if not rows:
        return await message.answer("እስካሁን ምንም የተመዘገበ ውጤት የለም።")
    
    text = "🏆 **የደረጃ ሰንጠረዥ (Top 10)** 🏆\n\n"
    for i, row in enumerate(rows, 1):
        text += f"{i}. {row[0]} — {row[1]} ነጥብ\n"
    await message.answer(text, parse_mode="Markdown")

# --- የጥያቄ ዑደት ---
async def quiz_timer(chat_id):
    local_q = list(questions)
    random.shuffle(local_q)
    idx = 0
    while active_loops.get(chat_id):
        if idx >= len(local_q):
            random.shuffle(local_q)
            idx = 0
        
        q = local_q[idx]
        sent_poll = await bot.send_poll(
            chat_id=chat_id,
            question=q['q'],
            options=q['o'],
            type='quiz',
            correct_option_id=q['c'],
            is_anonymous=False
        )
        poll_map[sent_poll.poll.id] = {"correct": q['c'], "chat_id": chat_id, "winners": []}
        idx += 1
        await asyncio.sleep(180)

@dp.poll_answer()
async def on_poll_answer(poll_answer: types.PollAnswer):
    data = poll_map.get(poll_answer.poll_id)
    if data and poll_answer.option_ids[0] == data["correct"]:
        data["winners"].append(poll_answer.user.id)
        points = 8 if len(data["winners"]) == 1 else 4
        save_score(poll_answer.user.id, poll_answer.user.full_name, points)
        if len(data["winners"]) == 1:
            await bot.send_message(data["chat_id"], f"👏 {poll_answer.user.first_name} ፈጣኑ ሰው! +8 ነጥብ!")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
