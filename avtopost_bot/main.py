import logging
import os
import asyncio
from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import BoundFilter
from aiogram.dispatcher.handler import CancelHandler, current_handler
from aiogram.dispatcher.middlewares import BaseMiddleware
from aiogram.utils.exceptions import Throttled, BotBlocked
from aiogram.types import (
    InlineKeyboardMarkup, InlineKeyboardButton, 
    KeyboardButton, ReplyKeyboardMarkup, CallbackQuery,
    ChatType, InputFile, ReplyKeyboardRemove
)
from dotenv import load_dotenv
from db import *
import kb
from states import *
from datetime import datetime

messages_to_delete = {}

load_dotenv()

API_BOT_TOKEN = os.getenv("API_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))
CHANNEL_ID = os.getenv("CHANNEL_ID")

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_BOT_TOKEN, parse_mode='HTML')
dp = Dispatcher(bot, storage=MemoryStorage())

usersdb = UsersDB()
addb = AdDB()

class ThrottlingMiddleware(BaseMiddleware):
    def __init__(self, limit=0.5, key_prefix="antiflood_"):
        self.rate_limit = limit
        self.prefix = key_prefix
        super(ThrottlingMiddleware, self).__init__()

    async def on_process_message(self, message: types.Message, data: dict):
        handler = current_handler.get()
        dispatcher = Dispatcher.get_current()
        if handler:
            limit = getattr(handler, "throttling_rate_limit", self.rate_limit)
            key = getattr(handler, "throttling_key", f"{self.prefix}_{handler.__name__}")
        else:
            limit = self.rate_limit
            key = f"{self.prefix}_message"
        try:
            await dispatcher.throttle(key, rate=limit)
        except Throttled as t:
            await self.message_throttled(message, t)
            raise CancelHandler()

    async def message_throttled(self, message: types.Message, throttled: Throttled):
        handler = current_handler.get()
        dispatcher = Dispatcher.get_current()
        if handler:
            key = getattr(handler, "throttling_key", f"{self.prefix}_{handler.__name__}")
        else:
            key = f"{self.prefix}_message"
        delta = throttled.rate - throttled.delta
        if throttled.exceeded_count <= 2:
            await message.reply("<b>❗ Не спамь</b>")
        await asyncio.sleep(delta)
        thr = await dispatcher.check_key(key)

def rate_limit(limit: int, key=None):
    def decorator(func):
        setattr(func, "throttling_rate_limit", limit)
        if key:
            setattr(func, "throttling_key", key)
        return func
    return decorator

@dp.message_handler(commands="start", state="*")
@rate_limit(2, 'start')
async def start(message: types.Message):
    check_user = usersdb.check_client_in_db(message.from_user.id)
    if check_user:
        get_user = usersdb.get_user(message.from_user.id)
        user_id = message.from_user.id
        user_photos = await bot.get_user_profile_photos(user_id)

        get_user = usersdb.get_user(user_id)
        msg = f'''➖➖➖➖➖➖➖➖➖➖➖➖➖➖➖
👤 Логин: @{message.from_user.username}
🕜 Регистрация: {get_user[4]}
🔑 ID: <code>{message.from_user.id}</code>
➖➖➖➖➖➖➖➖➖➖➖➖➖➖➖
📨 Всего объявлений: {usersdb.get_all_ads(message.from_user.id)}
📝 Объявлений на проверке: {usersdb.get_ads_pending(message.from_user.id)}
➖➖➖➖➖➖➖➖➖➖➖➖➖➖➖'''

        if user_photos.total_count > 0:
            photo = user_photos.photos[0][-1]
            await message.answer_photo(photo=photo.file_id, caption=msg, reply_markup=kb.menu(message.from_user.id))
        else:
            await message.reply(msg, reply_markup=kb.menu(message.from_user.id))
    else:
        user_photos = await bot.get_user_profile_photos(message.from_user.id)
        if user_photos.total_count > 0:
            photo = user_photos.photos[0][-1]
            file_info = await bot.get_file(photo.file_id)
            file_path = file_info.file_path
            photo_file = await bot.download_file(file_path)
            save_path = os.path.join("avatars", f"{message.from_user.id}.jpg")
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            with open(save_path, 'wb') as f:
                f.write(photo_file.getvalue())
            now = datetime.now()
            timestamp = now.strftime("%Y-%m-%d")
            usersdb.add_user(
                telegram_id=message.from_user.id,
                username='@'+message.from_user.username,
                avatar=f'avatars/{message.from_user.id}.jpg',
                resgistration_time=timestamp
            )
            get_user = usersdb.get_user(message.from_user.id)
            msg = f'''➖➖➖➖➖➖➖➖➖➖➖➖➖➖➖
👤 Логин: @{message.from_user.username}
🕜 Регистрация: {get_user[4]}
🔑 ID: <code>{message.from_user.id}</code>
➖➖➖➖➖➖➖➖➖➖➖➖➖➖➖
📨 Всего объявлений: {usersdb.get_all_ads(message.from_user.id)}
📝 Объявлений на проверке: {usersdb.get_ads_pending(message.from_user.id)}
➖➖➖➖➖➖➖➖➖➖➖➖➖➖➖'''
            await message.answer_photo(photo=photo.file_id, caption=msg, reply_markup=kb.menu(message.from_user.id),parse_mode='html')
        else:
            now = datetime.now()
            timestamp = now.strftime("%Y-%m-%d")
            usersdb.add_user(
                telegram_id=message.from_user.id,
                username='@'+message.from_user.username,
                avatar=f'No photo',
                resgistration_time=timestamp
            )
            get_user = usersdb.get_user(message.from_user.id)
            msg = f'''➖➖➖➖➖➖➖➖➖➖➖➖➖➖➖
👤 Логин: @{message.from_user.username}
🕜 Регистрация: {get_user[4]}
🔑 ID: <code>{message.from_user.id}</code>
➖➖➖➖➖➖➖➖➖➖➖➖➖➖➖
📨 Всего объявлений: {usersdb.get_all_ads(message.from_user.id)}
📝 Объявлений на проверке: {usersdb.get_ads_pending(message.from_user.id)}
➖➖➖➖➖➖➖➖➖➖➖➖➖➖➖'''
            await message.reply(text=msg, reply_markup=kb.menu(message.from_user.id))

