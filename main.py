import os
import logging
import threading
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
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

def start(update: Update, context: CallbackContext):
    """Обработчик команды /start"""
    welcome_text = """
🤖 Привет! Я бот с искусственным интеллектом Gemini.

Просто напиши мне сообщение, и я постараюсь дать разумный ответ!

Доступные команды:
/start - показать это сообщение
/help - помощь
/reset - очистить историю диалога
    """
    update.message.reply_text(welcome_text)

def help_command(update: Update, context: CallbackContext):
    """Обработчик команды /help"""
    help_text = """
📖 Помощь по боту:

• Просто отправьте текстовое сообщение, и я отвечу
• Бот сохраняет контекст разговора
• Используйте /reset чтобы очистить историю диалога
• Работаю на основе Gemini Pro от Google

Если бот не отвечает, попробуйте команду /reset
    """
    update.message.reply_text(help_text)

def reset_chat(update: Update, context: CallbackContext):
    """Обработчик команды /reset - очищает историю диалога"""
    context.chat_data.clear()
    update.message.reply_text("🔄 История диалога очищена!")

def handle_message(update: Update, context: CallbackContext):
    """Обработчик текстовых сообщений"""
    user_message = update.message.text
    user_id = update.message.from_user.id
    
    logger.info(f"Получено сообщение от {user_id}: {user_message}")
    
    try:
        # Показываем индикатор набора сообщения
        context.bot.send_chat_action(chat_id=update.message.chat_id, action="typing")
        
        # Простой запрос к Gemini (без истории для начала)
        response = model.generate_content(user_message)
        
        # Проверяем блокировку контента
        if response.prompt_feedback.block_reason:
            logger.warning(f"Контент заблокирован: {response.prompt_feedback.block_reason}")
            update.message.reply_text("🚫 Запрос был заблокирован системой безопасности. Попробуйте переформулировать.")
            return
            
        if not response.text:
            update.message.reply_text("🤔 Не получилось сгенерировать ответ. Попробуйте другой запрос.")
            return
            
        # Обрезаем длинные сообщения для Telegram
        if len(response.text) > 4000:
            response_text = response.text[:4000] + "..."
        else:
            response_text = response.text
            
        update.message.reply_text(response_text)
        logger.info(f"Ответ отправлен пользователю {user_id}")
        
    except Exception as e:
        logger.error(f"Ошибка при обработке сообщения: {e}", exc_info=True)
        error_message = "⚠️ Произошла ошибка при обработке запроса. Попробуйте еще раз."
        update.message.reply_text(error_message)

def error_handler(update: Update, context: CallbackContext):
    """Обработчик ошибок"""
    logger.error(f"Ошибка в боте: {context.error}", exc_info=True)

def main():
    """Основная функция для запуска бота"""
    try:
        # Создаем Updater (старый стиль для версии 13.15)
        updater = Updater(TELEGRAM_TOKEN, use_context=True)
        
        # Получаем диспетчер
        dp = updater.dispatcher
        
        # Добавляем обработчики
        dp.add_handler(CommandHandler("start", start))
        dp.add_handler(CommandHandler("help", help_command))
        dp.add_handler(CommandHandler("reset", reset_chat))
        dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))
        
        # Добавляем обработчик ошибок
        dp.add_error_handler(error_handler)
        
        # Запускаем бота
        logger.info("Бот запускается...")
        updater.start_polling()
        
        # Запускаем бота до тех пор, пока пользователь не остановит его
        updater.idle()
        
    except Exception as e:
        logger.error(f"Ошибка при запуске бота: {e}", exc_info=True)
        raise

if __name__ == '__main__':
    main()
