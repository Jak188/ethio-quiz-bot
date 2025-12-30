import asyncio
import json
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command

API_TOKEN = '8392060519:AAGQ4yLcsHLN9wgP92eZXW3DXPBom-a3Bkw'
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# ጥያቄዎቹን ከፋይል የማንበብ ተግባር
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

@dp.message(Command("start_quiz"))
async def start_quiz_handler(message: types.Message):
    await message.answer("🚀 የጥያቄ ውድድሩ ተጀምሯል! በየ 3 ደቂቃው ይላካል።")
    asyncio.create_task(send_quiz(message.chat.id))

async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
