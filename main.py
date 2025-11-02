import os
import logging
import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import google.generativeai as genai

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Токены из переменных окружения
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

# Проверка токенов
if not TELEGRAM_TOKEN:
    logger.error("❌ TELEGRAM_TOKEN не найден!")
    exit(1)

if not GEMINI_API_KEY:
    logger.error("❌ GEMINI_API_KEY не найден!")
    exit(1)

# Инициализация Gemini
try:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-pro')
    logger.info("✅ Gemini AI настроен успешно")
except Exception as e:
    logger.error(f"❌ Ошибка настройки Gemini: {e}")
    exit(1)

# Команды бота
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    welcome_text = """
🤖 Привет! Я бот с искусственным интеллектом Gemini.

Просто напиши мне сообщение, и я постараюсь дать разумный ответ!

Команды:
/start - это сообщение
/help - помощь
    """
    await update.message.reply_text(welcome_text)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /help"""
    help_text = """
📖 Помощь по боту:

• Просто напиши мне сообщение - я отвечу
• Работаю на основе Gemini Pro от Google

Начни общение с простого "Привет!" 👍
    """
    await update.message.reply_text(help_text)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик текстовых сообщений"""
    user_message = update.message.text
    user_id = update.effective_user.id
    
    logger.info(f"📨 Сообщение от {user_id}: {user_message}")
    
    try:
        # Показываем что бот печатает
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
        
        # Простой запрос к Gemini (без сложной истории)
        response = await asyncio.get_event_loop().run_in_executor(
            None, 
            lambda: model.generate_content(user_message)
        )
        
        if response.text:
            # Обрезаем длинные сообщения для Telegram
            if len(response.text) > 4000:
                bot_response = response.text[:4000] + "..."
            else:
                bot_response = response.text
            
            await update.message.reply_text(bot_response)
            logger.info(f"✅ Ответ отправлен пользователю {user_id}")
        else:
            await update.message.reply_text("❌ Не удалось получить ответ от AI")
            logger.warning("Пустой ответ от Gemini")
            
    except Exception as e:
        logger.error(f"❌ Ошибка: {e}")
        await update.message.reply_text("⚠️ Временная ошибка. Попробуйте еще раз.")

def main():
    """Основная функция запуска бота"""
    try:
        logger.info("🚀 Запуск бота...")
        
        # Создаем Application
        application = Application.builder().token(TELEGRAM_TOKEN).build()
        
        # Добавляем обработчики
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        
        # Запускаем бота
        logger.info("✅ Бот успешно запущен и работает!")
        application.run_polling()
        
    except Exception as e:
        logger.error(f"💥 Критическая ошибка при запуске: {e}")
        exit(1)

if __name__ == '__main__':
    main()
