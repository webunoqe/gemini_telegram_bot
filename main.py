import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import google.generativeai as genai

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Конфигурация
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

# Настройка Gemini
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-pro')

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
    if 'chat_history' in context.chat_data:
        context.chat_data['chat_history'] = []
    await update.message.reply_text("🔄 История диалога очищена!")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    
    try:
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
        
        if 'chat_history' not in context.chat_data:
            context.chat_data['chat_history'] = []
        
        context.chat_data['chat_history'].append({"role": "user", "parts": user_message})
        
        chat = model.start_chat(history=context.chat_data['chat_history'])
        response = chat.send_message(user_message)
        bot_response = response.text
        
        context.chat_data['chat_history'].append({"role": "model", "parts": bot_response})
        
        if len(context.chat_data['chat_history']) > 10:
            context.chat_data['chat_history'] = context.chat_data['chat_history'][-6:]
        
        await update.message.reply_text(bot_response)
        
    except Exception as e:
        error_message = "⚠️ Произошла ошибка. Попробуйте еще раз или используйте /reset"
        await update.message.reply_text(error_message)

def main():
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("reset", reset_chat))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("Бот запущен...")
    application.run_polling()

if __name__ == '__main__':
    main()