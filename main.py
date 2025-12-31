import asyncio
import json
import logging
import random
import sqlite3
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command

# 1. ቦቱን እና ባለቤቶቹን መለየት
API_TOKEN = '8392060519:AAEn4tQwJgB2Q7QTNb5fM3XD59bnX34bxKg'
ADMIN_IDS = [7231324244, 8394878208] 

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# 2. የዳታቤዝ ዝግጅት
conn = sqlite3.connect('quiz_results.db', check_same_thread=False)
cursor = conn.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS scores 
                  (user_id INTEGER PRIMARY KEY, name TEXT, points REAL DEFAULT 0)''')
conn.commit()

# 3. የጥያቄዎች ፋይል
try:
    with open('questions.json', 'r', encoding='utf-8') as f:
        all_questions = json.load(f)
except:
    all_questions = []

active_loops = {}
poll_map = {}

def save_score(user_id, name, points):
    cursor.execute("SELECT points FROM scores WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    if row:
        new_score = row[0] + points
        cursor.execute("UPDATE scores SET points = ?, name = ? WHERE user_id = ?", (new_score, name, user_id))
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
        return await message.answer("⚠️ ውድድሩ ቀድሞውኑ እየሰራ ነው።")

    active_loops[chat_id] = True
    # 3. ውድድሩ ሲጀመር መልካም ምኞት
    start_msg = (
        "🎯 የኩዊዝ ውድድር ተጀመረ!\n"
        "መልካም እድል ለሁላችሁም! 🍀 መልካም የውድድር ጊዜ ይሁንላችሁ።\n\n"
        "⏰ በየ 4 ደቂቃው ጥያቄ ይላካል።\n"
        "🥇 1ኛ ለመለሰ: 8 ነጥብ\n"
        "✅ ለሌላ ትክክል: 4 ነጥብ\n"
        "✍️ ለተሳተፈ: 1.5 ነጥብ"
    )
    await message.answer(start_msg)
    asyncio.create_task(quiz_timer(chat_id))

@dp.message(Command("stop"))
async def cmd_stop(message: types.Message):
    if message.from_user.id not in ADMIN_IDS:
        return
    
    active_loops[message.chat.id] = False
    
    cursor.execute("SELECT name, points FROM scores ORDER BY points DESC LIMIT 1")
    winner = cursor.fetchone()
    
    # 2. ለአሸናፊው ብዙ ርችት እና ሽልማት
    if winner:
        congrats_text = (
            f"🛑 ውድድሩ ተጠናቋል! 🛑\n\n"
            f"🎊✨🎆 🎇 🎆 ✨🎊\n"
            f"🏆 የዛሬው ታላቅ አሸናፊ፡ {winner[0]}\n"
            f"💰 ያከማቹት አጠቃላይ ነጥብ፡ {winner[1]}\n"
            f"🎊✨🎆 🎇 🎆 ✨🎊\n\n"
            "እንኳን ደስ አሎት! ቀጣይ ውድድር ላይ እንገናኝ። 👋"
        )
        await message.answer(congrats_text)
    else:
        await message.answer("🛑 ውድድሩ ቆሟል። ምንም ውጤት አልተመዘገበም።")

@dp.message(Command("rank"))
async def cmd_rank(message: types.Message):
    cursor.execute("SELECT name, points FROM scores ORDER BY points DESC LIMIT 10")
    rows = cursor.fetchall()
    if not rows:
        return await message.answer("እስካሁን ምንም ውጤት የለም።")
    
    text = "🏆 አጠቃላይ የደረጃ ሰንጠረዥ (Top 10) 🏆\n\n"
    for i, row in enumerate(rows, 1):
        text += f"{i}. {row[0]} — {row[1]} ነጥብ\n"
    await message.answer(text)

@dp.message(Command("clear_rank"))
async def cmd_clear(message: types.Message):
    if message.from_user.id not in ADMIN_IDS:
        return
    cursor.execute("DELETE FROM scores")
    conn.commit()
    await message.answer("🧹 የደረጃ ሰንጠረዥ በሙሉ ተሰርዟል!")

# --- 4 & 5. የጥያቄ ዑደት (Random & No Repeat) ---
async def quiz_timer(chat_id):
    # ጥያቄዎችን በየዙሩ በዘፈቀደ ለመቀያየር
    available_questions = list(all_questions)
    
    while active_loops.get(chat_id):
        if not available_questions:
            # ጥያቄዎች ካለቁ እንደገና ከፋይሉ ይጫኑ
            available_questions = list(all_questions)
            
        # 4. በዘፈቀደ (Random) መምረጥ
        q = random.choice(available_questions)
        # 5. የተመረጠውን ጥያቄ ከዝርዝሩ ማስወገድ (እንዳይደገም)
        available_questions.remove(q)
        
        subject = q.get('subject', 'General')
        
        try:
            sent_poll = await bot.send_poll(
                chat_id=chat_id,
                question=f"📚 Subject: {subject}\n\n{q['q']}",
                options=q['o'],
                type='quiz',
                correct_option_id=q['c'],
                is_anonymous=False
            )
            poll_map[sent_poll.poll.id] = {
                "correct": q['c'], 
                "chat_id": chat_id, 
                "winners": [], 
                "all_participants": []
            }
        except Exception as e:
            logging.error(f"Error sending poll: {e}")

        # 1. በየ 4 ደቂቃው (240 ሰከንድ)
        await asyncio.sleep(240)

@dp.poll_answer()
async def on_poll_answer(poll_answer: types.PollAnswer):
    data = poll_map.get(poll_answer.poll_id)
    if not data: return

    user_id = poll_answer.user.id
    user_name = poll_answer.user.full_name
    
    if user_id not in data["all_participants"]:
        data["all_participants"].append(user_id)

    if poll_answer.option_ids[0] == data["correct"]:
        data["winners"].append(user_id)
        is_first = len(data["winners"]) == 1
        points = 8 if is_first else 4
        save_score(user_id, user_name, points)
        
        if is_first:
            await bot.send_message(data["chat_id"], f"GREAT {user_name} ቀድመው በመመለስዎ 8 ነጥብ አግኝተዋል! 🎉")
    else:
        save_score(user_id, user_name, 1.5)

async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
