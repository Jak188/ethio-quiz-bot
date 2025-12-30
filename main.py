import asyncio
import json
import logging
import random
import sqlite3
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command

# 1. ቦቱን እና ባለቤቱን መለየት
API_TOKEN = '8392060519:AAFMzK7HGRsZ-BkajlD6wcQ9W6Bq8BqkzNM'
ADMIN_ID = 8394878208 # የሰጠኸኝ ID እዚህ ገብቷል

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# 2. የዳታቤዝ ዝግጅት (SQLite)
conn = sqlite3.connect('quiz_bot.db', check_same_thread=False)
cursor = conn.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS scores 
                  (user_id INTEGER PRIMARY KEY, name TEXT, points INTEGER)''')
conn.commit()

# 3. የጥያቄዎች ፋይል
with open('questions.json', 'r', encoding='utf-8') as f:
    questions = json.load(f)

running_loops = {} 
answered_users = {}

# --- ውጤትን በዳታቤዝ ውስጥ ለመጨመር ---
def update_score(user_id, name, points):
    cursor.execute("SELECT points FROM scores WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    if row:
        new_points = row[0] + points
        cursor.execute("UPDATE scores SET points = ?, name = ? WHERE user_id = ?", (new_points, name, user_id))
    else:
        cursor.execute("INSERT INTO scores (user_id, name, points) VALUES (?, ?, ?)", (user_id, name, points))
    conn.commit()

# --- የ /start ኮማንድ (ለአድሚን ብቻ) ---
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return 
    
    chat_id = message.chat.id
    if running_loops.get(chat_id):
        return await message.answer("ቦቱ ቀድሞውኑ እየሰራ ነው።")

    running_loops[chat_id] = True
    await message.answer("የጥያቄ ውድድር በዳታቤዝ ታጅቦ ተጀምሯል! 🚀\nበየ 3 ደቂቃው ጥያቄ ይቀርባል።")
    asyncio.create_task(quiz_loop(chat_id))

# --- የጥያቄ ዑደት ---
async def quiz_loop(chat_id):
    random_questions = list(questions)
    random.shuffle(random_questions)
    
    q_index = 0
    while running_loops.get(chat_id):
        if q_index >= len(random_questions):
            random.shuffle(random_questions)
            q_index = 0
            
        current_q = random_questions[q_index]
        answered_users[chat_id] = []
        
        options_text = "\n".join([f"{idx+1}. {opt}" for idx, opt in enumerate(current_q['o'])])
        msg_text = f"🔹 Subject: {current_q.get('subject', 'General')}\n\n{current_q['q']}\n\n{options_text}"
        
        # ፎቶ ካለ መላክ፣ ከሌለ በቴክስት ብቻ
        try:
            if "img" in current_q and current_q["img"] and current_q["img"].startswith("http"):
                sent_msg = await bot.send_photo(chat_id, photo=current_q["img"], caption=msg_text)
            else:
                sent_msg = await bot.send_message(chat_id, msg_text)
            
            running_loops[chat_id] = {"q": current_q, "msg_id": sent_msg.message_id, "active": True}
        except Exception as e:
            logging.error(f"Error sending: {e}")

        q_index += 1
        await asyncio.sleep(180) # 3 ደቂቃ

# --- መልስ መቀበያ ---
@dp.message()
async def handle_answer(message: types.Message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    
    loop_info = running_loops.get(chat_id)
    if not loop_info or not isinstance(loop_info, dict) or not loop_info.get("active"):
        return

    if user_id in answered_users.get(chat_id, []):
        return

    current_q = loop_info["q"]
    correct_text = current_q["o"][current_q["c"]]

    if message.text == correct_text:
        if chat_id not in answered_users: answered_users[chat_id] = []
        answered_users[chat_id].append(user_id)
        
        is_first = len(answered_users[chat_id]) == 1
        points = 8 if is_first else 4
        
        # ውጤትን በዳታቤዝ ውስጥ ማስቀመጥ
        update_score(user_id, message.from_user.full_name, points)
        
        if is_first:
            await message.answer(f"👏 ጎበዝ {message.from_user.first_name}! ቀድመህ በመመለስህ 8 ነጥብ አግኝተሃል!")
        else:
            await message.answer(f"✅ ትክክል {message.from_user.first_name}! 4 ነጥብ ተጨምሮልሃል።")

# --- የ /stop ኮማንድ (ለአድሚን ብቻ) ---
@dp.message(Command("stop"))
async def cmd_stop(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    running_loops[message.chat.id] = False
    await message.answer("ውድድሩ ቆሟል። ውጤቶች በዳታቤዝ ተቀምጠዋል። 🛑")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
