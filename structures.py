from aiogram.dispatcher.filters.state import State, StatesGroup


class AddContent(StatesGroup):
    name = State()
    link = State()


class EditText(StatesGroup):
    index = State()
    text = State()


class EditLink(StatesGroup):
    index = State()
    text = State()


class EditTime(StatesGroup):
    index = State()
    text = State()
