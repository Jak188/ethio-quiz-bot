import asyncio
import logging
import sqlite3
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message

# TOKEN
API_TOKEN = '8392060519:AAGQ4yLcsHLN9wgP92eZXW3DXPBom-a3Bkw'

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Database setup
conn = sqlite3.connect('quiz_bot.db', check_same_thread=False)
cursor = conn.cursor()
cursor.execute('CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, score INTEGER DEFAULT 0)')
conn.commit()

# Sample Questions
questions = [
    {"q": "የኢትዮጵያ ረጅሙ ተራራ ማን ይባላል?", "o": ["ባቲ", "ራስ ዳሽን", "ቱሉ ዲምቱ", "ጭልጭል"], "c": 1, "e": "ራስ ዳሽን 4,550 ሜትር ከፍታ ያለው የኢትዮጵያ ከፍተኛው ተራራ ነው።"},
    {"q": "What is the square root of 144?", "o": ["10", "11", "12", "14"], "c": 2, "e": "Because 12 * 12 = 144."}
]

async def send_quiz(chat_id):
    i = 0
    while True:
        try:
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
            await asyncio.sleep(180) # በየ 3 ደቂቃው
        except Exception as e:
            logging.error(f"Error sending poll: {e}")
            await asyncio.sleep(10)

# አዲሱ የአጻጻፍ ስልት (Command filter)
@dp.message(Command("start_quiz"))
async def start_quiz_handler(message: Message):
    await message.answer("🚀 ጥያቄው ተጀምሯል! በየ 3 ደቂቃው ግሩፑ ላይ ይላካል።")
    asyncio.create_task(send_quiz(message.chat.id))

@dp.message(Command("start"))
async def welcome_handler(message: Message):
    await message.answer("ሰላም! እኔ የ9-12 ክፍል የጥያቄ ቦት ነኝ። በግሩፕ ውስጥ ጥያቄ ለመጀመር /start_quiz ይበሉ።")

async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