@dp.message_handler(content_types=['text'], text=['💻Профиль'])
async def send_profile(message: types.Message):
    user_id = message.from_user.id
    user_photos = await bot.get_user_profile_photos(user_id)

    get_user = usersdb.get_user(user_id)
    msg = f'''➖➖➖➖➖➖➖➖➖➖➖➖➖➖➖
👤 Логин: @{message.from_user.username}
🕜 Регистрация: {get_user[4]}
🔑 ID: <code>{message.from_user.id}</code>
➖➖➖➖➖➖➖➖➖➖➖➖➖➖➖
📨 Всего объявлений: {usersdb.get_all_ads(message.from_user.id)}
📝 Объявлений на проверке: {usersdb.get_ads_pending(message.from_user.id)}
➖➖➖➖➖➖➖➖➖➖➖➖➖➖➖'''

    if user_photos.total_count > 0:
        photo = user_photos.photos[0][-1]
        await message.answer_photo(photo=photo.file_id, caption=msg, reply_markup=kb.menu(message.from_user.id))
    else:
        await message.reply(msg, reply_markup=kb.menu(message.from_user.id))

@dp.message_handler(content_types=['text'], text=['❓FAQ'])
async def faq(message: types.Message):
    msg = '''Запрещено: 
...'''
    await message.answer_document(InputFile('docs/Правила.pdf'),caption=msg)

@dp.message_handler(content_types=['text'], text=['♨️Помощь'])
async def help(message: types.Message):
    await message.answer('📲Связь с администрацией: ')

@dp.message_handler(content_types=['text'], text=['📨Объявления'])
async def send_profile(message: types.Message):
    await message.answer("Выберите дейстиве:",reply_markup=kb.ad_keyboard())

