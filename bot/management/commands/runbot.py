import asyncio
import random
import traceback
from datetime import datetime

from django.utils import timezone
from aiogram.client.default import DefaultBotProperties
from aiogram.methods import GetChatMember
from aiogram.utils.serialization import deserialize_telegram_object
from asgiref.sync import sync_to_async
from django.core.management.base import BaseCommand
from aiogram import Bot, Dispatcher, filters
from aiogram.client.session.middlewares.request_logging import logger
from django.db.models import Q
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
from PromotionMaker.models import Post, Button, Chat, PromotionPost
from ChatModerator.settings import API_TOKEN,PROMOTER_TOKEN
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


# Bot token can be obtained via https://t.me/BotFather
TOKEN = getenv("BOT_TOKEN")
bot_helper_promoter = Bot(PROMOTER_TOKEN)
# All handlers should be attached to the Router (or Dispatcher)
dp = Dispatcher()
messages_counter = {

}
last_messages = {

}

router = Router()


async def remove_message(message, chat_for_subscribe, subscribe_link):
    try:

        if not message.from_user.is_bot and chat_for_subscribe is not None:
            is_subscribe = await message.bot(GetChatMember(chat_id=chat_for_subscribe, user_id=message.from_user.id))
            if is_subscribe.status is not ChatMemberStatus.CREATOR and is_subscribe.status is not ChatMemberStatus.MEMBER:
                print("sss")
                message_for_delete = await message.answer(
                    f"""<a href="tg://user?id={message.from_user.id}">{message.from_user.full_name}</a>, щоб ваші повідомлення не видалялись будь-ласка підпишіться на чат: <a href="{subscribe_link}">Тисни сюди щоб вступити в чат</a> .\n\n<b>Наша спільнота {message.chat.title} поступово розвивається, кількість повідомлень зростає, щоб відсіяти спам та ботів ми підключили функцію захисту - Вам достатньо вступити в чат вказаний в повідомленні,щоб ваші повідомлення перестали видалятися.</b>""",
                    parse_mode=ParseMode.HTML)
                waiting_time = random.randint(3, 10)
                await asyncio.sleep(waiting_time)
                await message.delete()
                await asyncio.sleep(waiting_time)
                await message_for_delete.delete()
    except Exception as e:
        print(e)


async def publish_buttons_post(message, db_chat, chat_id):
    # публікація посту з кнопками
    # отримання інформації про чат в базі, перевірка чи він є в базі
    # якщо є в базі то main_post буде збережено відповідний пост
    # якщо нема чату, то буде збережено дефолт пост
    try:
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
        pass


async def publish_promotion_posts(message, db_chat):
    # для публікації реклами
    try:
        if db_chat is not None:
            now = datetime.now()
            promotion_posts = PromotionPost.objects.filter(
            chat_id=db_chat,
            end_date_promotion__gte=now
            )
            for post in promotion_posts:
                print(post)
                try:
                    await bot_helper_promoter.forward_message(message.chat.id,post.chat_message_id,post.message_id)
                except Exception as e:
                    print(e)
                    pass
                random_wait = random.randint(15,160)
                await asyncio.sleep(random_wait)
    except Exception as e:
        print(e)
        pass



@router.channel_post()
async def set_new_channel_message(message: types.Message) -> None:
    # парсим отсюда, сейвим айди поста и сохраняем в бд,
    # в бд мы вручную добавляем даты публикаций(дедлайн) и так же привязываем чат
    await PromotionPost(message_id=message.message_id, chat_message_id=message.chat.id).asave()


@router.message()
async def read_messages(message: types.Message) -> None:
    try:
        # підтримка відслідковування чату, де видаляється, аби змушувати підписувати саме на відповідний чат/канал
        chat_id = message.chat.id
        db_chat = Chat.objects.filter(chat_id=chat_id).first()
        if db_chat is not None:
            community = db_chat.get_community_for_subscribe()
            if community is not None:
                task = asyncio.create_task(
                    remove_message(message, community.subscribe_chat.chat_id, community.subscribe_link))

        if chat_id not in messages_counter:
            messages_counter[chat_id] = 0
        messages_counter[chat_id] += 1
        if messages_counter[chat_id] % 5 == 0:
            # Перевірка, чи кількість повідомлень кратна 5
            # Виклик функції для публікації реклами у вигляді кнопок
            buttonPromotionTask = asyncio.create_task(publish_buttons_post(message, db_chat, chat_id))

        if messages_counter[chat_id] % 7 == 0:
            promotionPostTask = asyncio.create_task(publish_promotion_posts(message, db_chat))

    except Exception as e:
        traceback.print_exc()
        # But not all the types is supported to be copied so need to handle it
        pass


async def runner() -> None:
    # Initialize Bot instance with a default parse mode which will be passed to all API calls
    bot = Bot(API_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp.include_router(router)
    # And the run events dispatching
    await dp.start_polling(bot)


def main():
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(runner())
