import asyncio
import json
import logging
import sys
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import ReplyKeyboardBuilder

# 1. ቦቱን እና ሎጊንግን ሴትአፕ ማድረግ
# ያቀበልከኝን ቶክን እዚህ አስገብቼዋለሁ
API_TOKEN = '8392060519:AAFMzK7HGRsZ-BkajlD6wcQ9W6Bq8BqkzNM'
logging.basicConfig(level=logging.INFO, stream=sys.stdout)

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# 2. የጥያቄዎች ፋይልን መጫን
# ፋይሉ 'questions.json' ተብሎ በፕሮጀክትህ ውስጥ መቀመጥ አለበት
try:
    with open('questions.json', 'r', encoding='utf-8') as f:
        questions = json.load(f)
except Exception as e:
    logging.error(f"JSON ፋይሉን መጫን አልተቻለም: {e}")
    questions = []

# 3. የተማሪዎችን ውጤት ለመያዝ (In-memory Storage)
# ቦቱ ሪስታርት ሲያደርግ ይህ መረጃ ይጠፋል። ለቋሚነት ዳታቤዝ ያስፈልጋል።
user_data = {}

# --- የ /start ኮማንድ ---
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    
    if user_id not in user_data:
        user_data[user_id] = {"score": 0, "current_q": 0}
        await message.answer("እንኳን ደህና መጣህ! የዩኒቨርሲቲ መግቢያ ዝግጅት 820 ጥያቄዎችን እንጀምራለን። 🚀")
    else:
        info = user_data[user_id]
        await message.answer(f"እንኳን ተመለስክ! ካቆምክበት (ጥያቄ {info['current_q'] + 1}) እንቀጥላለን። \nያለህ ውጤት: {info['score']}")

    await send_question(message)

# --- ጥያቄ ለመላክ የሚያገለግል Function ---
async def send_question(message: types.Message):
    user_id = message.from_user.id
    user_info = user_data[user_id]
    q_index = user_info["current_q"]

    if q_index < len(questions):
        q = questions[q_index]
        
        # Keyboard ማዘጋጀት (አማራጮቹን ለማሳየት)
        builder = ReplyKeyboardBuilder()
        for option in q["o"]:
            builder.add(types.KeyboardButton(text=option))
        builder.adjust(2) # በአንድ መስመር ሁለት አማራጮች እንዲሆኑ
        
        await message.answer(
            f"ጥያቄ {q_index + 1}:\n\n{q['q']}",
            reply_markup=builder.as_markup(resize_keyboard=True)
        )
    else:
        await message.answer(f"ድንቅ ነው! ሁሉንም 820 ጥያቄዎች ጨርሰሃል። 🎉\nየመጨረሻ ውጤትህ: {user_info['score']}")

# --- የ /stop ኮማንድ (ውጤት አሳይቶ የሚያቆም) ---
@dp.message(Command("stop"))
async def cmd_stop(message: types.Message):
    user_id = message.from_user.id
    if user_id in user_data:
        info = user_data[user_id]
        await message.answer(
            f"ጥያቄዎች ለጊዜው ቆመዋል! 🛑\n"
            f"እስካሁን ያመጣኸው ውጤት: {info['score']}\n"
            f"የደረስክበት ጥያቄ: {info['current_q'] + 1}\n\n"
            f"ለመቀጠል በፈለግክ ጊዜ /start በል!",
            reply_markup=types.ReplyKeyboardRemove()
        )
    else:
        await message.answer("ገና ጥያቄ አልጀመርክም። ለመጀመር /start በል።")

# --- የተማሪውን መልስ መቀበል እና ማረም ---
@dp.message()
async def handle_answer(message: types.Message):
    user_id = message.from_user.id
    if user_id not in user_data:
        return

    user_info = user_data[user_id]
    q_index = user_info["current_q"]

    if q_index < len(questions):
        correct_idx = questions[q_index]["c"]
        correct_text = questions[q_index]["o"][correct_idx]
        explanation = questions[q_index]["e"]

        # መልሱ ትክክል መሆኑን ቼክ ማድረግ
        if message.text == correct_text:
            user_info["score"] += 1
            await message.answer("ትክክል ነህ! ✅")
        else:
            await message.answer(f"ተሳስተሃል። ❌\nትክክለኛው መልስ: {correct_text}\n\nማብራሪያ: {explanation}")

        # ወደ ቀጣዩ ጥያቄ ማለፍ
        user_info["current_q"] += 1
        await send_question(message)

# --- ቦቱን የሚያስነሳ Main Function ---
async def main():
    logging.info("ቦቱ መስራት ጀምሯል...")
    # የቆዩ ሜሴጆችን ችላ እንዲል skip_updates=True በ Dispatcher በኩል ይሰራጃል
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("ቦቱ ቆሟል!")
