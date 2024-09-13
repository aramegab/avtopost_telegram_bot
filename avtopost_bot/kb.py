from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, KeyboardButton, ReplyKeyboardMarkup
from aiogram.utils.callback_data import CallbackData
from db import *
from dotenv import load_dotenv
import os

load_dotenv()
ADMIN_ID = int(os.getenv("ADMIN_ID"))

def menu(telegram_id) -> ReplyKeyboardMarkup:
    profile = KeyboardButton(text="💻Профиль")
    obyavlenia = KeyboardButton(text='📨Объявления')
    faq = KeyboardButton(text="❓FAQ")
    help = KeyboardButton(text="♨️Помощь")
    admin = KeyboardButton(text="🎛Админ Панель🎛")
    if telegram_id == ADMIN_ID:
        return ReplyKeyboardMarkup(resize_keyboard=True).add(profile).add(obyavlenia,faq).add(help).add(admin)
    else:
        return ReplyKeyboardMarkup(resize_keyboard=True).add(profile).add(obyavlenia,faq).add(help)

def adminmenu(telegram_id) -> ReplyKeyboardMarkup:
    rassilka = KeyboardButton(text="Рассылка")
    users = KeyboardButton(text='Количество юзеров')
    add_moder = KeyboardButton(text='Добавить модера')
    del_moder = KeyboardButton(text='Удалить модера')
    exit = KeyboardButton(text="Выйти из панели")
    if telegram_id == ADMIN_ID:
        return ReplyKeyboardMarkup(resize_keyboard=True).add(rassilka).add(add_moder,del_moder).add(users).add(exit)
    else:
        return menu(telegram_id)

def cancel() -> InlineKeyboardMarkup:
    otmena = InlineKeyboardButton("❌ Отмена", callback_data=f'cancel_func')
    return InlineKeyboardMarkup().add(otmena)

def ad_keyboard() -> ReplyKeyboardMarkup:
    add = KeyboardButton('✅Создать объявление')
    back = KeyboardButton('Назад')
    return ReplyKeyboardMarkup(resize_keyboard=True).add(add,back)

def confirmation_keyboard() -> ReplyKeyboardMarkup:
    add = KeyboardButton('Да')
    back = KeyboardButton('Отменить публикацию')
    return ReplyKeyboardMarkup(resize_keyboard=True).add(add).add(back)

def publish_keyboard() -> ReplyKeyboardMarkup:
    add = KeyboardButton('Публиковать')
    back = KeyboardButton('Отменить публикацию')
    return ReplyKeyboardMarkup(resize_keyboard=True).add(add).add(back)

def no_photo() -> ReplyKeyboardMarkup:
    add = KeyboardButton('Продолжить без фотографии')
    back = KeyboardButton('Отменить публикацию')
    return ReplyKeyboardMarkup(resize_keyboard=True).add(add).add(back)

def moderation_keyboard(ad_id) -> InlineKeyboardMarkup:
    accept = InlineKeyboardButton("✅ Одобрить", callback_data=f'approve_{ad_id}')
    decline = InlineKeyboardButton("❌ Отклонить", callback_data=f'reject_{ad_id}')
    return InlineKeyboardMarkup().add(accept).add(decline)