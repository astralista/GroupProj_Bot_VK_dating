import random
import asyncio
from vk_api.longpoll import VkLongPoll, VkEventType
from bot.keyboard import *
from db.db_functions import *
from vk.user_information import take_user_info


def kirillic_symbols(text):
    letters_permitted = (
        "АБВГДЕЁЖЗИКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯабвгдеёжзийклмнопрстуфхцчшщъыьэюя -"
    )
    kirillic = list(letters_permitted)
    example = list(text)
    for letter in example:
        if letter not in kirillic:
            return False
    return True


def write_msg(session, user_id, message, keyboard=None):
    params = {
        "user_id": user_id,
        "message": message,
        "random_id": random.randrange(10 ** 7),
    }
    if keyboard is not None:
        params["keyboard"] = keyboard.get_keyboard()
    else:
        params = params

    session.method("messages.send", params)


def wrong_input(session, user_id):
    write_msg(session, user_id, "Пожалуйста, выбери значение с кнопки, дорогуша.")


def greetings(session, user_id):
    for event in VkLongPoll(session).listen():
        if event.type == VkEventType.MESSAGE_NEW and event.to_me:
            who = take_user_info(user_id)
            write_msg(
                session,
                user_id,
                f"Привет, {who['first_name']}! Добро пожаловать в наш бот для знакомств.\n"
                f"Исходя из данных о тебе: город: {who['city_title']}, возраст: {who['age']} лет\n"
                f"Подберём тебе пару.\n\n"
                f"Жми кнопку Вперёд и начнём",
                keyboard_hello_generate(),
            )
            return


def start_bot(session, user_id):
    create_db()
    create_table()
    for event in VkLongPoll(session).listen():
        if event.type == VkEventType.MESSAGE_NEW and event.to_me:
            if event.text == "Вперёд!":
                return
            else:
                wrong_input(session, user_id)


def gender_choice(session, user_id):
    write_msg(
        session,
        user_id,
        "Приступим! Кого ты желаешь найти?",
        keyboard_gender_generate(),
    )
    for event in VkLongPoll(session).listen():
        if event.type == VkEventType.MESSAGE_NEW and event.to_me:
            text = event.text
            if text == "Парня":
                gender = 2
                return gender
            elif text == "Девушку":
                gender = 1
                return gender
            elif text == "Пол не важен":
                gender = 0
                return gender
            else:
                wrong_input(session, user_id)


def age_check_low(session, user_id):
    write_msg(
        session,
        user_id,
        "Теперь поговорим про возраст партнёра. "
        "Какая нижняя граница желаемого возраста?",
        keyboard_stupid_generate(),
    )
    for event in VkLongPoll(session).listen():
        if event.type == VkEventType.MESSAGE_NEW and event.to_me:
            text = event.text
            if text is not None:
                if text.isnumeric():
                    text = int(text)
                    if text >= 12:
                        age_low = text
                        return age_low
                    else:
                        write_msg(
                            session,
                            user_id,
                            "Извини, наш бот не может искать партнёров младше 12 лет.",
                        )
                else:
                    write_msg(session, user_id, "Пожалуйста, введи ответ цифрой.")
            else:
                write_msg(session, user_id, "Пожалуйста, введи ответ.")


def age_check_high(session, user_id, age_low):
    write_msg(
        session, user_id, "Что насчёт верхней планки?", keyboard_stupid_generate()
    )
    for event in VkLongPoll(session).listen():
        if event.type == VkEventType.MESSAGE_NEW and event.to_me:
            text = event.text
            if text is not None:
                if text.isnumeric():
                    text = int(text)
                    if text < age_low:
                        write_msg(
                            session,
                            user_id,
                            "Бот умеет считать, дорогуша) "
                            "Этот показатель должен быть БОЛЬШЕ, чем предыдущий.",
                        )
                    else:
                        age_high = text
                        return age_high
                else:
                    write_msg(session, user_id, "Пожалуйста, введи ответ цифрой.")
            else:
                write_msg(session, user_id, "Пожалуйста, введи ответ.")


#не использую
def country_input(session, user_id):
    write_msg(
        session,
        user_id,
        "Отлично! В какой стране ищете вашего человека?",
        keyboard_country_generate(),
    )
    for event in VkLongPoll(session).listen():
        if event.type == VkEventType.MESSAGE_NEW and event.to_me:
            text = event.text
            if text is not None:
                if kirillic_symbols(text):
                    if text == "Страна не имеет значения":
                        country = None
                        return country
                    else:
                        country = text
                        return country
                else:
                    write_msg(session, user_id, "Пожалуйста, введите ответ кириллицей.")
            else:
                write_msg(session, user_id, "Пожалуйста, введите ответ.")


