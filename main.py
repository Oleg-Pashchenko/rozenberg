import time
from datetime import datetime, timedelta
import json
import logging
from threading import Thread

import requests
from aiogram import Dispatcher, Bot
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext

from aiogram.types import (
    ReplyKeyboardMarkup,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
import os
from aiogram.utils import executor
from dotenv import load_dotenv

from structures import AddContent, EditText, EditLink, EditTime

load_dotenv()

API_TOKEN = os.getenv("API_TOKEN")
logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())

my_id = 1398715343
rozenberg_id = 996051043
admin_ids = [my_id, rozenberg_id, 791143287]


@dp.callback_query_handler(lambda m: "delete" in m.data)
async def delete(data):
    index = int(data.data.replace("delete_", ""))
    await bot.answer_callback_query(data.id)
    existing_content = json.load(open("content.json", "r"))
    existing_content.pop(index)
    with open("content.json", "w", encoding="UTF-8") as f:
        f.write(json.dumps(existing_content))
    f.close()
    await bot.send_message(data.message.chat.id, "Удалено!")
    await cmd_admin(data.message)


@dp.callback_query_handler(lambda callback_query: "edit_link" in callback_query.data, state="*")
async def edit_link(callback_query, state):
    index = int(callback_query.data.replace("edit_link_", ""))
    await bot.answer_callback_query(callback_query.id)
    async with state.proxy() as data:
        data["index"] = index
    await EditLink.text.set()
    await bot.send_message(callback_query.from_user.id, "Введите новый текст:")


@dp.message_handler(lambda m: True, state=EditLink.text)
async def edit_link_2(message, state: FSMContext):
    async with state.proxy() as data:
        index = data["index"]

    existing_content = json.load(open("content.json", "r"))
    existing_content[index]["link"] = message.text
    with open("content.json", "w", encoding="UTF-8") as f:
        f.write(json.dumps(existing_content))
    f.close()
    await bot.send_message(message.chat.id, f"Изменено!")
    await state.finish()
    await cmd_admin(message)


@dp.callback_query_handler(
    lambda callback_query: "edit_text" in callback_query.data, state="*"
)
async def edit_text(callback_query, state):
    index = int(callback_query.data.replace("edit_text_", ""))
    await bot.answer_callback_query(callback_query.id)
    async with state.proxy() as data:
        data["index"] = index
    await EditText.text.set()

    await bot.send_message(callback_query.from_user.id, "Введите новый текст:")


@dp.message_handler(lambda m: True, state=EditText.text)
async def edit_text_2(message, state: FSMContext):
    async with state.proxy() as data:
        index = data["index"]

    existing_content = json.load(open("content.json", "r"))
    existing_content[index]["message"] = message.text
    with open("content.json", "w", encoding="UTF-8") as f:
        f.write(json.dumps(existing_content))
    f.close()
    await bot.send_message(message.chat.id, f"Изменено!")
    await state.finish()
    await cmd_admin(message)


@dp.callback_query_handler(
    lambda callback_query: "edit_time" in callback_query.data, state="*"
)
async def edit_time(callback_query, state):
    index = int(callback_query.data.replace("edit_time_", ""))
    await bot.answer_callback_query(callback_query.id)
    async with state.proxy() as data:
        data["index"] = index
    await EditTime.text.set()
    await bot.send_message(
        callback_query.from_user.id, "Введите время (в формате 09:00):"
    )


@dp.message_handler(lambda m: True, state=EditTime.text)
async def edit_time_2(message, state: FSMContext):
    async with state.proxy() as data:
        index = data["index"]

    existing_content = json.load(open("content.json", "r"))
    existing_content[index]["time"] = message.text
    with open("content.json", "w", encoding="UTF-8") as f:
        f.write(json.dumps(existing_content))
    f.close()
    await bot.send_message(message.chat.id, f"Изменено!")
    await state.finish()
    await cmd_admin(message)


@dp.message_handler(lambda m: m.text == "Добавить новый контент", state="*")
async def add_new_content(message, state: FSMContext):
    await bot.send_message(message.chat.id, "Введите описание:")
    await AddContent.name.set()


@dp.message_handler(state=AddContent.name)
async def add_new_content_2(message, state: FSMContext):
    async with state.proxy() as data:
        data["name"] = message.text
    await AddContent.link.set()
    await bot.send_message(message.chat.id, "Введите ссылку на видео:")


@dp.message_handler(lambda m: True, state=AddContent.link)
async def add_new_content_3(message, state: FSMContext):
    async with state.proxy() as data:
        name = data["name"]
        link = message.text

    d = {"message": name, "link": link}
    existing_content = json.load(open("content.json", "r"))
    existing_content.append(d)
    with open("content.json", "w", encoding="UTF-8") as f:
        f.write(json.dumps(existing_content))
    f.close()
    await bot.send_message(message.chat.id, f"Добавлено!")
    await state.finish()
    await cmd_admin(message)


def register_if_user_is_new(chat_id):
    db = json.load(open("db.json", "r", encoding="UTF-8"))
    if chat_id in db.keys():
        return False

    current_time = datetime.now().time()
    hour = current_time.hour
    minute = current_time.minute
    day = datetime.now().date().day
    db[chat_id] = f"{day}:{hour}:{minute}:0"
    with open("db.json", "w", encoding="UTF-8") as f:
        f.write(json.dumps(db))
        f.close()


