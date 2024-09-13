from aiogram.dispatcher.filters.state import State, StatesGroup

class CreateAd(StatesGroup):
    waiting_for_text = State()
    waiting_for_confirmation = State()
    waiting_for_photo = State()
    waiting_for_publish = State()

class Rassilka(StatesGroup):
    text = State()

class Addmoder(StatesGroup):
    idmoder = State()

class Delmoder(StatesGroup):
    idmoder = State()