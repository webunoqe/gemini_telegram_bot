import os
import logging
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
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
    logger.error("❌ TELEGRAM_TOKEN не найден! Проверьте переменные окружения.")
    exit(1)

if not GEMINI_API_KEY:
    logger.error("❌ GEMINI_API_KEY не найден! Проверьте переменные окружения.")
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
def start(update: Update, context: CallbackContext):
    """Обработчик команды /start"""
    welcome_text = """
🤖 Привет! Я бот с искусственным интеллектом Gemini.

Просто напиши мне сообщение, и я постараюсь дать разумный ответ!

Команды:
/start - это сообщение
/help - помощь
/reset - очистить историю
    """
    update.message.reply_text(welcome_text)

def help_command(update: Update, context: CallbackContext):
    """Обработчик команды /help"""
    help_text = """
📖 Помощь по боту:

• Просто напиши мне сообщение - я отвечу
• Я помню контекст разговора
• Используй /reset чтобы очистить историю
• Работаю на основе Gemini Pro от Google

Начни общение с простого "Привет!" 👍
    """
    update.message.reply_text(help_text)

def reset_chat(update: Update, context: CallbackContext):
    """Обработчик команды /reset"""
    context.chat_data.clear()
    update.message.reply_text("🔄 История диалога очищена! Начнем заново.")

def handle_message(update: Update, context: CallbackContext):
    """Обработчик текстовых сообщений"""
    user_message = update.message.text
    user_id = update.message.from_user.id
    
    logger.info(f"📨 Сообщение от {user_id}: {user_message}")
    
    try:
        # Показываем что бот печатает
        context.bot.send_chat_action(chat_id=update.message.chat_id, action="typing")
        
        # Инициализируем историю если её нет
        if 'history' not in context.chat_data:
            context.chat_data['history'] = []
        
        # Добавляем сообщение пользователя в историю
        context.chat_data['history'].append({"role": "user", "parts": user_message})
        
        # Создаем чат с историей
        chat = model.start_chat(history=context.chat_data['history'])
        
        # Получаем ответ от Gemini
        response = chat.send_message(user_message)
        bot_response = response.text
        
        # Добавляем ответ бота в историю
        context.chat_data['history'].append({"role": "model", "parts": bot_response})
        
        # Ограничиваем размер истории (последние 6 сообщений)
        if len(context.chat_data['history']) > 6:
            context.chat_data['history'] = context.chat_data['history'][-6:]
        
        # Отправляем ответ
        update.message.reply_text(bot_response)
        logger.info(f"✅ Ответ отправлен пользователю {user_id}")
        
    except Exception as e:
        logger.error(f"❌ Ошибка: {e}", exc_info=True)
        
        # Пробуем отправить сообщение без истории
        try:
            response = model.generate_content(user_message)
            if response.text:
                update.message.reply_text(response.text)
                logger.info("✅ Ответ отправлен (без истории)")
            else:
                update.message.reply_text("❌ Не удалось получить ответ от AI")
        except:
            update.message.reply_text("⚠️ Ошибка соединения. Попробуйте позже или используйте /reset")

def error_handler(update: Update, context: CallbackContext):
    """Обработчик ошибок"""
    logger.error(f"🔥 Ошибка бота: {context.error}")

def main():
    """Основная функция запуска бота"""
    try:
        logger.info("🚀 Запуск бота...")
        
        # Создаем апдейтер
        updater = Updater(TELEGRAM_TOKEN, use_context=True)
        
        # Получаем диспетчер
        dp = updater.dispatcher
        
        # Добавляем обработчики
        dp.add_handler(CommandHandler("start", start))
        dp.add_handler(CommandHandler("help", help_command))
        dp.add_handler(CommandHandler("reset", reset_chat))
        dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))
        
        # Обработчик ошибок
        dp.add_error_handler(error_handler)
        
        # Запускаем бота
        updater.start_polling()
        logger.info("✅ Бот успешно запущен и работает!")
        
        # Работаем до остановки
        updater.idle()
        
    except Exception as e:
        logger.error(f"💥 Критическая ошибка при запуске: {e}")
        exit(1)

if __name__ == '__main__':
    main()
