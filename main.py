import asyncio
import json
import logging
import random
import sqlite3
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command

# 1. ቦቱን እና ባለቤቱን መለየት
API_TOKEN = '8392060519:AAEn4tQwJgB2Q7QTNb5fM3XD59bnX34bxKg'
ADMIN_ID = 8394878208 # ያንተ የቴሌግራም ID

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# 2. የዳታቤዝ ዝግጅት
conn = sqlite3.connect('quiz_competition.db', check_same_thread=False)
cursor = conn.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS scores 
                  (user_id INTEGER PRIMARY KEY, name TEXT, points INTEGER)''')
conn.commit()

# 3. የጥያቄዎች ፋይል
with open('questions.json', 'r', encoding='utf-8') as f:
    questions = json.load(f)

running_loops = {} 
poll_data = {} # የትኛው ፖል ከየትኛው ጥያቄ ጋር እንደተያያዘ ለማወቅ

# --- ውጤትን በዳታቤዝ ውስጥ ለማደስ ---
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
        return await message.answer("⚠️ የኩዊዝ ውድድሩ ቀድሞውኑ እየሰራ ነው።")

    running_loops[chat_id] = True
    await message.answer("🎯 የኩዊዝ ውድድር በ Native Mode ተጀምሯል!\nበየ 3 ደቂቃው ጥያቄ ይቀርባል።\nፈጣን መልስ: 8 ነጥብ | ሌላ: 4 ነጥብ")
    asyncio.create_task(quiz_loop(chat_id))

# --- የጥያቄ ዑደት (Loop) ---
async def quiz_loop(chat_id):
    random_questions = list(questions)
    random.shuffle(random_questions)
    
    q_index = 0
    while running_loops.get(chat_id):
        if q_index >= len(random_questions):
            random.shuffle(random_questions)
            q_index = 0
            
        current_q = random_questions[q_index]
        
        # 📝 Native Quiz መላክ (Poll)
        sent_poll = await bot.send_poll(
            chat_id=chat_id,
            question=current_q['q'],
            options=current_q['o'],
            type='quiz',
            correct_option_id=current_q['c'],
            explanation=current_q.get('e', "ትክክለኛ መልስ!"),
            is_anonymous=False # ነጥብ ለመቁጠር ግዴታ False መሆን አለበት
        )
        
        # የፖሉን መረጃ ለጊዜው መያዝ
        poll_data[sent_poll.poll.id] = {
            "correct_option": current_q['c'],
            "answered_count": 0,
            "chat_id": chat_id
        }

        q_index += 1
        await asyncio.sleep(180) # በየ 3 ደቂቃው

# --- ተማሪዎች ኩዊዙን ሲመልሱ ነጥብ መቁጠሪያ ---
@dp.poll_answer()
async def handle_poll_answer(poll_answer: types.PollAnswer):
    p_id = poll_answer.poll_id
    if p_id not in poll_data:
        return

    data = poll_data[p_id]
    user_id = poll_answer.user.id
    user_name = poll_answer.user.first_name

    # ተማሪው የመረጠው መልስ ትክክል መሆኑን ቼክ ማድረግ
    if poll_answer.option_ids[0] == data["correct_option"]:
        data["answered_count"] += 1
        is_first = data["answered_count"] == 1
        points = 8 if is_first else 4
        
        update_score(user_id, user_name, points)
        
        if is_first:
            await bot.send_message(data["chat_id"], f"👏 ጎበዝ {user_name}! ቀድመህ በመመለስህ 8 ነጥብ አግኝተሃል! 🎉")

# --- የ /stop ኮማንድ ---
@dp.message(Command("stop"))
async def cmd_stop(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    running_loops[message.chat.id] = False
    await message.answer("🛑 ውድድሩ ቆሟል። ውጤቶች በዳታቤዝ ተቀምጠዋል።")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
