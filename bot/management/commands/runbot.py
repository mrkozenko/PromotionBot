import asyncio
import random
import re
import traceback
from datetime import datetime
from pprint import pprint
from typing import Any

from django.utils import timezone
from aiogram.client.default import DefaultBotProperties
from aiogram.methods import GetChatMember
from aiogram.utils.serialization import deserialize_telegram_object
from asgiref.sync import sync_to_async
from django.core.management.base import BaseCommand
from aiogram import Bot, Dispatcher, filters, F
from aiogram.client.session.middlewares.request_logging import logger
from django.db.models import Q
import asyncio
import logging
import sys
from os import getenv

from aiogram import Bot, Dispatcher, Router, types
from aiogram.enums import ParseMode, ChatMemberStatus, ChatType
from aiogram.filters import CommandStart, ChatMemberUpdatedFilter, IS_NOT_MEMBER, MEMBER, JOIN_TRANSITION
from aiogram.types import Message, ChatInviteLink, ChatMemberUpdated
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.utils.markdown import hbold

from PromotionMaker.models import Post, Button, Chat, PromotionPost, SpamFilterModel
from ChatModerator.settings import API_TOKEN, PROMOTER_TOKEN
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
last_promotion_post = {

}
messages_counter = {

}
last_messages = {

}

router = Router()


async def remove_message(message, chat_for_subscribe, subscribe_link):
    try:

        if not message.from_user.is_bot and chat_for_subscribe is not None:
            is_subscribe = await message.bot(GetChatMember(chat_id=chat_for_subscribe, user_id=message.from_user.id))
            print(chat_for_subscribe)
            print(is_subscribe)
            if is_subscribe.status!="creator" and is_subscribe.status!="member" and is_subscribe.status!="restricted":
                print("sss")
                keyboard = InlineKeyboardBuilder()
                keyboard.row(types.InlineKeyboardButton(text=f"Спільнота для підписки", url=subscribe_link))
                message_for_delete = await message.answer(
                    f"""{message.from_user.full_name}, щоб ваші повідомлення не видалялися, просто приєднайтесь до вказаного в повідомленні чату!  
<a href="{subscribe_link}">✅ Тисни сюди щоб вступити в чат</a>  

🔹 Наша спільнота {message.chat.title} постійно зростає, і щоб уникнути спаму та ботів, ми ввели простий захист.  

<b>Все, що потрібно – це приєднатися до чату, і ваші повідомлення більше не будуть видалятися. Долучайся та будь у курсі всіх новин!</b>""",
                    parse_mode=ParseMode.HTML, reply_markup=keyboard.as_markup())

                waiting_time = random.randint(15, 35)
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
        #спроба зупинити видалення реклами (тестовий режим поки що)
        # try:
        #     for i in last_promotion_post.get(message.chat.id, []):
        #         try:
        #             print(i)
        #             await bot_helper_promoter.delete_message(chat_id=message.chat.id, message_id=i)
        #         except Exception as e:
        #             print(e)
        # except Exception as e:
        #     print(e)
        #     pass
        if db_chat is not None:
            now = datetime.now()
            promotion_posts = PromotionPost.objects.filter(
                chat_id=db_chat,
                end_date_promotion__gte=now
            )
            for post in promotion_posts:
                try:
                    mess = await bot_helper_promoter.forward_message(message.chat.id, post.chat_message_id,
                                                                     post.message_id)
                    last_promotion_post[message.chat.id] = last_promotion_post.get(message.chat.id, [])
                    last_promotion_post[message.chat.id].append(mess.message_id)
                except Exception as e:
                    print(e)
                    pass
                random_wait = random.randint(35, 260)
                await asyncio.sleep(random_wait)
    except Exception as e:
        print(e)
        pass


async def spam_filter_search(message):
    #пошук та порівняння повідомлень на наявність заборонених слів
    try:

        words = message.text.lower().split()

        query = Q()

        # Добавляем условия для каждого слова с использованием регулярных выражений
        for word in words:
            # Создаем регулярное выражение для точного совпадения слова целиком
            regex = fr"\b{re.escape(word)}\b"
            query |= Q(black_words__iregex=regex)

        # Выполняем запрос и проверяем наличие записей
        exists_bad_word = SpamFilterModel.objects.filter(query).exists()
        if exists_bad_word:
            print("Spam filter")
            exists_exception_user = SpamFilterModel.objects.filter(
                except_ids__contains=str(message.from_user.id)
            ).exists()
            if not exists_exception_user:
                mess_warning = await bot_helper_promoter.send_message(chat_id=message.chat.id,
                                                                      text="Воу, схоже, що ваше оголошення підпадає під категорію платних та буде видалено:\nНа платній основі публікуються:\n- Реклама магазинів, ресторанів та послуг.\n- Продажі.\n- Верифікації.\n- Брачка, вебкам,офіси.\n- Оренда акаунтів.\nРекомендуємо звернутися до адміністратора стосовно купівлі реклами.",
                                                                      reply_to_message_id=message.message_id)
                await asyncio.sleep(15)
                try:
                    await message.delete()
                except Exception as e:
                    pass
                await asyncio.sleep(3)
                try:
                    await bot_helper_promoter.delete_message(mess_warning.chat.id, mess_warning.message_id)
                except Exception as e:
                    print(e)
    except Exception as e:
        print(e)

