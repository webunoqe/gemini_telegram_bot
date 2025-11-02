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

# Конфигурация (получаем из переменных окружения)
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

# Проверяем наличие токенов
if not TELEGRAM_TOKEN:
    logger.error("TELEGRAM_TOKEN не установлен!")
if not GEMINI_API_KEY:
    logger.error("GEMINI_API_KEY не установлен!")

# Настройка Gemini
try:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-pro')
    logger.info("Gemini AI настроен успешно")
except Exception as e:
    logger.error(f"Ошибка настройки Gemini: {e}")

# Команды бота
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
    chat_id = update.message.chat_id
    
    logger.info(f"Получено сообщение от {chat_id}: {user_message}")
    
    try:
        # Показываем индикатор набора сообщения
        context.bot.send_chat_action(chat_id=chat_id, action="typing")
        
        # Инициализируем историю диалога если её нет
        if 'chat_history' not in context.chat_data:
            context.chat_data['chat_history'] = []
        
        # Создаем чат сессию с историей
        chat = model.start_chat(history=context.chat_data['chat_history'])
        
        # Получаем ответ от Gemini
        response = chat.send_message(user_message)
        bot_response = response.text
        
        # Обновляем историю диалога
        context.chat_data['chat_history'].extend([
            {"role": "user", "parts": user_message},
            {"role": "model", "parts": bot_response}
        ])
        
        # Ограничиваем размер истории чтобы не превышать лимиты
        if len(context.chat_data['chat_history']) > 10:
            context.chat_data['chat_history'] = context.chat_data['chat_history'][-6:]
        
        # Отправляем ответ пользователю
        update.message.reply_text(bot_response)
        logger.info(f"Отправлен ответ пользователю {chat_id}")
        
    except Exception as e:
        logger.error(f"Ошибка при обработке сообщения: {e}")
        error_message = "⚠️ Произошла ошибка при обработке запроса. Попробуйте еще раз или используйте /reset"
        update.message.reply_text(error_message)

def error_handler(update: Update, context: CallbackContext):
    """Обработчик ошибок"""
    logger.error(f"Ошибка вызвана апдейтом {update}: {context.error}")

def main():
    """Основная функция для запуска бота"""
    try:
        # Создаем Updater и передаем ему токен бота
        updater = Updater(TELEGRAM_TOKEN, use_context=True)
        
        # Получаем диспетчер для регистрации обработчиков
        dp = updater.dispatcher
        
        # Добавляем обработчики команд
        dp.add_handler(CommandHandler("start", start))
        dp.add_handler(CommandHandler("help", help_command))
        dp.add_handler(CommandHandler("reset", reset_chat))
        
        # Добавляем обработчик текстовых сообщений
        dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))
        
        # Добавляем обработчик ошибок
        dp.add_error_handler(error_handler)
        
        # Запускаем бота
        logger.info("Бот запускается...")
        updater.start_polling()
        
        # Запускаем бота до тех пор, пока пользователь не остановит его
        updater.idle()
        
    except Exception as e:
        logger.error(f"Ошибка при запуске бота: {e}")

if __name__ == '__main__':
    main()
