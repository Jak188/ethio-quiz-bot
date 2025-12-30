import asyncio, json, logging, sqlite3, random
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message, PollAnswer

API_TOKEN = '8392060519:AAFMzK7HGRsZ-BkajlD6wcQ9W6Bq8BqkzNM'
logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# --- DATABASE ---
def init_db():
    conn = sqlite3.connect('quiz_bot.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users 
                      (user_id INTEGER PRIMARY KEY, username TEXT, full_name TEXT, score INTEGER DEFAULT 0)''')
    conn.commit()
    conn.close()

def add_score(user_id, username, full_name):
    conn = sqlite3.connect('quiz_bot.db')
    cursor = conn.cursor()
    cursor.execute('''INSERT INTO users (user_id, username, full_name, score) VALUES (?, ?, ?, 8)
                      ON CONFLICT(user_id) DO UPDATE SET score = score + 8''', (user_id, username, full_name))
    conn.commit()
    conn.close()

# --- QUIZ LOGIC ---
active_polls = {} # የትኛው ጥያቄ የትኛው እንደሆነ ለማወቅ

def load_questions():
    with open('questions.json', 'r', encoding='utf-8') as f:
        return json.load(f)

async def send_quiz(chat_id):
    questions = load_questions()
    while True:
        q = random.choice(questions) # Random ጥያቄ
        poll = await bot.send_poll(
            chat_id=chat_id,
            question=f"📝 {q['q']}",
            options=q["o"],
            type='quiz',
            correct_option_id=q["c"],
            explanation=f"💡 Explanation: {q['e']}\n✨ በርታ/ች! ትችላለህ/ያለሽ!",
            is_anonymous=False
        )
        # የትክክለኛውን መልስ ቁጥር ለጊዜው እንያዝ
        active_polls[poll.poll.id] = q["c"]
        await asyncio.sleep(120) # በየ 2 ደቂቃው

@dp.poll_answer()
async def handle_poll_answer(poll_answer: PollAnswer):
    correct_id = active_polls.get(poll_answer.poll_id)
    if poll_answer.option_ids[0] == correct_id:
        user = poll_answer.user
        add_score(user.id, user.username, user.full_name)
        # ለሞራል መልእክት መላክ ይቻላል (ለግሩፕ ከሆነ)

@dp.message(Command("rank"))
async def cmd_rank(message: Message):
    conn = sqlite3.connect('quiz_bot.db')
    cursor = conn.cursor()
    cursor.execute('SELECT full_name, score FROM users ORDER BY score DESC LIMIT 10')
    ranks = cursor.fetchall()
    text = "🏆 **የመሪዎች ሰሌዳ (Top 10)** 🏆\n\n"
    for i, (name, score) in enumerate(ranks, 1):
        text += f"{i}. {name} — {score} ነጥብ 🌟\n"
    await message.answer(text, parse_mode="Markdown")

@dp.message(Command("start_quiz"))
async def start(message: Message):
    await message.answer("🚀 የ Entrance ዝግጅት ተጀመረ! ፈጣን ሁኑ!")
    asyncio.create_task(send_quiz(message.chat.id))

async def main():
    init_db()
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