#не использую
def city_input(session, user_id):
    write_msg(
        session, user_id, "Теперь укажите желаемый город", keyboard_city_generate()
    )
    for event in VkLongPoll(session).listen():
        if event.type == VkEventType.MESSAGE_NEW and event.to_me:
            text = event.text
            if text is not None:
                if kirillic_symbols(text):
                    if text == "Город не имеет значения":
                        city = 0
                        return city
                    else:
                        city = text
                        return city
                else:
                    write_msg(session, user_id, "Пожалуйста, введи ответ кириллицей.")
            else:
                write_msg(session, user_id, "Пожалуйста, введи ответ.")



"""ЗДЕСЬ АКТИВИРУЕТСЯ ПОИСК (см. VK.search_candidates)"""


def random_person(candidate_list):
    candidate = random.choice(candidate_list)
    return candidate


"""ВЫВОДИТСЯ РАНДОМНЫЙ ЧЕЛОВЕК ИЗ ВЫБОРКИ"""


def generate_candidate_message(cur):
    cur.execute(
        "SELECT first_name, last_name, photo, vk_link FROM people_found ORDER BY random() LIMIT 1"
    )
    candidate_data = cur.fetchone()
    fname = candidate_data[0]
    lname = candidate_data[1]
    photo_link = f"*{candidate_data[2]}*"
    link = candidate_data[3]
    return f"{fname} {lname}\n{photo_link}\n\n{link}"


async def discuss_candidates(session, user_id):
    await asyncio.sleep(1)
    conn = psycopg2.connect(
        host="localhost", user="postgres", password="postgres", database="vkinder"
    )
    cur = conn.cursor()
    message = generate_candidate_message(cur)
    write_msg(
        session,
        user_id,
        f"Начнём! Что думаешь об этом человеке?\n{message}",
        keyboard_discussion_generate(),
    )
    for event in VkLongPoll(session).listen():
        if event.type == VkEventType.MESSAGE_NEW and event.to_me:
            text = event.text
            if text == "Да! Добавь в Избранное":
                bot_satisfied_reply()
                save_to_favorites(cur, conn, message)
                bot_next_reply()
                cur.execute(
                    "DELETE FROM people_found WHERE vk_link = %s", (message,)
                )
                conn.commit()
                message = generate_candidate_message(cur)
                write_msg(
                    session,
                    user_id,
                    f"Что думаешь об этом человеке?\n{message}",
                    keyboard_discussion_generate(),
                )
            elif text == "Давай посмотрим ещё":
                bot_neutral_reply()
                bot_next_reply()
                cur.execute(
                    "DELETE FROM people_found WHERE vk_link = %s", (message,)
                )
                conn.commit()
                message = generate_candidate_message(cur)
                write_msg(
                    session,
                    user_id,
                    f"Что думаешь об этом человеке?\n{message}",
                    keyboard_discussion_generate(),
                )
            elif text == "Нет. Больше не показывай":
                bot_upset_reply()
                save_to_black_list(cur, conn, message)
                bot_next_reply()
                cur.execute(
                    "DELETE FROM people_found WHERE vk_link = %s", (message,)
                )
                conn.commit()
                message = generate_candidate_message(cur)
                write_msg(
                    session,
                    user_id,
                    f"Что думаешь об этом человеке?\n{message}",
                    keyboard_discussion_generate(),
                )
            elif text == "Стоп":
                return
            else:
                wrong_input(session, user_id)


def final_menu(session, user_id):
    write_msg(
        session,
        user_id,
        "Что хочешь делать сейчас, дорогуша?",
        keyboard_final_generate(),
    )
    for event in VkLongPoll(session).listen():
        if event.type == VkEventType.MESSAGE_NEW and event.to_me:
            text = event.text
            if text == "Поищем ещё!":
                write_msg(session, user_id, "Вот это настрой! Я в тебе не сомневалась)")
                decision = 1
                return decision
            elif text == "Покажи моих Избранных":
                write_msg(session, user_id, "ЗДЕСЬ МОГЛИ БЫТЬ ВАШИ ИЗБРАННЫЕ)))")

                '''Далее будет команда для вывода избранных'''

            elif text == "Заканчивай":
                write_msg(
                    session,
                    user_id,
                    "Я поняла тебя! Дай знать, если захочешь вернуться;)",
                    keyboard_hello_generate(),
                )
                decision = 0
                return decision
            else:
                wrong_input(session, user_id)
