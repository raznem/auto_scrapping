import logging

from telegram.ext import CommandHandler, Filters, MessageHandler, Updater

from scrap import dump_links, prepare_dict, send_new_ads

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

logger = logging.getLogger(__name__)

INTERVAL = 60

jobs = {}  # Dict for the APScheduler jobs


def error(update, context):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, context.error)


def callback_alarm(context):
    context.job_queue.scheduler.print_jobs()
    job = context.job
    chat_id = job.context["chat_id"]
    send_new_ads(context, chat_id, LINKS_DICT)


def callback_timer(update, context):
    chat_id = update.message.chat_id
    context.user_data["chat_id"] = chat_id
    context.bot.send_message(chat_id=chat_id, text="Starting!")
    job_name = str(chat_id)
    jobs[job_name] = context.job_queue.run_repeating(
        callback_alarm, INTERVAL, first=1, context=context.user_data, name=job_name
    )
    # context.job_queue.scheduler.print_jobs()


def stop_timer(update, context):
    chat_id = update.message.chat_id
    context.bot.send_message(chat_id=chat_id, text="Stoped!")
    jobs[str(chat_id)].remove()
    dump_links(LINKS_DICT)


LINKS_DICT = prepare_dict()

with open("tg_token.txt", "r") as f:
    TOKEN = f.read()

updater = Updater(TOKEN, use_context=True)

dp = updater.dispatcher

dp.add_handler(CommandHandler("start", callback_timer))
dp.add_handler(CommandHandler("stop", stop_timer))
dp.add_error_handler(error)

updater.start_polling()

updater.idle()
