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

# 3. ጥያቄዎችን ከ bot.py ላይ መጫን እና በዘርፍ መለየት
def load_and_filter_questions():
    # አንተ የሰጠኸኝ ጥያቄዎች ዝርዝር
    raw_data = [
        {"q": "If f(x) = 3x + 2, find f(4).", "o": ["12", "14", "10", "16"], "c": 1, "e": "f(4) = 3(4) + 2 = 14."},
        {"q": "Solve for x: x^2 = 25.", "o": ["5 only", "-5 only", "5 and -5", "0"], "c": 2, "e": "Both 5 and -5 squared equal 25."},
        {"q": "What is the derivative of x^3?", "o": ["x^2", "3x", "3x^2", "2x^3"], "c": 2, "e": "3x^2 using power rule."},
        {"q": "In Math, what is 25% of 200?", "o": ["25", "40", "50", "75"], "c": 2, "e": "0.25 * 200 = 50."},
        {"q": "What is the value of pi (to 2 decimal places)?", "o": ["3.12", "3.14", "3.16", "3.18"], "c": 1, "e": "Pi is 3.14."},
        {"q": "Choose the synonym for 'Huge':", "o": ["Tiny", "Massive", "Small", "Short"], "c": 1, "e": "Massive means huge."},
        {"q": "Identify the adverb in: 'She ran fast.'", "o": ["She", "ran", "fast", "runs"], "c": 2, "e": "Fast is the adverb."},
        {"q": "Which country is the largest in the world by land area?", "o": ["USA", "China", "Russia", "Canada"], "c": 2, "e": "Russia is the largest."},
        {"q": "Who was the 'Liberator' of South America?", "o": ["Napoleon", "Simon Bolivar", "San Martin", "Columbus"], "c": 1, "e": "Simon Bolivar."},
        {"q": "What is the capital of France?", "o": ["Berlin", "Madrid", "Paris", "Rome"], "c": 2, "e": "Paris is the capital."},
        # ... ሌሎች ጥያቄዎች ቢኖሩም ኮዱ በራሱ ይለያቸዋል
    ]
    
    filtered = []
    for q in raw_data:
        txt = q['q'].lower()
        # የትምህርት ዘርፎችን በቁልፍ ቃላት መለየት
        if any(k in txt for k in ['f(x)', 'x^', 'solve', 'math', '%', 'pi', 'value of']):
            q['sub'] = 'Mathematics'
        elif any(k in txt for k in ['synonym', 'adverb', 'grammar', 'english', 'identify']):
            q['sub'] = 'English'
        elif any(k in txt for k in ['country', 'land area', 'capital', 'geography', 'river']):
            q['sub'] = 'Geography'
        elif any(k in txt for k in ['history', 'liberator', 'war', 'ancient', 'who was']):
            q['sub'] = 'History'
        else:
            q['sub'] = None # ሌሎች ትምህርቶች (ለምሳሌ ፊዚክስ) እዚህ ይገባሉ
            
        # አንተ የፈለግካቸው 4ቱ ብቻ እንዲመረጡ
        if q['sub'] in ['English', 'Mathematics', 'Geography', 'History']:
            filtered.append(q)
    return filtered

questions = load_and_filter_questions()

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
    if message.from_user.id not in ADMIN_IDS: return
    chat_id = message.chat.id
    if active_loops.get(chat_id): return
    
    active_loops[chat_id] = True
    await message.answer("🚀 ውድድሩ ተጀመረ!\n📚 ትምህርቶች: English, Math, Geography, History\n⏰ በየ 4 ደቂቃው ጥያቄ ይላካል።")
    asyncio.create_task(quiz_timer(chat_id))

@dp.message(Command("stop"))
async def cmd_stop(message: types.Message):
    if message.from_user.id not in ADMIN_IDS: return
    active_loops[message.chat.id] = False
    await message.answer("🛑 ውድድሩ ቆሟል።")

@dp.message(Command("rank"))
async def cmd_rank(message: types.Message):
    cursor.execute("SELECT name, points FROM scores ORDER BY points DESC LIMIT 10")
    rows = cursor.fetchall()
    text = "🏆 **የደረጃ ሰንጠረዥ (Top 10)** 🏆\n\n"
    for i, row in enumerate(rows, 1):
        text += f"{i}. {row[0]} — {round(row[1], 1)} ነጥብ\n"
    await message.answer(text)

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
        try:
            sent_poll = await bot.send_poll(
                chat_id=chat_id,
                question=f"📖 Subject: {q['sub']}\n\n{q['q']}",
                options=q['o'],
                type='quiz',
                correct_option_id=q['c'],
                explanation=q.get('e', ""),
                is_anonymous=False
            )
            poll_map[sent_poll.poll.id] = {"correct": q['c'], "chat_id": chat_id, "winners": []}
            idx += 1
        except: pass
        await asyncio.sleep(240) # 4 ደቂቃ

@dp.poll_answer()
async def on_poll_answer(poll_answer: types.PollAnswer):
    data = poll_map.get(poll_answer.poll_id)
    if not data: return
    
    user_id = poll_answer.user.id
    user_name = poll_answer.user.full_name

    if poll_answer.option_ids[0] == data["correct"]:
        data["winners"].append(user_id)
        is_first = len(data["winners"]) == 1
        points = 8 if is_first else 4
        save_score(user_id, user_name, points)
        if is_first:
            await bot.send_message(data["chat_id"], f"👏 ጎበዝ {poll_answer.user.first_name}! +8 ነጥብ! 🎉")
    else:
        # ለተሳተፈ (ለተሳሳተ) ሰው 1.5 ነጥብ
        save_score(user_id, user_name, 1.5)

async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
