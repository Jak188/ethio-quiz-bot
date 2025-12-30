import asyncio
import json
import logging
import random
import sqlite3
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command

# 1. ቦቱን እና ባለቤቱን መለየት
API_TOKEN = '8392060519:AAFMzK7HGRsZ-BkajlD6wcQ9W6Bq8BqkzNM'
ADMIN_ID = 8394878208  # ያንተ የቴሌግራም ID

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# 2. የዳታቤዝ ዝግጅት (ውጤት እንዳይጠፋ)
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
    logging.error(f"JSON ፋይሉን ማንበብ አልተቻለም: {e}")
    questions = []

# የጥያቄ ሁኔታ መቆጣጠሪያ
active_loops = {} 
poll_map = {} # የትኛው ፖል ከየትኛው ጥያቄ ጋር እንደተያያዘ ለማወቅ

# --- ውጤትን በዳታቤዝ ውስጥ ለማስቀመጥ ---
def save_score(user_id, name, points):
    cursor.execute("SELECT points FROM scores WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    if row:
        cursor.execute("UPDATE scores SET points = points + ?, name = ? WHERE user_id = ?", (points, name, user_id))
    else:
        cursor.execute("INSERT INTO scores (user_id, name, points) VALUES (?, ?, ?)", (user_id, name, points))
    conn.commit()

# --- የ /start ኮማንድ (ለአድሚን ብቻ) ---
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    
    chat_id = message.chat.id
    if active_loops.get(chat_id):
        return await message.answer("⚠️ ውድድሩ ቀድሞውኑ ተጀምሯል።")

    active_loops[chat_id] = True
    await message.answer("🎯 የኩዊዝ ውድድር ተጀምሯል! በየ 3 ደቂቃው ጥያቄ ይላካል።\n\nፈጣን መልስ: 8 ነጥብ | ሌላ: 4 ነጥብ")
    asyncio.create_task(quiz_timer(chat_id))

# --- የ 3 ደቂቃ የጊዜ ቆጣሪ ---
async def quiz_timer(chat_id):
    local_questions = list(questions)
    random.shuffle(local_questions)
    
    idx = 0
    while active_loops.get(chat_id):
        if idx >= len(local_questions):
            random.shuffle(local_questions)
            idx = 0
        
        q = local_questions[idx]
        
        # 📝 Native Quiz (Poll) መላክ
        try:
            sent_poll = await bot.send_poll(
                chat_id=chat_id,
                question=q['q'],
                options=q['o'],
                type='quiz',
                correct_option_id=q['c'],
                explanation=q.get('e', "ትክክለኛ መልስ!"),
                is_anonymous=False  # ውጤት ለመቁጠር ግዴታ False መሆን አለበት
            )
            
            # የፖሉን መረጃ መመዝገብ
            poll_map[sent_poll.poll.id] = {
                "correct": q['c'],
                "winners": [],
                "chat_id": chat_id
            }
        except Exception as e:
            logging.error(f"Poll መላክ አልተቻለም: {e}")

        idx += 1
        await asyncio.sleep(180) # 3 ደቂቃ መጠበቅ

# --- ተማሪዎች ሲመልሱ ነጥብ መቁጠሪያ ---
@dp.poll_answer()
async def on_poll_answer(poll_answer: types.PollAnswer):
    p_id = poll_answer.poll_id
    if p_id not in poll_map:
        return

    data = poll_map[p_id]
    user_id = poll_answer.user.id
    user_name = poll_answer.user.full_name

    # ትክክለኛ መልስ ከሆነ
    if poll_answer.option_ids[0] == data["correct"]:
        data["winners"].append(user_id)
        
        # ነጥብ አሰጣጥ
        is_first = len(data["winners"]) == 1
        reward = 8 if is_first else 4
        
        save_score(user_id, user_name, reward)
        
        if is_first:
            await bot.send_message(data["chat_id"], f"👏 ዛሬው ፈጣን! {user_name} መጀመሪያ በመመለሱ 8 ነጥብ አግኝቷል! 🎊")

# --- የ /stop ኮማንድ (ለአድሚን ብቻ) ---
@dp.message(Command("stop"))
async def cmd_stop(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    active_loops[message.chat.id] = False
    await message.answer("🛑 የጥያቄ ዑደቱ ቆሟል። ውጤቶች በዳታቤዝ ተቀምጠዋል።")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
