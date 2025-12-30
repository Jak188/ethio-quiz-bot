import asyncio
import json
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command

# አዲሱ Token እዚህ ጋር ገብቷል
API_TOKEN = '8392060519:AAFMzK7HGRsZ-BkajlD6wcQ9W6Bq8BqkzNM'

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

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
        await bot.send_message(chat_id, "ጥያቄዎች አልተገኙም! እባክህ questions.json ፋይልን አረጋግጥ።")
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
        await asyncio.sleep(180) # በየ 3 ደቂቃው

@dp.message(Command("start_quiz"))
async def start_quiz_handler(message: types.Message):
    await message.answer("🚀 የጥያቄ ውድድሩ በአዲሱ Token ተጀምሯል! በየ 3 ደቂቃው ይላካል።")
    asyncio.create_task(send_quiz(message.chat.id))

@dp.message(Command("start"))
async def welcome(message: types.Message):
    await message.answer("እንኳን ደህና መጣህ! የጥያቄ ውድድር ለመጀመር /start_quiz በል።")

async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
