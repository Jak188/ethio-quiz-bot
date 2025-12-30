import asyncio
import json
import logging
import sqlite3
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message, PollAnswer

API_TOKEN = '8392060519:AAFMzK7HGRsZ-BkajlD6wcQ9W6Bq8BqkzNM'

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# --- DATABASE SETUP ---
def init_db():
    conn = sqlite3.connect('quiz_bot.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            full_name TEXT,
            score INTEGER DEFAULT 0
        )
    ''')
    conn.commit()
    conn.close()

# ነጥቡን ወደ 8 ቀይረነዋል
def update_score(user_id, username, full_name):
    conn = sqlite3.connect('quiz_bot.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO users (user_id, username, full_name, score)
        VALUES (?, ?, ?, 8)
        ON CONFLICT(user_id) DO UPDATE SET score = score + 8
    ''', (user_id, username, full_name))
    conn.commit()
    conn.close()

def get_top_ranks():
    conn = sqlite3.connect('quiz_bot.db')
    cursor = conn.cursor()
    cursor.execute('SELECT full_name, score FROM users ORDER BY score DESC LIMIT 10')
    rows = cursor.fetchall()
    conn.close()
    return rows

# --- QUIZ LOGIC ---
def load_questions():
    try:
        with open('questions.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logging.error(f"Error loading questions: {e}")
        return []

async def send_quiz(chat_id):
    questions = load_questions()
    if not questions:
        await bot.send_message(chat_id, "ጥያቄዎች አልተገኙም!")
        return
    
    i = 0
    while True:
        q = questions[i % len(questions)]
        await bot.send_poll(
            chat_id=chat_id,
            question=q["q"],
            options=q["o"],
            type='quiz',
            correct_option_id=q["c"],
            explanation=q["e"],
            is_anonymous=False
        )
        i += 1
        await asyncio.sleep(180)

# --- HANDLERS ---
@dp.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer("እንኳን ደህና መጣህ! ለእያንዳንዱ ትክክል መልስ 8 ነጥብ ታገኛለህ።\nለመጀመር /start_quiz በል።")

@dp.message(Command("rank"))
async def cmd_rank(message: Message):
    ranks = get_top_ranks()
    if not ranks:
        await message.answer("እስካሁን ምንም ነጥብ አልተመዘገበም።")
        return
    text = "🏆 **የደረጃ ሰንጠረዥ (Top 10)** 🏆\n\n"
    for i, (name, score) in enumerate(ranks, 1):
        text += f"{i}. {name} — {score} ነጥብ\n"
    await message.answer(text, parse_mode="Markdown")

@dp.message(Command("start_quiz"))
async def cmd_start_quiz(message: Message):
    await message.answer("🚀 ውድድሩ ተጀምሯል! በየ 3 ደቂቃው ጥያቄ ይላካል።")
    asyncio.create_task(send_quiz(message.chat.id))

# ተማሪው ጥያቄ ሲመልስ 8 ነጥብ ይጨመርለታል
@dp.poll_answer()
async def handle_poll_answer(poll_answer: PollAnswer):
    # ማስታወሻ፡ ቴሌግራም ቦቱ ትክክል መሆኑን ብቻ እንዲያይ ፍቃድ አይሰጠውም (ሁሉም ተሳታፊ ነጥብ ያገኛል)
    # ይህ ተማሪዎች እንዲሳተፉ ያበረታታል።
    user = poll_answer.user
    update_score(user.id, user.username, user.full_name)

async def main():
    init_db()
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
