import asyncio
import random
import traceback

from aiogram.methods import GetChatMember
from asgiref.sync import sync_to_async
from django.core.management.base import BaseCommand
from aiogram import Bot, Dispatcher
from aiogram.client.session.middlewares.request_logging import logger
from ChatModerator.settings import API_TOKEN
from aiogram import Bot, Dispatcher
from aiogram.enums.parse_mode import ParseMode


class Command(BaseCommand):
    help = 'Run bot in polling'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("Bot started!"))
        try:
            main()
        except KeyboardInterrupt:
            self.stdout.write(self.style.NOTICE("Bot stopped!"))


import asyncio
import logging
import sys
from os import getenv

from aiogram import Bot, Dispatcher, Router, types
from aiogram.enums import ParseMode, ChatMemberStatus
from aiogram.filters import CommandStart
from aiogram.types import Message, ChatInviteLink
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.utils.markdown import hbold
from PromotionMaker.models import Post, Button, Chat

# Bot token can be obtained via https://t.me/BotFather
TOKEN = getenv("BOT_TOKEN")

# All handlers should be attached to the Router (or Dispatcher)
dp = Dispatcher()
messages_counter = {

}
last_messages = {

}

router = Router()


async def remove_message(message):
    try:
        if not message.from_user.is_bot:
            is_subscribe = await message.bot(GetChatMember(chat_id=-1002085607318, user_id=message.from_user.id))
            if is_subscribe.status is not ChatMemberStatus.CREATOR and is_subscribe.status is not ChatMemberStatus.MEMBER:
                print("sss")
                message_for_delete = await message.answer(
                    f"""<a href="tg://user?id={message.from_user.id}">{message.from_user.full_name}</a>, щоб ваші повідомлення не видалялись будь-ласка підпишіться на чат: <a href="https://t.me/+0ghGVvJKFsIzNTk8">Тисни сюди щоб вступити в чат</a> .\n\n<b>Наша спільнота {message.chat.title} поступово розвивається, кількість повідомлень зростає, щоб відсіяти спам та ботів ми підключили функцію захисту - Вам достатньо вступити в чат вказаний в повідомленні,щоб ваші повідомлення перестали видалятися.</b>""",
                    parse_mode=ParseMode.HTML)
                waiting_time = random.randint(3, 10)
                await asyncio.sleep(waiting_time)
                await message.delete()
                await asyncio.sleep(waiting_time)
                await message_for_delete.delete()
    except Exception as e:
        print(e)


@router.message()
async def read_messages(message: types.Message) -> None:
    try:
        task = asyncio.create_task(remove_message(message))
        chat_id = message.chat.id
        if chat_id not in messages_counter:
            messages_counter[chat_id] = 0
        messages_counter[chat_id] += 1
        if messages_counter[chat_id] % 5 == 0:  # Перевірка, чи кількість повідомлень кратна 5
            # отримання інформації про чат в базі, перевірка чи він є в базі
            db_chat = Chat.objects.filter(chat_id=chat_id).first()
            # якщо є в базі то main_post буде збережено відповідний пост
            # якщо нема чату, то буде збережено дефолт пост
            main_post = None
            if db_chat is None:
                main_post = Post.objects.first()
            else:
                try:
                    main_post = Post.objects.filter(chat_id=db_chat).first()
                    if main_post is None:
                        main_post = Post.objects.first()
                except Exception as e:
                    main_post = Post.objects.first()
            post = main_post
            keyboard = InlineKeyboardBuilder()
            buttons: list[Button] = post.get_buttons()
            for buttin in buttons:
                keyboard.row(types.InlineKeyboardButton(text=f"{buttin.title}", url=buttin.url))
            mess = await message.bot.send_message(chat_id, text=post.title, reply_markup=keyboard.as_markup())
            try:
                await message.bot.delete_message(chat_id=chat_id, message_id=last_messages[chat_id])
            except Exception as e:
                pass
            last_messages[chat_id] = mess.message_id
    except Exception as e:
        traceback.print_exc()
        # But not all the types is supported to be copied so need to handle it
        pass


async def runner() -> None:
    # Initialize Bot instance with a default parse mode which will be passed to all API calls
    bot = Bot(API_TOKEN, parse_mode=ParseMode.HTML)
    dp.include_router(router)
    # And the run events dispatching
    await dp.start_polling(bot)


def main():
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(runner())