@dp.message_handler(content_types=['text'], text=['🎛Админ Панель🎛'])
async def help(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        await message.answer('🎛Вы перешли в админ панель:',reply_markup=kb.adminmenu(message.from_user.id))
    else:
        pass

@dp.callback_query_handler(text_startswith=('cancel_func'), state='*')
async def cancel(call: types.CallbackQuery, state: FSMContext):
    await state.finish()
    await call.message.delete()
    await call.message.answer('✅ Действие отменена')

@dp.message_handler(content_types=['text'], text=['Количество юзеров'])
async def help(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        count = usersdb.get_all_users_count()
        await message.answer(f'🚀Количество юзеров в боте: {count}')
    else:
        pass

@dp.message_handler(content_types=['text'], text=['Рассылка'])
async def help(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        await message.answer('💬Введите текст для рассылки:',reply_markup=kb.cancel())
        await Rassilka.text.set()
    else:
        pass

@dp.message_handler(content_types=['text'], text=['Добавить модера'])
async def help(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        await message.answer('💬Введите Телеграмм айди пользователя: ',reply_markup=kb.cancel())
        await Addmoder.idmoder.set()
    else:
        pass

@dp.message_handler(state=Addmoder.idmoder)
async def cancel_publication(message: types.Message, state: FSMContext):
    await state.update_data(text=message.text)
    await state.finish()
    user = usersdb.add_moder(message.text)
    try:
        usersdb.add_moder(message.text)
        await bot.send_message(chat_id=message.text,text='✨ Вас назначили модератором!')
        await message.answer('✅ Модератор добавлен')
    except:
        await message.answer('❌ Ошибка: Пользователь не найден')

@dp.message_handler(content_types=['text'], text=['Удалить модера'])
async def help(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        await message.answer('💬Введите Телеграмм айди модера: ',reply_markup=kb.cancel())
        await Delmoder.idmoder.set()
    else:
        pass

@dp.message_handler(state=Delmoder.idmoder)
async def cancel_publication(message: types.Message, state: FSMContext):
    await state.update_data(text=message.text)
    await state.finish()
    try:
        user = usersdb.delete_moder(message.text)
        await bot.send_message(chat_id=message.text,text='❌ Вас сняли с поста модератора!')
        await message.answer('✅ Модератор снят')
    except:
        await message.answer('❌ Ошибка: Модератор не найден')

@dp.message_handler(content_types=['text'], text=['Выйти из панели'])
async def help(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        await message.answer('Главное меню',reply_markup=kb.menu(message.from_user.id))
    else:
        pass

@dp.message_handler(state=Rassilka.text)
async def cancel_publication(message: types.Message, state: FSMContext):
    await state.update_data(text=message.text)
    await state.finish()
    users = usersdb.get_all_users()
    for user in users:
        try:
            await bot.send_message(user[0],message.text)
        except:
            await asyncio.sleep(1)
    await message.answer('✅Рассылка успешно завершена')


@dp.message_handler(content_types=['text'], text=['Назад'])
async def send_profile(message: types.Message):
    await message.answer("Главное меню",reply_markup=kb.menu(message.from_user.id))

@dp.message_handler(text='Отменить публикацию', state=[CreateAd.waiting_for_text, CreateAd.waiting_for_confirmation, CreateAd.waiting_for_photo, CreateAd.waiting_for_publish])
async def cancel_publication(message: types.Message, state: FSMContext):
    await state.finish()
    await message.answer("Публикация отменена.", reply_markup=kb.ad_keyboard())

@dp.message_handler(text='✅Создать объявление')
async def start_ad_creation(message: types.Message):
    await message.answer("✉️Напишите объявление:\n",
                         reply_markup=ReplyKeyboardRemove())
    await CreateAd.waiting_for_text.set()

@dp.message_handler(state=CreateAd.waiting_for_text, content_types=types.ContentTypes.TEXT)
async def ad_text_received(message: types.Message, state: FSMContext):
    await state.update_data(ad_text=message.text)
    await message.answer(f"💬Ваш текст для объявления:\n{message.text}\n\n❗️Для перехода к следующему шагу, нажмите - Да",
                         reply_markup=kb.confirmation_keyboard())
    await CreateAd.waiting_for_confirmation.set()

@dp.message_handler(text='Да', state=CreateAd.waiting_for_confirmation)
async def confirm_ad_text(message: types.Message, state: FSMContext):
    await message.answer("🖼️Пожалуйста, приложите ОДНУ фотографию для объявления:",reply_markup=kb.no_photo())
    await CreateAd.waiting_for_photo.set()

@dp.message_handler(content_types=['photo','text'],text='Продолжить без фотографии', state=CreateAd.waiting_for_photo)
async def photo_received(message: types.Message, state: FSMContext):
    if message.text == 'Продолжить без фотографии':
        photo_id = 'None'
        data = await state.get_data()
        ad_text = data['ad_text']
        await message.answer(ad_text)
        await message.answer("🛑Ваше объявление готово к публикации!\nДля публикации выберите кнопку ниже:",
                         reply_markup=kb.publish_keyboard())
        await state.update_data(photo_id=photo_id)
        await CreateAd.waiting_for_publish.set()
    else:
        photo_id = message.photo[-1].file_id
        data = await state.get_data()
        ad_text = data['ad_text']

        await message.answer_photo(photo=photo_id, caption=ad_text)
        await message.answer("🛑Ваше объявление готово к публикации!\nДля публикации выберите кнопку ниже:",
                            reply_markup=kb.publish_keyboard())
        await state.update_data(photo_id=photo_id)
        await CreateAd.waiting_for_publish.set()

@dp.message_handler(text='Публиковать', state=CreateAd.waiting_for_publish)
async def send_for_moderation(message: types.Message, state: FSMContext):
    data = await state.get_data()
    ad_text = data['ad_text']
    photo_id = data['photo_id']
    user_id = message.from_user.id

    if photo_id == 'None':
        addb.add_ad(user_id, ad_text, photo_id, 'Ожидание')
        ad_id = addb.get_ad_by_tg_id(user_id)[0]
        await message.answer("❄️Ваше объявление отправлено на модерацию!\nОжидайте принятия модерации", reply_markup=kb.menu(message.from_user.id))
        moderators = usersdb.get_moderators()
        for moderator in moderators:
            await bot.send_message(moderator[1], text=ad_text, reply_markup=kb.moderation_keyboard(ad_id))
        await bot.send_message(ADMIN_ID, text=ad_text, reply_markup=kb.moderation_keyboard(ad_id))

        await state.finish()
    
    else:
        addb.add_ad(user_id, ad_text, photo_id, 'Ожидание')
        ad_id = addb.get_ad_by_photo_id(photo_id)[0]
        await message.answer("❄️Ваше объявление отправлено на модерацию!\nОжидайте принятия модерации", reply_markup=kb.menu(message.from_user.id))
        moderators = usersdb.get_moderators()
        for moderator in moderators:
            await bot.send_photo(moderator[1], photo=photo_id, caption=ad_text, reply_markup=kb.moderation_keyboard(ad_id))
        await bot.send_photo(ADMIN_ID, photo=photo_id, caption=ad_text, reply_markup=kb.moderation_keyboard(ad_id))
        await state.finish()

@dp.callback_query_handler(text_startswith="approve_", state="*")
async def approve_ad(callback_query: types.CallbackQuery):
    ad_id = int(callback_query.data.split('_')[1])
    ad = addb.get_ad(ad_id)
    if ad[3] == 'None':
        if ad[4] == 'Ожидание':
            ad_id = int(callback_query.data.split('_')[1])
            addb.update_ad_status(ad_id, 'Одобрен')
            await callback_query.message.delete()
            await callback_query.answer('✅ Вы приняли заявку на публикацию')


            ad = addb.get_ad(ad_id)
            user_id = ad[1]
            await bot.send_message(user_id, "✅ Ваше объявление одобрено и опубликовано!")
            await bot.send_message(CHANNEL_ID, text=ad[2])
        else:
            await callback_query.message.delete()
            await callback_query.message.answer('Ошибка:\n\nЗаявка уже была одобрена или отклонена.')
    else:
        if ad[4] == 'Ожидание':
            ad_id = int(callback_query.data.split('_')[1])
            addb.update_ad_status(ad_id, 'Одобрен')
            await callback_query.message.delete()
            await callback_query.answer('✅ Вы приняли заявку на публикацию')


            ad = addb.get_ad(ad_id)
            user_id = ad[1]
            await bot.send_message(user_id, "✅ Ваше объявление одобрено и опубликовано!")
            

            await bot.send_photo(CHANNEL_ID, photo=ad[3], caption=ad[2])
        else:
            await callback_query.message.delete()
            await callback_query.message.answer('Ошибка:\n\nЗаявка уже была одобрена или отклонена.')

@dp.callback_query_handler(text_startswith="reject_", state="*")
async def reject_ad(callback_query: types.CallbackQuery):
    ad_id = int(callback_query.data.split('_')[1])
    ad = addb.get_ad(ad_id)
    if ad[4] == 'Ожидание':
        addb.update_ad_status(ad_id, 'Отклонен')

        await callback_query.message.delete()
        ad = addb.get_ad(ad_id)
        user_id = ad[1]
        await bot.send_message(user_id, "❌ Ваше объявление отклонено модератором.")
        
        await callback_query.answer('❌ Вы отклонили заявку на публикацию')
    else:
        await callback_query.message.delete()
        await callback_query.message.answer('Ошибка\n\nЗаявка уже была одобрена или отклонена.')

if __name__ == '__main__':
    if not os.path.exists('avatars'):
        os.makedirs('avatars')
    if not os.path.exists('database'):
        os.makedirs('database')
    logging.basicConfig(level=logging.INFO)
    executor.start_polling(dp, skip_updates=True)
