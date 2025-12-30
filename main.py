import asyncio
import json
import logging
import random
import sqlite3
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command

# 1. ቦቱን እና ባለቤቶቹን መለየት
API_TOKEN = '8392060519:AAEn4tQwJgB2Q7QTNb5fM3XD59bnX34bxKg'
# የሰጠኸኝ 3ቱ IDs (አድሚኖች)
ADMIN_IDS = [-1003559562472, 7231324244, 8394878208] 

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# 2. የዳታቤዝ ዝግጅት
conn = sqlite3.connect('quiz_results.db', check_same_thread=False)
cursor = conn.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS scores 
                  (user_id INTEGER PRIMARY KEY, name TEXT, points INTEGER DEFAULT 0)''')
conn.commit()

# 3. የጥያቄዎች ፋይል
try:
    with open('questions.json', 'r', encoding='utf-8') as f:
        questions = json.load(f)
except Exception as e:
    logging.error(f"Error loading questions: {e}")
    questions = []

active_loops = {}
poll_map = {}

def save_score(user_id, name, points):
    cursor.execute("SELECT points FROM scores WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    if row:
        cursor.execute("UPDATE scores SET points = points + ?, name = ? WHERE user_id = ?", (points, name, user_id))
    else:
        cursor.execute("INSERT INTO scores (user_id, name, points) VALUES (?, ?, ?)", (user_id, name, points))
    conn.commit()

# --- ኮማንዶች ---

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    if message.from_user.id not in ADMIN_IDS:
        return
    
    chat_id = message.chat.id
    if active_loops.get(chat_id):
        return await message.answer("⚠️ ውድድሩ ቀድሞውኑ ተጀምሯል።")

    active_loops[chat_id] = True
    await message.answer("🎯 የኩዊዝ ውድድር ተጀምሯል! በየ 3 ደቂቃው ጥያቄ ይላካል።\n\nፈጣን መልስ: 8 ነጥብ | ሌላ: 4 ነጥብ")
    asyncio.create_task(quiz_timer(chat_id))

@dp.message(Command("stop"))
async def cmd_stop(message: types.Message):
    if message.from_user.id not in ADMIN_IDS:
        return
    active_loops[message.chat.id] = False
    await message.answer("🛑 የጥያቄ ዑደቱ ቆሟል። ውጤቶች በዳታቤዝ ተቀምጠዋል።")

@dp.message(Command("rank"))
async def cmd_rank(message: types.Message):
    cursor.execute("SELECT name, points FROM scores ORDER BY points DESC LIMIT 10")
    rows = cursor.fetchall()
    if not rows:
        return await message.answer("እስካሁን ምንም የተመዘገበ ውጤት የለም።")
    
    text = "🏆 **የደረጃ ሰንጠረዥ (Top 10)** 🏆\n\n"
    for i, row in enumerate(rows, 1):
        text += f"{i}. {row[0]} — {row[1]} ነጥብ\n"
    await message.answer(text)

# --- የጥያቄ ዑደት (3 ደቂቃ) ---
async def quiz_timer(chat_id):
    local_q = list(questions)
    random.shuffle(local_q)
    idx = 0
    
    while active_loops.get(chat_id):
        if idx >= len(local_q):
            random.shuffle(local_q)
            idx = 0
        
        q = local_q[idx]
        try:
            sent_poll = await bot.send_poll(
                chat_id=chat_id,
                question=q['q'],
                options=q['o'],
                type='quiz',
                correct_option_id=q['c'],
                explanation=q.get('e', "ትክክለኛ መልስ!"),
                is_anonymous=False
            )
            poll_map[sent_poll.poll.id] = {"correct": q['c'], "chat_id": chat_id, "winners": []}
        except Exception as e:
            logging.error(f"Poll Error: {e}")

        idx += 1
        await asyncio.sleep(180) # 180 ሰከንድ = 3 ደቂቃ

# --- መልስ መከታተያ ---
@dp.poll_answer()
async def on_poll_answer(poll_answer: types.PollAnswer):
    data = poll_map.get(poll_answer.poll_id)
    if not data: return

    if poll_answer.option_ids[0] == data["correct"]:
        data["winners"].append(poll_answer.user.id)
        is_first = len(data["winners"]) == 1
        points = 8 if is_first else 4
        
        save_score(poll_answer.user.id, poll_answer.user.full_name, points)
        
        if is_first:
            await bot.send_message(data["chat_id"], f"👏 {poll_answer.user.first_name} ፈጣኑ ሰው! +8 ነጥብ አግኝቷል! 🎉")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
