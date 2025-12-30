import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.types import PollAnswer
from datetime import datetime

# ያንተን Token እዚህ ጋር አስገብተናል
API_TOKEN = '8392060519:AAGQ4yLcsHLN9wgP92eZXW3DXPBom-a3Bkw'

# Logging - ስህተቶች ካሉ ለማየት
logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# የተጠቃሚዎች ነጥብ ማከማቻ (ለጊዜው በMemory፣ በኋላ በDatabase እንቀይረዋለን)
user_scores = {}
# የጥያቄዎች ዝርዝር (Database)
questions = [
    {
        "question": "ከሚከተሉት ውስጥ የቬክተር (Vector) መጠን የሆነው የቱ ነው?",
        "options": ["Speed", "Mass", "Velocity", "Time"],
        "correct_option_id": 2,
        "explanation": "Velocity የቬክተር መጠን ነው ምክንያቱም አቅጣጫ እና መጠን ስላለው።"
    },
    {
        "question": "The capital city of Ethiopia is ____.",
        "options": ["Adama", "Addis Ababa", "Gondar", "Hawassa"],
        "correct_option_id": 1,
        "explanation": "Addis Ababa is the capital city of Ethiopia, established in 1886."
    }
]

# በየ 3 ደቂቃው ጥያቄ የሚልክ Function
async def send_quiz_periodically(chat_id):
    index = 0
    while True:
        q = questions[index % len(questions)]
        await bot.send_poll(
            chat_id=chat_id,
            question=q["question"],
            options=q["options"],
            type='quiz',
            correct_option_id=q["correct_option_id"],
            explanation=q["explanation"],
            is_anonymous=False  # ማን እንደመለሰ ለማወቅ
        )
        index += 1
        await asyncio.sleep(180) # 180 ሰከንድ (3 ደቂቃ) ይጠብቃል

# ቦቱ ግሩፕ ውስጥ ሲጀመር
@dp.message(commands=['start_quiz'])
async def start_cmd(message: types.Message):
    await message.answer("✅ የ3 ደቂቃ ጥያቄ ተጀምሯል! ተዘጋጁ።")
    asyncio.create_task(send_quiz_periodically(message.chat.id))

# ውጤት ለማየት
@dp.message(commands=['rank'])
async def show_rank(message: types.Message):
    sorted_scores = sorted(user_scores.items(), key=lambda x: x[1], reverse=True)
    text = "🏆 የደረጃ ሰንጠረዥ (Top Scorers):\n\n"
    for i, (user_id, score) in enumerate(sorted_scores[:10], 1):
        text += f"{i}. የተጠቃሚ ID {user_id}: {score} ነጥብ\n"
    await message.answer(text)

# መልስ ሲሰጥ ነጥብ ለመያዝ
@dp.poll_answer()
async def handle_poll_answer(quiz_answer: PollAnswer):
    user_id = quiz_answer.user.id
    # እዚህ ጋር ትክክል መሆኑን እና ፍጥነቱን መለካት ይቻላል
    user_scores[user_id] = user_scores.get(user_id, 0) + 1

if __name__ == '__main__':
    dp.run_polling(bot)