@dp.message_handler(commands="admin", state="*")
async def cmd_admin(message):
    text = "Текущий сохраненный контент:"
    existing_content = json.load(open("content.json", "r"))

    greet_kb = ReplyKeyboardMarkup(resize_keyboard=True)
    greet_kb.add("Добавить новый контент")

    if message.chat.id in admin_ids:
        await bot.send_message(
            chat_id=message.chat.id, text=text, reply_markup=greet_kb
        )
        for index, content in enumerate(existing_content):
            inline_kb_full = InlineKeyboardMarkup()
            inline_kb_full.add(
                InlineKeyboardButton(
                    "Изменить текст", callback_data=f"edit_text_{index}"
                ),
                InlineKeyboardButton(
                    "Изменить ссылку", callback_data=f"edit_link_{index}"
                ),
                InlineKeyboardButton(
                    "Изменить время", callback_data=f"edit_time_{index}"
                ),
                InlineKeyboardButton("Удалить", callback_data=f"delete_{index}"),
            )
            if "time" in content.keys():
                t = content["time"]
            else:
                t = "спустя день после предыдущего"

            await bot.send_message(
                chat_id=message.chat.id,
                text=f"{index + 1}. Время: {t}\n{content['message']}\n{content['link']}",
                reply_markup=inline_kb_full,
            )


def send_video(chat_id, text, video_link):
    url_req = (
            "https://api.telegram.org/bot"
            + API_TOKEN
            + "/sendMessage"
            + "?chat_id="
            + chat_id
            + "&text="
            + f"{text}\n{video_link}"
    )
    results = requests.get(url_req)


async def add_referal_link(arg):
    referals = json.load(open('referals.json', 'r', encoding='UTF-8'))
    if arg in referals.keys():
        referals[arg] += 1
    else:
        referals[arg] = 1
    with open('referals.json', 'w', encoding='UTF-8') as f:
        f.write(json.dumps(referals))
    f.close()

async def get_referal_stats():
    referals = json.load(open('referals.json', 'r', encoding='UTF-8'))
    ans = ''
    for key in referals.keys():
        ans += f'{key}: {referals[key]}\n'
    return ans
@dp.message_handler(commands='stats')
async def stats(message):
    stats = await get_referal_stats()
    await message.answer(f"Статистика по реферальным ссылкам:\n{stats}")


@dp.message_handler(commands="start")
async def cmd_start(message):
    referral_link = message.get_args()
    if referral_link:
        await add_referal_link(referral_link)
    await bot.send_message(
        message.chat.id,
        text="""Доброго дня!\n\nВы тут, а значит не исключено, что в  ближайшее время вы планируете ремонт или приобретение квартиры (дома). Отлично!
\n\nОшибки, о которых идет речь в наших видео, приносят немало проблем: от значительных финансовых потерь до разочарования в конечном результате. Нам хочется, чтобы вы наслаждались процессом обустройства квартиры и в конечном итоге могли с гордостью заявить, что живете в квартире мечты.
\n\nПривлекая дизайнера к выбору квартиры, вы привлекаете человека, у которого нет финансовой заинтересованности продать более дорогой и большой по площади вариант. Он не считает проценты с продажи от застройщика. Его цель — не продажа квартиры, а финальный вид квартиры.
\n\nЯ Михаил Новинский, архитектор-дизайнер, основатель и руководитель студии MNdesign, 20 лет занимаюсь дизайном интерьеров и архитектурным проектированием.
\n\nРаботы нашей студии становились лауреатами многих престижных премий:
\n— Interia Awards
\n— Best Interior Festival (Союза архитекторов России)
\n— Premium Living Awards
\n— Modern Home Award
\n— Best Office Awards и др.
\n\nМы принимали участие в «Квартирном вопросе» и «Дачном ответе» на НТВ, выполняли работы для таких компаний, как Match Hospitality AG, Paulig AG, Mercedes-Benz Rus, Castorama, OBI, гостиничный комплекс «Я-Отель» и др.
\n\nИтак, каждый день в течение недели вы будете получать наши видеоуроки. Всего 6 уроков продолжительностью не более 5 минут каждый. Поверьте, эти 5 минут в день могут перевернуть ваше представление о дизайне и/или спасти от роковой ошибки.
\n\nНажимайте на кнопку ниже, чтобы получить первый урок.\n\nС уважением, Михаил Новинский и студия MNdesign.
""",
    )
    await cmd_go(message)



async def cmd_go(message):
    status = register_if_user_is_new(message.chat.id)
    if status is False:
        await bot.send_message(message.chat.id, text="Вы уже подписаны на уведомления!")


def update():
    while True:
        try:
            time.sleep(1)
            db = json.load(open("db.json", "r", encoding="UTF-8"))
            current_day = datetime.now().date().day
            current_time = datetime.now().time()
            current_hour = current_time.hour
            current_minute = current_time.minute
            for index in db.keys():
                day, hour, minute, v = map(int, db[index].split(":"))
                if (
                        current_day == day
                        and current_hour >= hour
                        and current_minute >= minute
                ):
                    dt = datetime.now().date()
                    next_day = dt + timedelta(days=1)
                    content = json.load(open("content.json", "r", encoding="UTF-8"))
                    if len(content) == v:
                        db[index] = f"{next_day.day}:{hour}:{minute}:{v}"
                    else:
                        send_video(index, content[v]["message"], content[v]["link"])
                        print(content)
                        if 'time' in content[v + 1].keys():
                            hour, minute = map(int, content[v + 1].split(':'))
                        db[index] = f"{next_day.day}:{hour}:{minute}:{v + 1}"
            with open("db.json", "w", encoding="UTF-8") as f:
                f.write(json.dumps(db))
                f.close()
        except:
            pass


th2 = Thread(target=update).start()
th1 = Thread(target=executor.start_polling(dp, skip_updates=True)).start()
