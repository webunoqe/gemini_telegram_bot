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

# Конфигурация
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

# Проверяем наличие токенов
if not TELEGRAM_TOKEN:
    logger.error("TELEGRAM_TOKEN не установлен!")
    raise ValueError("TELEGRAM_TOKEN не найден")

if not GEMINI_API_KEY:
    logger.error("GEMINI_API_KEY не установлен!")
    raise ValueError("GEMINI_API_KEY не найден")

# Настройка Gemini
try:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-pro')
    logger.info("Gemini AI настроен успешно")
except Exception as e:
    logger.error(f"Ошибка настройки Gemini: {e}")
    raise

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    welcome_text = """
🤖 Привет! Я бот с искусственным интеллектом Gemini.

Просто напиши мне сообщение, и я постараюсь дать разумный ответ!

Доступные команды:
/start - показать это сообщение
/help - помощь
/reset - очистить историю диалога
    """
    await update.message.reply_text(welcome_text)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /help"""
    help_text = """
📖 Помощь по боту:

• Просто отправьте текстовое сообщение, и я отвечу
• Бот сохраняет контекст разговора
• Используйте /reset чтобы очистить историю диалога
• Работаю на основе Gemini Pro от Google

Если бот не отвечает, попробуйте команду /reset
    """
    await update.message.reply_text(help_text)

async def reset_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /reset - очищает историю диалога"""
    if 'chat_history' in context.chat_data:
        context.chat_data['chat_history'] = []
    await update.message.reply_text("🔄 История диалога очищена!")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик текстовых сообщений"""
    user_message = update.message.text
    
    try:
        # Показываем индикатор набора сообщения
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
        
        # Инициализируем историю диалога если её нет
        if 'chat_history' not in context.chat_data:
            context.chat_data['chat_history'] = []
        
        # Добавляем сообщение пользователя в историю
        context.chat_data['chat_history'].append({"role": "user", "parts": user_message})
        
        # Создаем чат сессию с историей
        chat = model.start_chat(history=context.chat_data['chat_history'])
        
        # Получаем ответ от Gemini (асинхронно)
        response = await asyncio.get_event_loop().run_in_executor(
            None, 
            lambda: chat.send_message(user_message)
        )
        bot_response = response.text
        
        # Добавляем ответ бота в историю
        context.chat_data['chat_history'].append({"role": "model", "parts": bot_response})
        
        # Ограничиваем размер истории
        if len(context.chat_data['chat_history']) > 10:
            context.chat_data['chat_history'] = context.chat_data['chat_history'][-6:]
        
        # Отправляем ответ пользователю
        await update.message.reply_text(bot_response)
        
    except Exception as e:
        logger.error(f"Error: {e}")
        error_message = "⚠️ Произошла ошибка. Попробуйте еще раз или используйте /reset"
        await update.message.reply_text(error_message)

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик ошибок"""
    logger.error(f"Update {update} caused error {context.error}")

def main():
    """Основная функция для запуска бота"""
    try:
        # Создаем Application
        application = Application.builder().token(TELEGRAM_TOKEN).build()
        
        # Добавляем обработчики
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(CommandHandler("reset", reset_chat))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        
        # Добавляем обработчик ошибок
        application.add_error_handler(error_handler)
        
        # Запускаем бота
        logger.info("Бот запускается...")
        application.run_polling()
        
    except Exception as e:
        logger.error(f"Ошибка при запуске бота: {e}")
        raise

if __name__ == '__main__':
    main()
