import logging
import json
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor

# 1. ቦቱን እና ሎጊንግን ሴትአፕ ማድረግ
API_TOKEN = '8392060519:AAEn4tQwJgB2Q7QTNb5fM3XD59bnX34bxKg'
logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# 2. የጥያቄዎች ፋይልን መጫን
with open('questions.json', 'r', encoding='utf-8') as f:
    questions = json.load(f)

# 3. የተማሪዎችን ውጤት ለጊዜው በሜሞሪ ለመያዝ (ለወደፊቱ በDatabase ቢተካ ይመረጣል)
# መዋቅሩ: {user_id: {"score": 0, "current_q": 0}}
user_data = {}

# --- የ /start ኮማንድ ---
@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    user_id = message.from_user.id
    
    # አዲስ ተማሪ ከሆነ ወይም ካቆመበት ለመቀጠል
    if user_id not in user_data:
        user_data[user_id] = {"score": 0, "current_q": 0}
        await message.answer("እንኳን ደህና መጣህ! የዩኒቨርሲቲ መግቢያ ዝግጅት ጥያቄዎችን እንጀምራለን።")
    else:
        q_num = user_data[user_id]["current_q"]
        score = user_data[user_id]["score"]
        await message.answer(f"እንኳን ተመለስክ! ካቆምክበት (ጥያቄ {q_num + 1}) እንቀጥላለን። አሁን ያለህ ውጤት: {score}")

    await send_question(user_id)

# --- ጥያቄ ለመላክ የሚያገለግል Function ---
async def send_question(user_id):
    user_info = user_data[user_id]
    q_index = user_info["current_q"]

    if q_index < len(questions):
        q = questions[q_index]
        options = q["o"]
        
        # ተማሪው እንዲመርጥ Keyboard ማዘጋጀት
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        for option in options:
            keyboard.add(types.KeyboardButton(option))
        
        await bot.send_message(user_id, f"ጥያቄ {q_index + 1}: {q['q']}", reply_markup=keyboard)
    else:
        await bot.send_message(user_id, f"ተጠናቋል! ሁሉንም 820 ጥያቄዎች ጨርሰሃል። የመጨረሻ ውጤትህ: {user_info['score']}")

# --- የ /stop ኮማንድ (ውጤት ሴቭ አድርጎ የሚያቆም) ---
@dp.message_handler(commands=['stop'])
async def stop_quiz(message: types.Message):
    user_id = message.from_user.id
    if user_id in user_data:
        score = user_data[user_id]["score"]
        q_num = user_data[user_id]["current_q"]
        
        # እዚህ ጋር ዳታቤዝ ካለህ ወደ ዳታቤዝ ሴቭ ታደርጋለህ
        await message.answer(
            f"ጥያቄዎች ቆመዋል! 🛑\n"
            f"ያመጣኸው ውጤት: {score}\n"
            f"እስካሁን {q_num} ጥያቄዎችን ሰርተሃል።\n"
            f"ለመቀጠል /start በል!"
        )
        # Keyboardዱን ለማጥፋት
        await bot.send_message(user_id, "ቻው!", reply_markup=types.ReplyKeyboardRemove())
    else:
        await message.answer("ገና ምንም ጥያቄ አልጀመርክም። ለመጀመር /start በል።")

# --- የመልስ መቀበያ (መደበኛ መልዕክት) ---
@dp.message_handler()
async def handle_answer(message: types.Message):
    user_id = message.from_user.id
    if user_id not in user_data:
        return

    user_info = user_data[user_id]
    q_index = user_info["current_q"]
    
    if q_index < len(questions):
        correct_answer_index = questions[q_index]["c"]
        correct_answer_text = questions[q_index]["o"][correct_answer_index]
        explanation = questions[q_index]["e"]

        if message.text == correct_answer_text:
            user_info["score"] += 1
            await message.answer("ትክክል ነህ! ✅")
        else:
            await message.answer(f"ተሳስተሃል። ❌ ትክክለኛው መልስ: {correct_answer_text}\n\nማብራሪያ: {explanation}")

        # ወደ ቀጣዩ ጥያቄ ማለፍ
        user_info["current_q"] += 1
        await send_question(user_id)

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