async def rm_invite_message(event):
    #видалення та відправка повідомлення про потребу запросити користувача до чату
    try:
        message_for_delete = await event.answer(
            f"""🎉 <a href="tg://user?id={event.from_user.id}">{event.from_user.full_name}</a>, вітаємо у {event.chat.full_name}!

🔐 <b>Щоб розблокувати доступ до чату, вам потрібно пройти невеличку перевірку:</b>

<b>👥 Запросіть одного користувача до нашої спільноти</b>
⚡️ Це може бути ваш друг, колега або знайомий
✨ Після цього ви отримаєте повний доступ до чату

🛡️ Це наш спосіб захисту від:
- 🤖 Ботів
- 🚫 Спамерів
- 🎭 Фейкових акаунтів

🔐 <b>Щоб отримати доступ до чату:</b>
1️⃣ Натисніть на три крапки ⋮ у верхньому правому куті
2️⃣ Оберіть "Додати учасників"
3️⃣ Запросіть одного друга або знайомого

💫 <i>Разом ми створюємо безпечний простір для спілкування!</i>

🤝 Дякуємо за ваше розуміння та участь у розвитку спільноти""",
            parse_mode=ParseMode.HTML)
        waiting_time = random.randint(58, 120)
        await asyncio.sleep(waiting_time)
        await message_for_delete.delete()
    except Exception as e:
        print(e)
@router.chat_member(
    ChatMemberUpdatedFilter(JOIN_TRANSITION),
)
async def welcome(event: ChatMemberUpdated) -> Any:
    #хендлер на вступ нових користувачів
    try:
        if event.from_user.id != event.new_chat_member.user.id:
            restricted_permissions = types.ChatPermissions(can_send_messages=True, can_invite_users=True,can_send_photos=True, can_send_documents=True)
            await event.bot.restrict_chat_member(chat_id=event.chat.id, user_id=event.from_user.id,
                                                 permissions=restricted_permissions)
            await event.bot.send_message(chat_id=-1002155533730,text=f"юзер запросив іншого юзера {event.from_user.full_name} -> {event.new_chat_member.user.full_name} до чату {event.chat.full_name}")

        else:
            restricted_permissions = types.ChatPermissions(can_send_messages=False,can_invite_users=True)
            await event.bot.restrict_chat_member(chat_id=event.chat.id,user_id=event.from_user.id, permissions = restricted_permissions)
            print(f"юзер просто вступив - {event.from_user.full_name}")
            await event.bot.send_message(chat_id=-1002155533730,text=f"юзер просто вступив - {event.from_user.full_name} чат {event.chat.full_name}")
            asyncio.create_task(rm_invite_message(event))
    except Exception as e:
        pass

@router.channel_post()
async def set_new_channel_message(message: types.Message) -> None:
    # парсим отсюда, сейвим айди поста и сохраняем в бд,
    # в бд мы вручную добавляем даты публикаций(дедлайн) и так же привязываем чат
    await PromotionPost(message_id=message.message_id, chat_message_id=message.chat.id).asave()


@router.message()
async def read_messages(message: types.Message) -> None:
    try:

        spamfilterCall = asyncio.create_task(spam_filter_search(message))
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
        if messages_counter[chat_id] % 6 == 0:
            # Перевірка, чи кількість повідомлень кратна 5
            # Виклик функції для публікації реклами у вигляді кнопок
            buttonPromotionTask = asyncio.create_task(publish_buttons_post(message, db_chat, chat_id))

        if messages_counter[chat_id] % 16 == 0:
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
    await dp.start_polling(bot,allowed_updates=[   "chat_member",  # оновлення про учасників чату
    "message",      # звичайні повідомлення
    "edited_message",  # редаговані повідомлення
    "channel_post",    # пости в каналах
    "callback_query",  # натискання на інлайн кнопки
    "inline_query"    # інлайн запити
    ])


def main():
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(runner())
